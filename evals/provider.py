"""promptfoo provider: runs testquill's real pipeline on one eval case.

Pipeline = the same path a user gets from the CLI (minus the interactive
interview): build_context -> generate_test_cases -> review_and_fix.

Test vars:
  case        directory name under evals/cases/
  input_mode  "file" (default, passed like `-f prd.md`) or "prompt" (like `-p`)

Provider config (promptfooconfig.yaml -> providers[].config), all optional:
  provider, model       forwarded to testquill.providers.get_provider
  system_prompt_file    repo-relative path; replaces the default system prompt
  append_system         true to append instead of replace
"""

from __future__ import annotations

import json
from pathlib import Path

from dotenv import load_dotenv

from testquill.generator import generate_test_cases, review_and_fix
from testquill.loaders import build_context
from testquill.providers import get_provider

EVALS_DIR = Path(__file__).resolve().parent
REPO_DIR = EVALS_DIR.parent
load_dotenv(REPO_DIR / ".env")


def run_case(case: str, input_mode: str = "file", config: dict | None = None) -> dict:
    config = config or {}
    prd_path = EVALS_DIR / "cases" / case / "prd.md"
    if input_mode == "prompt":
        context, errors = build_context(
            prd_path.read_text(encoding="utf-8").strip(), []
        )
    else:
        context, errors = build_context(None, [str(prd_path)])
    if errors:
        raise RuntimeError(f"failed to load {prd_path}: {errors}")

    system_prompt = None
    if config.get("system_prompt_file"):
        system_prompt = (REPO_DIR / config["system_prompt_file"]).read_text(
            encoding="utf-8"
        )

    llm = get_provider(config.get("provider"), model=config.get("model"))
    rows, suggested = generate_test_cases(
        context,
        provider=llm,
        system_prompt=system_prompt,
        append_system=bool(config.get("append_system")),
        fmt="steps",
    )
    review = review_and_fix(rows, suggested, provider=llm)
    return {
        "case": case,
        "generator": {"provider": llm.name, "model": llm.model},
        "pipeline": {
            "initial_warnings": review.initial_report.count,
            "final_warnings": review.final_report.count,
            "judge_and_fix_ran": review.judge_ran,
            "judge_and_fix_error": review.judge_error,
        },
        "test_cases": review.rows,
    }


def call_api(prompt: str, options: dict, context: dict) -> dict:
    vars_ = context.get("vars", {})
    try:
        result = run_case(
            vars_["case"],
            vars_.get("input_mode", "file"),
            (options or {}).get("config") or {},
        )
    except Exception as e:
        return {"error": f"{type(e).__name__}: {e}"}
    return {"output": json.dumps(result)}
