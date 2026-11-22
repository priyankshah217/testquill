#!/usr/bin/env bash
# Run the eval suite, then print the report against baseline.json.
#   evals/run.sh                 # 3 repeats (default)
#   REPEAT=1 evals/run.sh        # quick smoke run
#   evals/run.sh --update-baseline
set -euo pipefail

REPO="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO"

PYTHON="$REPO/.venv/bin/python"
[[ -x "$PYTHON" ]] || { echo "Missing $PYTHON. Create the venv: python3 -m venv .venv && .venv/bin/pip install -e '.[dev]'"; exit 2; }

export PROMPTFOO_PYTHON="$PYTHON"
export EVAL_RUN_ID="${EVAL_RUN_ID:-$(date +%Y%m%d-%H%M%S)}"
mkdir -p evals/results

for c in evals/cases/*/; do
  [[ -f "$c/checks.json" ]] || { echo "Missing $c/checks.json. Run: $PYTHON evals/judge.py prepare"; exit 2; }
done

# promptfoo is a dev-only tool, pinned. --no-cache so repeats are real samples.
npx -y promptfoo@0.125.1 eval \
  -c evals/promptfooconfig.yaml \
  --repeat "${REPEAT:-3}" \
  --no-cache \
  -j "${CONCURRENCY:-3}" \
  -o "evals/results/promptfoo-$EVAL_RUN_ID.json" || true   # non-zero on trap hits; report decides

"$PYTHON" evals/report.py --run "$EVAL_RUN_ID" "$@"
