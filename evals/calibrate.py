"""Calibrate the LLM judge against human grades.

python evals/calibrate.py export [--run ID] [--n 40] [--seed 0]
    Writes evals/results/calibration/<run>/sheet.csv: a sample of generated
    test cases spread across all cases, WITHOUT the judge's labels. Fill in
    `human_label` with one of: covers_check, valid_extra, redundant, unsupported,
    generic_nfr (use the case's prd.md, NOTES.md and checks.json, same rules as
    the judge). Rows are grouped by case and run; "redundant" only means a
    duplicate of another test in the SAME run.

python evals/calibrate.py score [--run ID]
    Compares sheet.csv with the judge's labels. Trust the judge at >= 85%.
"""

from __future__ import annotations

import argparse
import csv
import json
import random
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from judge import CLASSIFICATIONS  # noqa: E402
from report import RUNS_DIR, latest_run_id, load_run  # noqa: E402

CAL_DIR = Path(__file__).resolve().parent / "results" / "calibration"
TRUST_THRESHOLD = 0.85
SHEET_COLS = [
    "row",
    "case",
    "run",
    "result_file",
    "tc_id",
    "Title",
    "Preconditions",
    "Steps",
    "Expected Result",
    "Priority",
    "human_label",
    "human_note",
]


def export(run_id: str, n: int, seed: int) -> Path:
    rng = random.Random(seed)
    pools: dict[str, list[tuple[str, dict]]] = {}
    for f in sorted((RUNS_DIR / run_id).glob("*.json")):
        rec = json.loads(f.read_text(encoding="utf-8"))
        for tc in rec["test_cases"]:
            pools.setdefault(rec["case"], []).append((f.name, tc))
    for pool in pools.values():
        rng.shuffle(pool)

    sample: list[tuple[str, str, dict]] = []
    while len(sample) < n and any(pools.values()):
        for case in sorted(pools):  # round-robin so every case is represented
            if pools[case] and len(sample) < n:
                fname, tc = pools[case].pop()
                sample.append((case, fname, tc))

    # Group by case, then run, so duplicates across runs aren't mistaken for
    # redundancy within one run.
    sample.sort(key=lambda s: (s[0], s[1], s[2].get("ID", "")))
    run_no = {
        fname: i
        for case in pools
        for i, fname in enumerate(sorted({f for c, f, _ in sample if c == case}), 1)
    }

    out = CAL_DIR / run_id / "sheet.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=SHEET_COLS)
        w.writeheader()
        for i, (case, fname, tc) in enumerate(sample, 1):
            w.writerow(
                {
                    "row": i,
                    "case": case,
                    "run": f"run {run_no[fname]}",
                    "result_file": fname,
                    "tc_id": tc.get("ID", ""),
                    **{
                        k: tc.get(k, "")
                        for k in (
                            "Title",
                            "Preconditions",
                            "Steps",
                            "Expected Result",
                            "Priority",
                        )
                    },
                    "human_label": "",
                    "human_note": "",
                }
            )
    return out


def score(run_id: str) -> int:
    sheet = CAL_DIR / run_id / "sheet.csv"
    judge_labels: dict[tuple[str, str], str] = {}
    for f in sorted((RUNS_DIR / run_id).glob("*.json")):
        rec = json.loads(f.read_text(encoding="utf-8"))
        for g in rec["verdicts"]["generated_cases"]:
            judge_labels[(f.name, g["tc_id"])] = g["classification"]

    with open(sheet, newline="", encoding="utf-8") as fh:
        rows = [r for r in csv.DictReader(fh) if r["human_label"].strip()]
    bad = [r["row"] for r in rows if r["human_label"].strip() not in CLASSIFICATIONS]
    if bad:
        raise SystemExit(f"Rows {bad} have a human_label not in {CLASSIFICATIONS}")
    if not rows:
        raise SystemExit(f"No human labels in {sheet} yet.")

    pairs = [
        (
            r["human_label"].strip(),
            judge_labels.get((r["result_file"], r["tc_id"]), "missing"),
        )
        for r in rows
    ]
    agree = sum(h == j for h, j in pairs)
    rate = agree / len(pairs)
    print(
        f"Agreement: {agree}/{len(pairs)} = {rate:.0%} (trust threshold {TRUST_THRESHOLD:.0%})"
    )
    print("\nConfusion (human -> judge):")
    for (h, j), c in sorted(Counter(pairs).items()):
        if h != j:
            print(f"  {h:13} -> {j:13} x{c}")
    print("\nDisagreements:")
    for r, (h, j) in zip(rows, pairs):
        if h != j:
            print(
                f"  row {r['row']} {r['case']} {r['tc_id']}: human={h} judge={j}  {r['human_note']}"
            )
    return 0 if rate >= TRUST_THRESHOLD else 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["export", "score"])
    ap.add_argument("--run")
    ap.add_argument("--n", type=int, default=40)
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()
    run_id = args.run or latest_run_id()
    load_run(run_id)  # fail early if the run is missing
    if args.cmd == "export":
        print(f"Wrote {export(run_id, args.n, args.seed)}")
        return 0
    return score(run_id)


if __name__ == "__main__":
    sys.exit(main())
