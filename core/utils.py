from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Optional

from core.config import ROOT_DIRECTORY

_JSON_BLOCK_RE = re.compile(r"\{.*\}|\[.*\]", re.DOTALL)
_CODE_FENCE_RE = re.compile(r"```(?:json)?|```", re.IGNORECASE)
_CTRL_CHARS_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")


def _base_dir(out_dir: str | Path | None = None) -> Path:
    return Path(out_dir) if out_dir is not None else Path(ROOT_DIRECTORY)


def _latest_json_file(folder: Path, ignore_names: set[str] | None = None) -> Optional[Path]:
    if not folder.exists():
        return None

    ignore_names = ignore_names or set()
    candidates = [
        p for p in folder.glob("*.json")
        if p.is_file() and p.name not in ignore_names
    ]
    if not candidates:
        return None

    # Najbardziej sensowne przy UUID w nazwie: wybierz po czasie modyfikacji
    return max(candidates, key=lambda p: p.stat().st_mtime)


def load_world(out_dir: str | Path | None = None) -> Optional[dict[str, Any]]:
    folder = _base_dir(out_dir) / "world"
    latest = _latest_json_file(folder)
    if not latest:
        print("Directory /world is empty or missing!")
        return None
    return json.loads(latest.read_text(encoding="utf-8"))


def load_npcs(out_dir: str | Path | None = None) -> list[dict[str, Any]]:
    folder = _base_dir(out_dir) / "npcs"
    if not folder.exists():
        print("Directory /npcs is missing!")
        return []

    npc_list: list[dict[str, Any]] = []
    for p in folder.glob("*.json"):
        if p.name == "relations.json":
            continue
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                npc_list.append(data)
        except Exception:
            # minimalnie: pomijamy uszkodzone pliki
            continue

    return npc_list


def load_hero(out_dir: str | Path | None = None) -> Optional[dict[str, Any]]:
    folder = _base_dir(out_dir) / "player"
    latest = _latest_json_file(folder)
    if not latest:
        print("Directory /player is empty or missing!")
        return None
    return json.loads(latest.read_text(encoding="utf-8"))


def load_missions(out_dir: str | Path | None = None) -> list[dict[str, Any]]:
    folder = _base_dir(out_dir) / "missions"
    if not folder.exists():
        print("Directory /missions is missing!")
        return []

    missions: list[dict[str, Any]] = []
    for p in folder.glob("*.json"):
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                missions.append(data)
        except Exception:
            continue

    return missions


def save_raw(text: str, out_dir: str | Path, subdir: str, filename: str) -> Path:
    base = Path(out_dir)
    d = base / subdir
    d.mkdir(parents=True, exist_ok=True)
    p = d / filename
    p.write_text(text, encoding="utf-8")
    return p


def extract_json(text: str) -> Optional[Any]:
    """
    Extract JSON (dict or list) from a string.

    - strips ```json fences
    - removes control chars
    - tries full json.loads
    - falls back to first {...} or [...] block
    """
    if not text:
        return None

    cleaned = text.strip()
    cleaned = _CODE_FENCE_RE.sub("", cleaned).strip()
    cleaned = _CTRL_CHARS_RE.sub("", cleaned)

    try:
        return json.loads(cleaned)
    except Exception:
        m = _JSON_BLOCK_RE.search(cleaned)
        if not m:
            return None
        try:
            return json.loads(m.group(0))
        except Exception:
            return None


def clean_filename(text: str) -> str:
    text = re.sub(r"[^\w\s-]", "", text, flags=re.UNICODE)
    return text.strip().replace(" ", "_")