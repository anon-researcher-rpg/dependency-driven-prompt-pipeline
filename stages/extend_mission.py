from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

from core.config import EPIC_TEMPERATURE, EPIC_NPC_TOKENS, LANGUAGE, ROOT_DIRECTORY
from core.prompts import get_prompt
from core.utils import (
    clean_filename,
    extract_json,
    load_hero,
    load_missions,
    load_npcs,
    load_world,
    save_raw,
)
from llm import openai_client


def _npc_full_name(npc: dict[str, Any]) -> str:
    name = npc.get("name") or npc.get("imię") or "UNKNOWN"
    surname = npc.get("surname") or npc.get("nazwisko") or "UNKNOWN"
    return f"{name} {surname}"


def normalize_missions(obj: Any) -> list[dict[str, Any]]:
    """
    Accepts:
    - {"missions": [...]}
    - a single mission dict {"id":..., "title":...}
    - a list of missions
    Returns a normalized list[dict].
    """
    if obj is None:
        return []

    if isinstance(obj, dict):
        missions = obj.get("missions")
        if isinstance(missions, list):
            return [m for m in missions if isinstance(m, dict)]
        if "id" in obj and "title" in obj:
            return [obj]
        return []

    if isinstance(obj, list):
        return [m for m in obj if isinstance(m, dict)]

    print("Unknown missions format:", type(obj))
    return []


def expand_mission(
        world_json: dict[str, Any],
        npc_list: list[dict[str, Any]],
        player_json: dict[str, Any],
        mission: dict[str, Any],
        language: str,
        out_dir: Path,
) -> Optional[list[dict[str, Any]]]:
    system_prompt, user_prompt = get_prompt("mission_epic", lang=language)
    npc_names = [_npc_full_name(npc) for npc in npc_list]

    prompt = (
        f"{user_prompt}\n\n"
        f"Game world:\n{json.dumps(world_json, ensure_ascii=False)}\n\n"
        f"NPCs:\n{json.dumps(npc_names, ensure_ascii=False)}\n\n"
        f"Player character:\n{json.dumps(player_json, ensure_ascii=False)}\n\n"
        f"Mission to expand:\n{json.dumps(mission, ensure_ascii=False)}\n\n"
        f"Return only valid JSON, no text or markdown."
    )

    print("Sending request to OpenAI...")

    raw = openai_client.ask_model(
        system_prompt=system_prompt,
        prompt=prompt,
        temperature=EPIC_TEMPERATURE,
        max_tokens=EPIC_NPC_TOKENS,
        label=f"mission-expander-{language.lower()}",
    )

    mid = str(mission.get("id", "X"))
    save_raw(raw, out_dir, "raw", f"mission_epic_{mid}.txt")

    parsed = extract_json(raw)
    missions = normalize_missions(parsed)

    if not missions:
        print("Error while parsing/normalizing expanded missions. Raw (first 1000 chars):\n", raw[:1000])
        return None

    return missions


def save_mission(mission: dict[str, Any], out_dir: Path) -> Path:
    """
    Save expanded mission to: <out_dir>/missions_epic/mission_<id>_<title>.json
    """
    missions_dir = out_dir / "missions_epic"
    missions_dir.mkdir(parents=True, exist_ok=True)

    mid = str(mission.get("id", "X"))
    title = clean_filename(str(mission.get("title", "untitled")))
    path = missions_dir / f"mission_{mid}_{title}.json"

    path.write_text(json.dumps(mission, indent=4, ensure_ascii=False), encoding="utf-8")
    print(f"Saved {path}")
    return path


def run(out_dir: Optional[str | Path] = None, lang: Optional[str] = None) -> Optional[list[Path]]:
    """
    Pipeline entrypoint. Expands all missions and saves them to disk.
    Returns list of saved expanded mission paths or None if nothing was expanded.
    """
    print("Generating extended campaign...")

    language = lang or LANGUAGE or "EN"
    out_path = Path(out_dir) if out_dir is not None else Path(ROOT_DIRECTORY)
    out_path.mkdir(parents=True, exist_ok=True)

    world_json = load_world(out_dir=out_path)
    npc_list = load_npcs(out_dir=out_path)
    player_json = load_hero(out_dir=out_path)
    mission_list = load_missions(out_dir=out_path)

    if not world_json:
        print("World not found. Generate world first.")
        return None
    if not mission_list:
        print("No missions found. Generate missions first.")
        return None

    def _mission_sort_key(m: dict[str, Any]) -> int:
        mid = m.get("id", 0)
        try:
            return int(mid)
        except Exception:
            return 0

    mission_list.sort(key=_mission_sort_key)

    saved: list[Path] = []
    for mission in mission_list:
        print(f"Extending mission: {mission.get('title', mission.get('id', 'X'))}")
        expanded = expand_mission(world_json, npc_list, player_json, mission, language, out_path)
        if not expanded:
            continue
        for m in expanded:
            saved.append(save_mission(m, out_path))

    if saved:
        print("All missions extended successfully.")
        return saved

    print("No missions were expanded.")
    return None


def main() -> None:
    run()


if __name__ == "__main__":
    main()
