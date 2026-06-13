from __future__ import annotations

from typing import Any, Callable

from .judge_client import run_llm_judge
from .judge_prompts import AGENT_JUDGE_PROMPT, ROUTER_JUDGE_PROMPT


def _judge(
    *,
    judge_name: str,
    criterion_name: str,
    system_prompt: str,
    payload: dict[str, Any],
) -> dict:
    return run_llm_judge(
        judge_name=judge_name,
        criterion_name=criterion_name,
        system_prompt=system_prompt,
        input_payload=payload,
    )


def _payload(output: dict[str, Any], prefix: str) -> dict[str, Any]:
    return {
        "task_prompt": output.get("task_prompt"),
        "agent_input": output.get(f"{prefix}_input"),
        "agent_output": output.get(f"{prefix}_output"),
        "agent_thought_log": output.get(f"{prefix}_thought_log"),
        "source_chunks": output.get("source_chunks"),
        "file_metadata": output.get("file_metadata"),
        "extracted_evidence": output.get("extracted_evidence"),
    }


def _make_agent_evaluator(
    *,
    name: str,
    judge_name: str,
    prefix: str,
    criterion: str,
) -> Callable[[dict[str, Any]], dict]:
    def evaluator(output: dict[str, Any]) -> dict:
        return _judge(
            judge_name=judge_name,
            criterion_name=name,
            system_prompt=AGENT_JUDGE_PROMPT,
            payload={**_payload(output, prefix), "criterion": criterion},
        )

    evaluator.__name__ = name
    return evaluator


def router_route_selection_correctness(output: dict[str, Any]) -> dict:
    return _judge(
        judge_name="RouterJudge",
        criterion_name="router_route_selection_correctness",
        system_prompt=ROUTER_JUDGE_PROMPT,
        payload={
            "task_prompt": output.get("task_prompt"),
            "router_input": output.get("router_input"),
            "router_output": output.get("router_output"),
            "router_thought_log": output.get("router_thought_log"),
            "criterion": "Router selected QA or ORGANIZE correctly from the user task.",
        },
    )


def router_output_schema_validity(output: dict[str, Any]) -> dict:
    return _judge(
        judge_name="RouterJudge",
        criterion_name="router_output_schema_validity",
        system_prompt=ROUTER_JUDGE_PROMPT,
        payload={
            "task_prompt": output.get("task_prompt"),
            "router_output": output.get("router_output"),
            "criterion": "Router output contains a valid task_type of QA or ORGANIZE and a reasoning string.",
        },
    )


def router_decision_explanation_consistency(output: dict[str, Any]) -> dict:
    return _judge(
        judge_name="RouterJudge",
        criterion_name="router_decision_explanation_consistency",
        system_prompt=ROUTER_JUDGE_PROMPT,
        payload={
            "task_prompt": output.get("task_prompt"),
            "router_output": output.get("router_output"),
            "router_thought_log": output.get("router_thought_log"),
            "criterion": "Router reasoning is consistent with the selected route.",
        },
    )


file_locator_query_alignment = _make_agent_evaluator(
    name="file_locator_query_alignment",
    judge_name="FileLocatorJudge",
    prefix="file_locator_agent",
    criterion="FileLocator analysis is aligned with the user query and available document content.",
)
file_locator_selection_relevance = _make_agent_evaluator(
    name="file_locator_selection_relevance",
    judge_name="FileLocatorJudge",
    prefix="file_locator_agent",
    criterion="FileLocator selected files that are relevant to the task or requested more pages when evidence was insufficient.",
)
planner_extraction_plan_relevance = _make_agent_evaluator(
    name="planner_extraction_plan_relevance",
    judge_name="PlannerJudge",
    prefix="planner_agent",
    criterion="Planner produced extraction guidelines and keywords that directly target the user task.",
)
extractor_evidence_groundedness = _make_agent_evaluator(
    name="extractor_evidence_groundedness",
    judge_name="ExtractorJudge",
    prefix="extractor_agent",
    criterion="Extractor output is directly supported by the source chunk it processed.",
)
extractor_no_fabrication = _make_agent_evaluator(
    name="extractor_no_fabrication",
    judge_name="ExtractorJudge",
    prefix="extractor_agent",
    criterion="Extractor did not invent data when the supplied chunk lacked relevant evidence.",
)
keyword_extractor_classification_signal = _make_agent_evaluator(
    name="keyword_extractor_classification_signal",
    judge_name="KeywordExtractorJudge",
    prefix="keyword_extractor_agent",
    criterion="KeywordExtractor selected keywords that are useful for classifying the document.",
)
file_organizer_folder_mapping_validity = _make_agent_evaluator(
    name="file_organizer_folder_mapping_validity",
    judge_name="FileOrganizerJudge",
    prefix="file_organizer_agent",
    criterion="FileOrganizer mapped each file to a plausible valid folder based on extracted keywords and task instructions.",
)
synthesizer_answer_supported_by_evidence = _make_agent_evaluator(
    name="synthesizer_answer_supported_by_evidence",
    judge_name="SynthesizerJudge",
    prefix="synthesizer_agent",
    criterion="Synthesizer final answer is supported by extracted evidence and source chunks.",
)
synthesizer_answer_format_validity = _make_agent_evaluator(
    name="synthesizer_answer_format_validity",
    judge_name="SynthesizerJudge",
    prefix="synthesizer_agent",
    criterion="Synthesizer answer follows the format requested by the task prompt.",
)
reviewer_decision_consistency = _make_agent_evaluator(
    name="reviewer_decision_consistency",
    judge_name="ReviewerJudge",
    prefix="reviewer_agent",
    criterion="Reviewer acceptance or rejection is consistent with the draft output and thought log.",
)


AGENT_EVALUATORS = [
    router_route_selection_correctness,
    router_output_schema_validity,
    router_decision_explanation_consistency,
    file_locator_query_alignment,
    file_locator_selection_relevance,
    planner_extraction_plan_relevance,
    extractor_evidence_groundedness,
    extractor_no_fabrication,
    keyword_extractor_classification_signal,
    file_organizer_folder_mapping_validity,
    synthesizer_answer_supported_by_evidence,
    synthesizer_answer_format_validity,
    reviewer_decision_consistency,
]

