from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

from core.config import LANGUAGE, QUESTS_TEMPERATURE, QUESTS_TOKENS, ROOT_DIRECTORY
from core.prompts import get_prompt
from core.utils import clean_filename, extract_json, load_hero, load_npcs, load_world, save_raw
from llm import openai_client


def _npc_full_name(npc: dict[str, Any]) -> str:
    name = npc.get("name") or npc.get("imię") or "UNKNOWN"
    surname = npc.get("surname") or npc.get("nazwisko") or "UNKNOWN"
    return f"{name} {surname}"


def save_missions(missions: list[dict[str, Any]], out_dir: Path) -> list[Path]:
    """
    Save missions to: <out_dir>/missions/mission_<id>_<title>.json
    Returns list of saved paths.
    """
    missions_dir = out_dir / "missions"
    missions_dir.mkdir(parents=True, exist_ok=True)

    saved: list[Path] = []
    for mission in missions:
        mid = str(mission.get("id", "X"))
        title = clean_filename(str(mission.get("title", f"mission_{mid}")))
        path = missions_dir / f"mission_{mid}_{title}.json"
        path.write_text(json.dumps(mission, indent=4, ensure_ascii=False), encoding="utf-8")
        print(f"Saved {path}")
        saved.append(path)

    return saved


def run(out_dir: Optional[str | Path] = None, lang: Optional[str] = None) -> Optional[list[Path]]:
    """
    Pipeline entrypoint. Loads world + NPCs + hero, generates missions, saves to disk.

    Returns list of saved mission paths or None if generation/parsing failed.
    """
    language = lang or LANGUAGE or "EN"
    out_path = Path(out_dir) if out_dir is not None else Path(ROOT_DIRECTORY)
    out_path.mkdir(parents=True, exist_ok=True)
    world_json = load_world(out_dir=out_path)
    npc_list = load_npcs(out_dir=out_path)
    player_json = load_hero(out_dir=out_path)

    if not world_json:
        print("World not found. Generate world first.")
        return None
    if not npc_list:
        print("NPCs not found. Generate NPCs first.")
        return None
    if not player_json:
        print("Hero not found. Generate hero first.")
        return None

    system_prompt, user_prompt = get_prompt("missions", lang=language)
    npc_names = [_npc_full_name(npc) for npc in npc_list]

    prompt = (
        f"{user_prompt}\n\n"
        f"Game world:\n{json.dumps(world_json, ensure_ascii=False)}\n\n"
        f"NPCs:\n{json.dumps(npc_names, ensure_ascii=False)}\n\n"
        f"Hero:\n{json.dumps(player_json, ensure_ascii=False)}\n\n"
        f"Return only valid JSON, no text or markdown."
    )

    print("Generating storyline...")

    raw = openai_client.ask_model(
        system_prompt=system_prompt,
        prompt=prompt,
        temperature=QUESTS_TEMPERATURE,
        max_tokens=QUESTS_TOKENS,
        label=f"quests-generator-{language.lower()}",
    )

    save_raw(raw, out_path, "raw", "missions_raw.txt")

    parsed = extract_json(raw)
    if not parsed:
        print("JSON parsing error. Raw output (first 1000 chars):\n", raw[:1000])
        return None

    missions = parsed.get("missions")
    if not isinstance(missions, list):
        print("Parsed JSON does not contain 'missions' list. Raw (first 1000 chars):\n", raw[:1000])
        return None

    saved_paths = save_missions(missions, out_path)
    if missions:
        print(json.dumps(missions, indent=4, ensure_ascii=False))

    return saved_paths


def main() -> None:
    run()


if __name__ == "__main__":
    main()