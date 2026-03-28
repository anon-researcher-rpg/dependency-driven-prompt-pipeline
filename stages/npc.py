from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

from core.config import (
    LANGUAGE,
    ROOT_DIRECTORY,
    BASIC_NPC_TEMPERATURE,
    BASIC_NPC_TOKENS,
)
from core.prompts import get_prompt
from core.utils import (
    extract_json,
    load_world,
    save_raw, clean_filename,
)
from llm import openai_client

def _npc_display_fields(npc: dict[str, Any]) -> tuple[str, str, str, str]:
    """Handles PL/EN keys gracefully."""
    name = npc.get("name") or npc.get("imię") or "UNKNOWN"
    surname = npc.get("surname") or npc.get("nazwisko") or "UNKNOWN"
    race = npc.get("race") or npc.get("rasa") or "UNKNOWN"
    age = str(npc.get("age") or npc.get("wiek") or "0")
    return str(name), str(surname), str(race), age


def save_individual_npcs(npcs: list[dict[str, Any]], out_dir: Path) -> tuple[list[Path], Path]:
    """
    Saves each NPC to <out_dir>/npcs/<safe_name>.json
    Also writes relations to <out_dir>/npcs/relations.json
    """
    npc_folder = out_dir / "npcs"
    npc_folder.mkdir(parents=True, exist_ok=True)

    saved_files: list[Path] = []
    relations: list[dict[str, str]] = []

    for npc in npcs:
        name, surname, race, age = _npc_display_fields(npc)

        safe_base = f"{name}_{surname}_{race}_{age}"
        try:
            safe_name = clean_filename(safe_base)
        except Exception:
            safe_name = safe_base.replace(" ", "_")

        path = npc_folder / f"{safe_name}.json"
        path.write_text(json.dumps(npc, indent=4, ensure_ascii=False), encoding="utf-8")
        saved_files.append(path)

        for rel in npc.get("relations", []) or []:
            to_name = rel.get("npc_name") or rel.get("imię_npc") or rel.get("name") or "UNKNOWN"
            rel_type = rel.get("relation_type") or rel.get("typ_relacji") or rel.get("type") or "UNKNOWN"
            relations.append(
                {
                    "from": f"{name} {surname}",
                    "to": str(to_name),
                    "type": str(rel_type),
                }
            )

    relations_file = npc_folder / "relations.json"
    relations_file.write_text(json.dumps(relations, indent=4, ensure_ascii=False), encoding="utf-8")

    print(f"Saved {len(saved_files)} NPC files and relations graph: {relations_file}")
    return saved_files, relations_file


def run(out_dir: Optional[str | Path] = None, lang: Optional[str] = None) -> Optional[tuple[list[Path], Path]]:
    """
    Pipeline entrypoint. Loads world, generates NPCs, saves them.

    Returns (saved_npc_files, relations_file) or None if generation/parsing failed.
    """
    out_path = Path(out_dir) if out_dir is not None else Path(ROOT_DIRECTORY)
    out_path.mkdir(parents=True, exist_ok=True)

    language = lang or LANGUAGE or "EN"

    world = load_world(out_dir=out_path)
    if not world:
        print("World not found. Generate world first.")
        return None

    system_prompt, user_prompt = get_prompt("npc", lang=language)
    user_prompt = user_prompt + "\n\nWorld (JSON format):\n" + json.dumps(world, ensure_ascii=False)

    print("Generating NPCs...")

    raw = openai_client.ask_model(
        system_prompt=system_prompt,
        prompt=user_prompt,
        temperature=BASIC_NPC_TEMPERATURE,
        max_tokens=BASIC_NPC_TOKENS,
        label=f"npc-generator-{language.lower()}",
    )

    save_raw(raw, out_path, "raw", "npc_raw.txt")

    parsed = extract_json(raw)
    if not parsed or "npcs" not in parsed:
        print("NPC response parsed without key data. Raw output:\n", raw[:1000])
        return None

    npcs = parsed.get("npcs") or []
    if not isinstance(npcs, list):
        print("NPC response has invalid format: 'npcs' is not a list.")
        return None

    return save_individual_npcs(npcs, out_path)


def main() -> None:
    run()


if __name__ == "__main__":
    main()