"""Tests for the deterministic parts of the eval harness and review_and_fix."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

EVALS_DIR = Path(__file__).resolve().parent.parent / "evals"
sys.path.insert(0, str(EVALS_DIR))

import judge  # noqa: E402
import report  # noqa: E402

from testquill.generator import review_and_fix  # noqa: E402

CHECKS = {
    "reference_checks": [
        {"id": "R01", "source_tc": "TC-001", "check": "a", "priority": "P0"},
        {"id": "R02", "source_tc": "TC-001", "check": "b", "priority": "P0"},
        {"id": "R03", "source_tc": "TC-002", "check": "c", "priority": "P1"},
        {"id": "R04", "source_tc": "TC-002", "check": "d", "priority": "P1"},
    ],
    "checklist_items": [{"id": "C01", "item": "x"}, {"id": "C02", "item": "y"}],
    "traps": [{"id": "T01", "trap": "refund"}],
}
GENERATED = [
    {"ID": "TC-001", "Priority": "P0"},
    {"ID": "TC-002", "Priority": "P0"},
    {"ID": "TC-003", "Priority": "P2"},
    {"ID": "TC-004", "Priority": "P2"},
]


def _cov(cid, covered, tcs):
    return {"id": cid, "covered": covered, "covering_tc_ids": tcs}


def _gen(tc, cls, traps=()):
    return {"tc_id": tc, "classification": cls, "trap_ids": list(traps), "reason": ""}


class TestComputeMetrics:
    def _verdicts(self, **overrides):
        v = {
            "reference_checks": [
                _cov("R01", True, ["TC-001"]),
                _cov("R02", True, ["TC-001"]),
                _cov("R03", True, ["TC-002"]),
                _cov("R04", False, []),
            ],
            "checklist_items": [_cov("C01", True, ["TC-002"]), _cov("C02", False, [])],
            "generated_cases": [
                _gen("TC-001", "covers_check"),
                _gen("TC-002", "covers_check"),
                _gen("TC-003", "valid_extra"),
                _gen("TC-004", "unsupported", ["T01"]),
            ],
        }
        v.update(overrides)
        return v

    def test_core_metrics(self):
        m = judge.compute_metrics(CHECKS, GENERATED, self._verdicts())
        assert m["recall"] == 0.75
        assert m["checklist_coverage"] == 0.5
        assert m["unsupported_rate"] == 0.25
        assert m["valid_extra"] == 1
        assert m["trap_hits"] == ["T01"]
        assert m["missed_reference_checks"] == ["R04"]
        assert m["generic_nfr_rate"] == 0.0

    def test_generic_nfr_counted_separately(self):
        v = self._verdicts()
        v["generated_cases"][3] = _gen("TC-004", "generic_nfr")
        m = judge.compute_metrics(CHECKS, GENERATED, v)
        assert m["generic_nfr_rate"] == 0.25
        assert m["unsupported_rate"] == 0.0

    def test_p0_agreement_counts_only_covered_checks(self):
        # R01, R02: ref P0 / gen P0 agree. R03: ref P1 but covered by a P0 case.
        m = judge.compute_metrics(CHECKS, GENERATED, self._verdicts())
        assert m["p0_agreement"] == round(2 / 3, 4)

    def test_covered_without_real_case_is_not_trusted(self):
        v = self._verdicts(
            reference_checks=[
                _cov("R01", True, ["TC-999"]),  # nonexistent case
                _cov("R02", True, []),  # no case at all
                # R03, R04 omitted entirely by the judge
            ]
        )
        m = judge.compute_metrics(CHECKS, GENERATED, v)
        assert m["recall"] == 0.0
        assert m["missed_reference_checks"] == ["R01", "R02", "R03", "R04"]

    def test_gaps_flagged_needs_a_real_question(self):
        qs = [{"id": "Q-01", "kind": "gap", "section": "", "question": "?"}]
        flagged = self._verdicts(
            traps=[{"id": "T01", "flagged": True, "question_ids": ["Q-01"]}]
        )
        m = judge.compute_metrics(CHECKS, GENERATED, flagged, qs)
        assert m["gaps_flagged"] == 1.0
        assert m["traps_flagged"] == ["T01"]
        assert m["n_open_questions"] == 1
        # Judge cites a question the generator never asked: not trusted.
        bogus = self._verdicts(
            traps=[{"id": "T01", "flagged": True, "question_ids": ["Q-09"]}]
        )
        assert (
            judge.compute_metrics(CHECKS, GENERATED, bogus, qs)["gaps_flagged"] == 0.0
        )
        # Old grades without trap verdicts or questions score 0, not crash.
        assert (
            judge.compute_metrics(CHECKS, GENERATED, self._verdicts())["gaps_flagged"]
            == 0.0
        )

    def test_unknown_trap_ids_and_unclassified_cases(self):
        v = self._verdicts(generated_cases=[_gen("TC-001", "unsupported", ["T99"])])
        m = judge.compute_metrics(CHECKS, GENERATED, v)
        assert m["trap_hits"] == []
        assert m["unclassified"] == 3


def _record(case, recall, unsupported=0.0, traps=()):
    return {
        "case": case,
        "generator": {"provider": "anthropic", "model": "m"},
        "pipeline": {"judge_and_fix_error": None},
        "meta": {"judge_model": "j"},
        "metrics": {
            "recall": recall,
            "checklist_coverage": recall,
            "unsupported_rate": unsupported,
            "redundant_rate": 0.0,
            "generic_nfr_rate": 0.0,
            "p0_agreement": None,
            "trap_hits": list(traps),
            "n_generated": 10,
        },
    }


class TestReport:
    def test_summarize_mean_and_min(self):
        s = report.summarize(
            [_record("a", 0.6), _record("a", 0.8), _record("b", 1.0, traps=["T01"])]
        )
        assert s["cases"]["a"]["recall"] == {"mean": 0.7, "min": 0.6, "max": 0.8}
        assert s["cases"]["b"]["trap_hits"] == ["T01"]
        assert s["overall"]["recall"] == 0.85
        assert s["overall"]["p0_agreement"] is None

    def test_regression_detection(self):
        base = report.summarize([_record("a", 0.80, unsupported=0.05)])
        ok = report.summarize([_record("a", 0.76, unsupported=0.09)])
        bad = report.summarize([_record("a", 0.70, unsupported=0.20)])
        assert report.regressions(ok, base) == []
        regs = report.regressions(bad, base)
        assert any(r.startswith("recall") for r in regs)
        assert any(r.startswith("unsupported_rate") for r in regs)


class TestValidate:
    SCHEMA = judge._GRADE_SCHEMA

    def test_accepts_valid(self):
        judge.validate(
            {
                "reference_checks": [_cov("R01", True, ["TC-001"])],
                "checklist_items": [],
                "generated_cases": [_gen("TC-001", "covers_check")],
                "traps": [{"id": "T01", "flagged": True, "question_ids": ["Q-01"]}],
            },
            self.SCHEMA,
        )

    def test_rejects_bad_enum_and_missing_keys(self):
        bad_enum = {
            "reference_checks": [],
            "checklist_items": [],
            "generated_cases": [_gen("TC-001", "great")],
            "traps": [],
        }
        with pytest.raises(judge.JudgeError, match="not in"):
            judge.validate(bad_enum, self.SCHEMA)
        with pytest.raises(judge.JudgeError, match="missing keys"):
            judge.validate({"reference_checks": []}, self.SCHEMA)
        with pytest.raises(judge.JudgeError, match="expected boolean"):
            judge.validate(
                {
                    "reference_checks": [_cov("R01", "yes", [])],
                    "checklist_items": [],
                    "generated_cases": [],
                    "traps": [],
                },
                self.SCHEMA,
            )

    def test_parse_json_strips_fences(self):
        assert judge._parse_json('```json\n{"a": 1}\n```') == {"a": 1}
        with pytest.raises(judge.JudgeError):
            judge._parse_json("not json")


class _Provider:
    name, model = "mock", "mock-1"

    def __init__(self, response):
        self.response = response
        self.calls = 0

    def complete(self, system, user, max_tokens=8192):
        self.calls += 1
        if isinstance(self.response, Exception):
            raise self.response
        return self.response


class TestReviewAndFix:
    CLEAN = [{"ID": "TC-001", "Steps": "1. Open page", "Expected Result": "Page opens"}]
    HEDGY = [
        {"ID": "TC-001", "Steps": "1. Open page", "Expected Result": "Page may open"}
    ]

    def test_clean_rows_skip_judge(self):
        p = _Provider("unused")
        r = review_and_fix(self.CLEAN, "name", p)
        assert p.calls == 0 and not r.judge_ran and r.rows == self.CLEAN

    def test_warnings_are_fixed(self):
        p = _Provider(
            json.dumps({"suggested_filename": "name", "test_cases": self.CLEAN})
        )
        started = []
        r = review_and_fix(self.HEDGY, "name", p, on_judge_start=started.append)
        assert r.judge_ran and r.judge_error is None
        assert r.initial_report.count == 1 and r.final_report.clean
        assert r.rows == self.CLEAN and len(started) == 1

    def test_judge_failure_keeps_original(self):
        r = review_and_fix(self.HEDGY, "name", _Provider(RuntimeError("boom")))
        assert r.rows == self.HEDGY
        assert r.judge_error == "RuntimeError: boom"
        assert r.final_report.count == 1
