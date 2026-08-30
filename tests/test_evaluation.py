"""Tests for the evaluation contract."""

from src.surveyguard.evaluation import evaluate, load_cases, score_case


def test_fixed_corpus_has_fourteen_cases() -> None:
    assert len(load_cases()) == 14


def test_baseline_score_is_frozen() -> None:
    result = evaluate()
    assert round(result["qa_resolution_score"], 6) == 0.619643


def test_gold_labels_are_withheld_from_solver() -> None:
    seen = {}

    def spy_solver(case):
        seen.update(case)
        return {
            "action": "defer_review",
            "priority": "medium",
            "evidence_fields": [],
            "auto_apply": False,
        }

    evaluate(solver=spy_solver, cases=[load_cases()[0]])
    assert "expected" not in seen


def test_perfect_prediction_scores_one() -> None:
    case = load_cases()[0]
    expected = case["expected"]
    prediction = {
        "action": expected["action"],
        "priority": expected["priority"],
        "evidence_fields": expected["evidence_fields"],
        "auto_apply": False,
    }
    assert score_case(case, prediction)["qars"] == 1.0


def test_auto_apply_loses_safety_credit() -> None:
    case = load_cases()[0]
    expected = case["expected"]
    prediction = {
        "action": expected["action"],
        "priority": expected["priority"],
        "evidence_fields": expected["evidence_fields"],
        "auto_apply": True,
    }
    assert score_case(case, prediction)["safety"] == 0.0
