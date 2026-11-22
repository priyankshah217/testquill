"""Aggregate one eval run and compare it with evals/baseline.json.

    python evals/report.py                    # latest run
    python evals/report.py --run 20261122-1530
    python evals/report.py --update-baseline  # make this run the baseline

Exit code 1 when a regression is detected (see THRESHOLDS).
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from pathlib import Path

EVALS_DIR = Path(__file__).resolve().parent
RUNS_DIR = EVALS_DIR / "results" / "runs"
BASELINE = EVALS_DIR / "baseline.json"

# Regression = metric moves more than 5 points in the bad direction vs baseline.
THRESHOLDS = {
    "recall": ("higher", 0.05),
    "checklist_coverage": ("higher", 0.05),
    "unsupported_rate": ("lower", 0.05),
}
TRACKED = [
    "recall",
    "checklist_coverage",
    "unsupported_rate",
    "redundant_rate",
    "generic_nfr_rate",
    "p0_agreement",
]


def load_run(run_id: str) -> list[dict]:
    files = sorted((RUNS_DIR / run_id).glob("*.json"))
    if not files:
        raise SystemExit(f"No graded results in {RUNS_DIR / run_id}")
    return [json.loads(f.read_text(encoding="utf-8")) for f in files]


def latest_run_id() -> str:
    runs = (
        sorted(p.name for p in RUNS_DIR.iterdir() if p.is_dir())
        if RUNS_DIR.exists()
        else []
    )
    if not runs:
        raise SystemExit("No runs found. Run evals/run.sh first.")
    return runs[-1]


def summarize(records: list[dict]) -> dict:
    by_case: dict[str, list[dict]] = {}
    for r in records:
        by_case.setdefault(r["case"], []).append(r)

    cases = {}
    for case, recs in sorted(by_case.items()):
        row: dict = {"runs": len(recs)}
        for k in TRACKED:
            vals = [r["metrics"][k] for r in recs if r["metrics"][k] is not None]
            row[k] = {
                "mean": round(statistics.mean(vals), 4) if vals else None,
                "min": round(min(vals), 4) if vals else None,
                "max": round(max(vals), 4) if vals else None,
            }
        row["trap_hits"] = sorted({t for r in recs for t in r["metrics"]["trap_hits"]})
        row["n_generated_mean"] = round(
            statistics.mean(r["metrics"]["n_generated"] for r in recs), 1
        )
        cases[case] = row

    overall = {}
    for k in TRACKED:
        means = [c[k]["mean"] for c in cases.values() if c[k]["mean"] is not None]
        overall[k] = round(statistics.mean(means), 4) if means else None

    generators = sorted(
        {f"{r['generator']['provider']}:{r['generator']['model']}" for r in records}
    )
    judges = sorted({r["meta"]["judge_model"] for r in records})
    return {
        "overall": overall,
        "cases": cases,
        "generators": generators,
        "judges": judges,
        "judge_and_fix_errors": sum(
            bool(r["pipeline"].get("judge_and_fix_error")) for r in records
        ),
    }


def regressions(current: dict, baseline: dict) -> list[str]:
    out = []
    for k, (better, tol) in THRESHOLDS.items():
        cur, base = current["overall"].get(k), baseline["overall"].get(k)
        if cur is None or base is None:
            continue
        delta = cur - base
        if (better == "higher" and delta < -tol) or (better == "lower" and delta > tol):
            out.append(f"{k}: {base:.1%} -> {cur:.1%} ({delta:+.1%})")
    return out


def _pct(v: float | None) -> str:
    return "  -  " if v is None else f"{v:5.0%}"


def print_report(run_id: str, s: dict, baseline: dict | None) -> None:
    print(
        f"\nRun {run_id}  generator={', '.join(s['generators'])}  judge={', '.join(s['judges'])}"
    )
    print(
        f"{'case':24} {'runs':>4} {'recall':>13} {'checklist':>13} {'unsupp':>6} {'redund':>6} {'nfr':>6} {'P0agr':>6}  traps"
    )
    for case, c in s["cases"].items():
        print(
            f"{case:24} {c['runs']:>4} "
            f"{_pct(c['recall']['mean'])} (min{_pct(c['recall']['min'])}) "
            f"{_pct(c['checklist_coverage']['mean'])} (min{_pct(c['checklist_coverage']['min'])}) "
            f"{_pct(c['unsupported_rate']['mean']):>6} {_pct(c['redundant_rate']['mean']):>6} {_pct(c['generic_nfr_rate']['mean']):>6} "
            f"{_pct(c['p0_agreement']['mean']):>6}  {', '.join(c['trap_hits']) or '-'}"
        )
    o = s["overall"]
    print(
        f"{'OVERALL':24}      {_pct(o['recall'])}         {_pct(o['checklist_coverage'])}"
        f"         {_pct(o['unsupported_rate']):>6} {_pct(o['redundant_rate']):>6} {_pct(o['generic_nfr_rate']):>6} {_pct(o['p0_agreement']):>6}"
    )
    if s["judge_and_fix_errors"]:
        print(
            f"WARNING: judge_and_fix failed in {s['judge_and_fix_errors']} generation(s)."
        )
    if baseline:
        print(
            f"\nBaseline: {baseline['run_id']} (generator={', '.join(baseline['generators'])})"
        )
        for k in TRACKED:
            cur, base = o.get(k), baseline["overall"].get(k)
            if cur is not None and base is not None:
                print(f"  {k:20} {base:6.1%} -> {cur:6.1%} ({cur - base:+.1%})")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run")
    ap.add_argument("--update-baseline", action="store_true")
    args = ap.parse_args()

    run_id = args.run or latest_run_id()
    summary = summarize(load_run(run_id))
    baseline = (
        json.loads(BASELINE.read_text(encoding="utf-8")) if BASELINE.exists() else None
    )
    print_report(run_id, summary, baseline)

    if args.update_baseline:
        BASELINE.write_text(
            json.dumps({"run_id": run_id, **summary}, indent=2) + "\n", encoding="utf-8"
        )
        print(f"\nBaseline updated to run {run_id}.")
        return 0
    if not baseline:
        print("\nNo baseline yet. Re-run with --update-baseline to set one.")
        return 0
    regs = regressions(summary, baseline)
    if regs:
        print("\nREGRESSION:\n  " + "\n  ".join(regs))
        return 1
    print("\nNo regression vs baseline.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
