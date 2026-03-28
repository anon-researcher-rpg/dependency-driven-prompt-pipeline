from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Any, Optional

from core.config import (
    CLASSES,
    HERO_TEMPERATURE,
    HERO_TOKENS,
    LANGUAGE,
    ROOT_DIRECTORY,
)
from core.prompts import get_prompt
from core.utils import clean_filename, extract_json, load_npcs, load_world, save_raw
from llm import openai_client


def save_player_card(player_card: dict[str, Any], out_dir: Path) -> Path:
    """
    Save hero JSON to: <out_dir>/player/<name>_<surname>_<class>.json
    """
    player_folder = out_dir / "player"
    player_folder.mkdir(parents=True, exist_ok=True)

    char_name = clean_filename(str(player_card.get("name", player_card.get("imię", "Unknown"))))
    char_surname = clean_filename(str(player_card.get("surname", player_card.get("nazwisko", "Unknown"))))
    char_class = clean_filename(str(player_card.get("class", player_card.get("klasa", "Unknown"))))

    path = player_folder / f"{char_name}_{char_surname}_{char_class}.json"
    path.write_text(json.dumps(player_card, indent=4, ensure_ascii=False), encoding="utf-8")

    print(f"Saved hero: {path}")
    return path


def run(out_dir: Optional[str | Path] = None, lang: Optional[str] = None) -> Optional[Path]:
    """
    Pipeline entrypoint. Loads world + NPCs, generates hero, saves to disk.

    Returns path to saved hero JSON or None if generation/parsing failed.
    """
    language = lang or LANGUAGE or "EN"
    out_path = Path(out_dir) if out_dir is not None else Path(ROOT_DIRECTORY)
    out_path.mkdir(parents=True, exist_ok=True)

    world_json = load_world(out_dir=out_path)
    npc_list = load_npcs(out_dir=out_path)

    if not world_json:
        print("World not found. Generate world first.")
        return None

    print("Generating hero...")

    system_prompt, user_prompt = get_prompt("hero", lang=language)

    char_class = random.choice(CLASSES) if CLASSES else "Unknown"
    k = min(3, len(npc_list))
    npc_sample = random.sample(npc_list, k=k) if npc_list and k > 0 else []

    npc_names = []
    for npc in npc_sample:
        name = npc.get("name") or npc.get("imię") or "UNKNOWN"
        surname = npc.get("surname") or npc.get("nazwisko") or "UNKNOWN"
        npc_names.append(f"{name} {surname}")

    prompt = (
        f"{user_prompt}\n\n"
        f"Game world:\n{json.dumps(world_json, ensure_ascii=False)}\n\n"
        f"Selected NPCs:\n{json.dumps(npc_names, ensure_ascii=False)}\n\n"
        f"Class: {char_class}\n\n"
        f"Return only valid JSON, no text or markdown."
    )

    raw = openai_client.ask_model(
        system_prompt=system_prompt,
        prompt=prompt,
        temperature=HERO_TEMPERATURE,
        max_tokens=HERO_TOKENS,
        label=f"hero-generation-{language.lower()}",
    )

    save_raw(raw, out_path, "raw", "hero_raw.txt")

    parsed = extract_json(raw)
    if not parsed:
        print("JSON parsing error. Raw output (first 1000 chars):\n", raw[:1000])
        return None

    hero_file = save_player_card(parsed, out_path)
    print(json.dumps(parsed, indent=4, ensure_ascii=False))
    return hero_file


def main() -> None:
    run()


if __name__ == "__main__":
    main()