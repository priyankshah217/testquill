"""promptfoo assertion: grade one provider output with evals/judge.py.

Each grade is also written to evals/results/runs/<EVAL_RUN_ID>/ so report.py and
calibrate.py work from plain files, independent of promptfoo's output format.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path

EVALS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(EVALS_DIR))

from dotenv import load_dotenv  # noqa: E402

import judge  # noqa: E402

load_dotenv(EVALS_DIR.parent / ".env")


def get_assert(output: str, context: dict) -> dict:
    result = json.loads(output)
    case = result["case"]
    target = judge.judge_target()
    if target[1] == result["generator"]["model"]:
        raise ValueError(
            f"Judge model {target[1]} is also the generator; pick another."
        )
    graded = judge.grade(
        EVALS_DIR / "cases" / case,
        result["test_cases"],
        target,
        open_questions=result.get("open_questions", []),
    )
    m = graded["metrics"]

    record = {
        "case": case,
        "provider_label": (context.get("provider") or {}).get("label")
        if isinstance(context.get("provider"), dict)
        else None,
        "generator": result["generator"],
        "pipeline": result["pipeline"],
        "test_cases": result["test_cases"],
        "open_questions": result.get("open_questions", []),
        **graded,
    }
    run_id = os.environ.get("EVAL_RUN_ID", "adhoc")
    out_dir = EVALS_DIR / "results" / "runs" / run_id
    out_dir.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha1(output.encode("utf-8")).hexdigest()[:10]
    (out_dir / f"{case}__{digest}.json").write_text(
        json.dumps(record, indent=2), encoding="utf-8"
    )

    return {
        # No fixed pass threshold yet: regressions are judged by report.py
        # against baseline.json. Trap hits are the one hard failure.
        "pass": not m["trap_hits"],
        "score": m["recall"],
        "reason": (
            f"recall {m['recall']:.0%}, checklist {m['checklist_coverage']:.0%}, "
            f"unsupported {m['unsupported_rate']:.0%}, traps {m['trap_hits'] or 'none'}, "
            f"gaps flagged {m['gaps_flagged'] or 0:.0%}"
        ),
        "namedScores": {
            "recall": m["recall"],
            "checklist_coverage": m["checklist_coverage"],
            "unsupported_rate": m["unsupported_rate"],
            "redundant_rate": m["redundant_rate"],
            "gaps_flagged": m["gaps_flagged"] or 0,
        },
    }
