from unittest.mock import MagicMock

from evaluation.agent_evaluators import router_output_schema_validity
from evaluation.dataset_loader import load_local_eval_samples
from evaluation.evaluator_schemas import BinaryJudgeResult
from evaluation.run_agent_task import _empty_output
from dataProvider.models.task import Task


def test_local_eval_samples_load():
    samples = load_local_eval_samples(limit=1)

    assert samples
    assert "ground_truth" not in samples[0]
    assert samples[0]["sample_id"]
    assert samples[0]["task_prompt"]


def test_run_agent_task_empty_output_contract():
    output = _empty_output(Task(task_id="sample-1", prompt_template="question", resources=[]))

    required = [
        "router_input",
        "router_output",
        "final_answer",
        "extracted_evidence",
        "source_chunks",
        "file_metadata",
        "full_agent_trace",
        "error",
    ]
    for field in required:
        assert field in output


def test_binary_judge_schema_enforces_binary():
    result = BinaryJudgeResult(score=1, label="FAIL", explanation="ok")

    assert result.score in {0, 1}
    assert result.label == "PASS"


def test_evaluator_returns_binary_schema(monkeypatch):
    fake = MagicMock(
        return_value={
            "score": 1,
            "label": "PASS",
            "explanation": "schema is valid",
            "judge_name": "RouterJudge",
            "criterion_name": "router_output_schema_validity",
        }
    )
    monkeypatch.setattr("evaluation.agent_evaluators.run_llm_judge", fake)

    result = router_output_schema_validity(
        {"router_output": {"task_type": "QA", "reasoning": "question answering"}}
    )

    assert result["score"] in {0, 1}
    assert result["label"] in {"PASS", "FAIL"}
    fake.assert_called_once()

