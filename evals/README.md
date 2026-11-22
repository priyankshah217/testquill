# testquill evals

Offline regression suite for generated test case quality. Run it whenever a
prompt, model, or provider changes, to answer: *did this change make the
output better or worse?*

## Layout

```
evals/
└── cases/
    └── <NN-slug>/
        ├── prd.md          Input given to testquill. The ONLY file testquill sees.
        ├── NOTES.md        Designer notes: intentional gaps, contradictions, traps.
        │                   Read by the human answer-key author and the judge.
        │                   NEVER passed to testquill.
        └── expected.csv    Human-written answer key (reference test cases).
```

## The cases

| # | Case | Shape | What it stresses |
|---|---|---|---|
| 01 | `01-mark-as-sold` | One-paragraph prompt (pass via `-p`) | No over-generation from thin input |
| 02 | `02-make-offer` | Medium, well-structured PRD | Baseline coverage |
| 03 | `03-listing-validation` | Dense rules table | Boundary values, many-rule coverage |
| 04 | `04-promoted-listings` | Gaps and ambiguity | Faithfulness: must not invent answers |
| 05 | `05-guest-checkout` | Internal contradiction | Surfaces the conflict instead of silently picking a side |
| 06 | `06-search-filters` | Interdependent controls | Tests every direction of each dependency |

## Writing an answer key (`expected.csv`)

1. Read `NOTES.md` **first**, so you don't fill a deliberate gap with your
   own assumption. Wherever the PRD is silent, your key stays silent too.
2. Write test cases in the same schema testquill emits, plus one column:

   | Column | Notes |
   |---|---|
   | `ID` | `TC-001`, `TC-002`, ... |
   | `Title` | Short imperative summary |
   | `Preconditions` | `None` if not applicable |
   | `Steps` | Numbered, one per line |
   | `Expected Result` | One deterministic outcome |
   | `Priority` | `P0`–`P3` |
   | `Type` | Functional, Negative, Edge, UI, Integration, Performance, Security, Accessibility |
   | `Requirement` | The PRD section/rule this tests, e.g. `§3.2 Offer expiry` |

3. Aim for what a strong QA engineer would ship. It doesn't need to be
   exhaustive: the judge credits "valid extra" cases testquill adds that you
   didn't think of.

## Running

Prerequisites: `.venv` with `pip install -e ".[dev]"`, Node (for `npx`), and
`GEMINI_API_KEY` in the environment or `.env`.

```bash
# 1. Once per answer-key change: freeze each case's grading key, then REVIEW
#    every evals/cases/*/checks.json by hand (it is derived from your key).
.venv/bin/python evals/judge.py prepare

# 2. Run: 6 cases x 3 repeats, full testquill pipeline, graded by the judge.
evals/run.sh                       # REPEAT=1 for a quick smoke run

# 3. First good run becomes the baseline (commit evals/baseline.json).
.venv/bin/python evals/report.py --update-baseline

# 4. Calibrate the judge once: grade the sheet by hand, then score agreement.
.venv/bin/python evals/calibrate.py export
.venv/bin/python evals/calibrate.py score
```

`npx promptfoo@0.125.1 view` opens the promptfoo UI for side-by-side results.
To compare a prompt change, add a second provider in `promptfooconfig.yaml`.

| File | Role |
|---|---|
| `provider.py` | promptfoo provider; runs testquill's real pipeline (`generate_test_cases` → `review_and_fix`) |
| `judge.py` | `prepare` (freeze `checks.json`) and `grade`; deterministic metric maths |
| `promptfoo_assert.py` | Calls the judge; writes each grade to `results/runs/<run>/` |
| `report.py` | Per-case mean/min, overall, regression check vs `baseline.json` (exit 1) |
| `calibrate.py` | Human-vs-judge agreement sheet |
| `regrade.py` | Re-grade an existing run after a rubric change, without regenerating (`--run <id>` → `runs/<id>-regrade/`) |

## How grading works

Framework: **promptfoo** (dev/CI only, not a runtime dependency). The judge
lives in a plain Python module (`evals/judge.py`) so the framework is swappable.
Judge: any testquill provider via `EVAL_JUDGE_PROVIDER` / `EVAL_JUDGE_MODEL`
(default `gemini` / `gemini-4-neon`: the most consistent of the four `gemini-4-*`
models in a comparison on case 02, and right on every disputed verdict). The generator
is testquill's own default (`gemini-2.5-pro`); the assertion refuses to grade if
judge and generator are the same model. The judge's JSON is validated against a
schema in code and retried once if invalid. Same-family judging (Gemini grading
Gemini) makes calibration mandatory.

- **Recall (primary)**: the judge decomposes each reference case into atomic
  checks, then marks each check Covered / Missed by the generated suite.
  Recall = checks covered ÷ total checks.
- **Checklist coverage (secondary)**: the same scoring against the
  "hot spots" / dependency-matrix lists in `NOTES.md`, reported separately so
  gaps in the human key stay visible.
- **Recall rule**: a check counts as covered when one generated case, or several
  together, verify it.
- **Precision**: every generated case gets one label, in this precedence:
  Unsupported (hallucinated, asserts a trap, or silently resolves a
  contradiction) > Generic NFR (accessibility, performance etc. the PRD doesn't
  ask for) > Redundant (repeats an earlier generated case) > Covers check
  (matches the human answer key; checklist-only matches don't count) > Valid
  extra (PRD-supported, not in the key).
- **Priority**: scored only as P0 vs not-P0. **Type is not scored** (the human
  key uses its own taxonomy).
- **Calibration**: a human grades a 40-case sample with the same rubric; the
  judge is trusted at ≥85% agreement. Current judge: 98% (39/40) on run
  `20261123-011908-regrade`, after two rubric fixes found during calibration.

The judge is deliberately separate from `judge_and_fix()` in `generator.py`,
which edits output and therefore can't also grade it.
