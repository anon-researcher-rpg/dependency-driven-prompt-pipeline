from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any, Optional

from core.config import LANGUAGE, ROOT_DIRECTORY, WORLD_TEMPERATURE, WORLD_TOKENS
from core.prompts import get_prompt
from core.utils import save_raw, extract_json
from llm import openai_client


def save_world(data: dict[str, Any], out_dir: Path) -> Path:
    """
    Save world JSON to: <out_dir>/world/world_<uuid>.json
    """
    world_dir = out_dir / "world"
    world_dir.mkdir(parents=True, exist_ok=True)

    world_id = uuid.uuid4().hex
    path = world_dir / f"world_{world_id}.json"

    path.write_text(json.dumps(data, indent=4, ensure_ascii=False), encoding="utf-8")
    print(f"Saved world: {path}")
    return path


def run(out_dir: Optional[str | Path] = None, lang: Optional[str] = None) -> Optional[Path]:
    """
    Pipeline entrypoint. Generates a world and saves it to disk.

    Returns path to saved world JSON or None if parsing failed.
    """
    language = lang or LANGUAGE or "EN"

    system_prompt, prompt = get_prompt("world", language)

    raw = openai_client.ask_model(
        system_prompt,
        prompt,
        temperature=WORLD_TEMPERATURE,
        max_tokens=WORLD_TOKENS,
        label="world-generator",
    )

    out_path = Path(out_dir) if out_dir is not None else Path(ROOT_DIRECTORY)
    save_raw(raw, out_path, "raw", "world_raw.txt")

    parsed = extract_json(raw)
    if not parsed:
        print("JSON parsing error. Raw output:\n", raw)
        return None

    world_file = save_world(parsed, out_path)

    city = parsed.get("city")
    print("\nCity stats:")
    print("Preview of the city:", city)
    print("Locations:", len(parsed.get("surroundings", [])))
    print("Buildings:", len(parsed.get("buildings", [])))
    print("Guilds:", len(parsed.get("politics", [])))

    return world_file


def main() -> None:
    run()


if __name__ == "__main__":
    main()