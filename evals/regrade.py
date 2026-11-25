"""Re-grade an existing run with the current judge, without regenerating.

Use after a rubric change: reads evals/results/runs/<run>/*.json, grades each
record's test_cases again, and writes them to runs/<run>-regrade/ (same file
names, so a calibration sheet from <run> can be scored against it).

    .venv/bin/python evals/regrade.py --run <run> [-j 3]
"""

from __future__ import annotations

import argparse
import json
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

EVALS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(EVALS_DIR))

from dotenv import load_dotenv  # noqa: E402

import judge  # noqa: E402

RUNS_DIR = EVALS_DIR / "results" / "runs"


def main() -> int:
    load_dotenv(EVALS_DIR.parent / ".env")
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True)
    ap.add_argument("-j", type=int, default=3)
    args = ap.parse_args()
    src = RUNS_DIR / args.run
    dst = RUNS_DIR / f"{args.run}-regrade"
    dst.mkdir(parents=True, exist_ok=True)
    target = judge.judge_target()

    def one(f: Path) -> str:
        out = dst / f.name
        if out.exists():
            return f"{f.name}: already done"
        rec = json.loads(f.read_text(encoding="utf-8"))
        if target[1] == rec["generator"]["model"]:
            raise ValueError(f"Judge model {target[1]} is also the generator.")
        graded = judge.grade(
            EVALS_DIR / "cases" / rec["case"],
            rec["test_cases"],
            target,
            open_questions=rec.get("open_questions", []),
        )
        rec.update(graded)
        out.write_text(json.dumps(rec, indent=2), encoding="utf-8")
        m = graded["metrics"]
        return f"{f.name}: recall {m['recall']:.0%} traps {m['trap_hits'] or '-'}"

    files = sorted(src.glob("*.json"))
    with ThreadPoolExecutor(max_workers=args.j) as ex:
        for line in ex.map(one, files):
            print(line, flush=True)
    print(f"Wrote {len(files)} grades to {dst}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
