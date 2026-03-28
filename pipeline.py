from __future__ import annotations

import argparse
import json
import logging
import sys
import uuid
from datetime import datetime
from pathlib import Path
from typing import Callable

from core.config import DATA_DIR, LANGUAGE, MODEL, log_config_vars
from stages import world, npc, hero, missions, extend_mission
from visualization import visualization


STAGES: dict[str, Callable[..., object]] = {
    "world": world.run,
    "npc": npc.run,
    "hero": hero.run,
    "missions": missions.run,
    "extend_mission": extend_mission.run,
    "visualization": visualization.run,
}


def make_run_dir(base_dir: Path, model_name: str) -> Path:
    run_id = uuid.uuid4().hex
    run_dir = base_dir / model_name / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    return run_dir


def setup_logging(log_path: Path) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler(log_path, encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )


def write_meta(run_dir: Path, model_name: str, lang: str, steps: list[str]) -> None:
    meta = {
        "run_id": run_dir.name,
        "model": model_name,
        "language": lang,
        "steps": steps,
        "created_at": datetime.utcnow().isoformat() + "Z",
    }
    (run_dir / "meta.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")


def run_pipeline(steps: list[str], out_dir: Path, lang: str) -> None:
    logging.info(f"Run directory: {out_dir}")
    logging.info("Pipeline: " + " → ".join(steps))
    log_config_vars()

    for step in steps:
        fn = STAGES[step]
        logging.info(f"Running stage: {step}")
        try:
            result = fn(out_dir=out_dir, lang=lang)
            if result is None:
                logging.warning(f"Stage '{step}' returned None (stopping pipeline).")
                break
            logging.info(f"Stage '{step}' completed.")
        except Exception as e:
            logging.exception(f"Stage '{step}' crashed: {e}")
            break

def main() -> None:
    parser = argparse.ArgumentParser(description="Pipeline runner (module-based)")

    parser.add_argument(
        "steps",
        nargs="*",
        help="Optional steps to run (default: run all).",
    )

    parser.add_argument("--list", action="store_true", help="List available steps")
    parser.add_argument("--model", default=MODEL, help="Model folder under data/ (default from config/env)")
    parser.add_argument("--out-base", default=str(DATA_DIR), help="Base output directory (default from config/env)")
    parser.add_argument("--lang", default=LANGUAGE, help="Language (default from config/env)")
    parser.add_argument("--run-id", help="Existing run ID (skip creating new UUID)")
    args, unknown = parser.parse_known_args()

    if args.list:
        print("Available steps:")
        for step in STAGES.keys():
            print(f"  - {step}")
        raise SystemExit(0)

    raw_steps = [s for s in (args.steps or []) if s not in ("[]", "[ ]")]

    allowed = set(STAGES.keys())
    invalid = [s for s in raw_steps if s not in allowed]
    if invalid:
        print("Invalid step(s):", ", ".join(invalid))
        print("Allowed steps:", ", ".join(STAGES.keys()))
        raise SystemExit(2)

    steps = raw_steps if raw_steps else list(STAGES.keys())

    if args.run_id:
        out_dir = Path(args.out_base) / args.model / args.run_id
        out_dir.mkdir(parents=True, exist_ok=True)
    else:
        out_dir = make_run_dir(Path(args.out_base), args.model)

    print("OUT_DIR =", out_dir)

    setup_logging(out_dir / "pipeline.log")
    write_meta(out_dir, args.model, args.lang, steps)

    run_pipeline(steps, out_dir, args.lang)


if __name__ == "__main__":
    main()