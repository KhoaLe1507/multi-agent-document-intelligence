from __future__ import annotations

from typing import Any, Callable

from .judge_client import run_llm_judge
from .judge_prompts import E2E_JUDGE_PROMPT


def _payload(output: dict[str, Any], criterion: str) -> dict[str, Any]:
    return {
        "criterion": criterion,
        "task_prompt": output.get("task_prompt"),
        "final_answer": output.get("final_answer"),
        "extracted_evidence": output.get("extracted_evidence"),
        "source_chunks": output.get("source_chunks"),
        "file_metadata": output.get("file_metadata"),
        "full_agent_trace": output.get("full_agent_trace"),
    }


def _make_e2e_evaluator(name: str, criterion: str) -> Callable[[dict[str, Any]], dict]:
    def evaluator(output: dict[str, Any]) -> dict:
        return run_llm_judge(
            judge_name="EndToEndJudge",
            criterion_name=name,
            system_prompt=E2E_JUDGE_PROMPT,
            input_payload=_payload(output, criterion),
        )

    evaluator.__name__ = name
    return evaluator


e2e_final_answer_groundedness = _make_e2e_evaluator(
    "e2e_final_answer_groundedness",
    "Final answer is grounded in the supplied source chunks or extracted evidence.",
)
e2e_final_answer_relevance = _make_e2e_evaluator(
    "e2e_final_answer_relevance",
    "Final answer directly addresses the user query.",
)
e2e_proxy_accuracy = _make_e2e_evaluator(
    "e2e_proxy_accuracy",
    "With no ground truth, final answer is reasonable and accurate based only on all supplied evidence.",
)
e2e_no_hallucination = _make_e2e_evaluator(
    "e2e_no_hallucination",
    "Final answer contains no unsupported claims beyond the supplied evidence.",
)
e2e_citation_or_source_traceability = _make_e2e_evaluator(
    "e2e_citation_or_source_traceability",
    "If the task or answer requires source attribution, the answer can be traced to file/page/chunk evidence.",
)
e2e_completeness = _make_e2e_evaluator(
    "e2e_completeness",
    "Final answer covers the main parts of the user query without omitting important requested information.",
)


E2E_EVALUATORS = [
    e2e_final_answer_groundedness,
    e2e_final_answer_relevance,
    e2e_proxy_accuracy,
    e2e_no_hallucination,
    e2e_citation_or_source_traceability,
    e2e_completeness,
]

