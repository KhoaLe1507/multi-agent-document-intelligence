from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from core.config.settings import settings
from core.parsers.file_router import parse_file
from core.pipeline import SystemPipeline
from dataProvider import ProviderService
from dataProvider.models.task import Resource, Task

from .phoenix_config import phoenix_span


def run_agent_task(sample: dict[str, Any]) -> dict[str, Any]:
    task = _sample_to_task(sample)
    provider = ProviderService(
        dump_path=settings.DATA_DUMP_PATH,
        data_dir=settings.DATA_DIR,
        submissions_path=settings.LOCAL_SUBMISSIONS_PATH,
        skip_missing_tasks=settings.LOCAL_SKIP_MISSING_TASKS,
    )
    provider.create_session()

    pipeline = SystemPipeline(provider)
    output = _empty_output(task)

    try:
        with phoenix_span(
            "multi_agent_task",
            {"sample_id": task.task_id, "task_prompt": task.prompt_template},
        ):
            execution = pipeline.process_task(task)
            _emit_agent_spans(execution.get("full_agent_trace") or {})
        output.update(_artifact_from_execution(execution, task))
        output["error"] = execution.get("error")
    except Exception as exc:
        output["error"] = str(exc)
        trace = getattr(__import__("core.utils.trace_logger", fromlist=["tracer"]), "tracer")
        output["full_agent_trace"] = trace.last_completed_task or trace.get_current_trace()

    output.update(_source_artifacts(task))
    output.update(_latest_submission(task.task_id))
    return output


def _emit_agent_spans(trace: dict[str, Any]) -> None:
    for span in trace.get("spans") or []:
        agent_name = span.get("agent_name") or "unknown"
        output = span.get("response_raw")
        with phoenix_span(
            f"agent.{agent_name}",
            {
                "agent_name": agent_name,
                "agent_input": span.get("user_prompt"),
                "agent_output": output,
                "thought_log": _thought_from_output(output),
            },
        ):
            pass


def _thought_from_output(output: Any) -> str | None:
    if isinstance(output, dict):
        return output.get("thought_log") or output.get("reasoning")
    return None


def _sample_to_task(sample: dict[str, Any]) -> Task:
    metadata = sample.get("metadata") or {}
    resources = [
        Resource(
            file_path=res.get("file_path", ""),
            file_type=res.get("file_type", ""),
            token=res.get("token", ""),
            local_path=res.get("local_path"),
        )
        for res in metadata.get("resources", [])
    ]
    return Task(
        task_id=sample.get("sample_id") or sample.get("task_id") or "unknown-sample",
        prompt_template=sample.get("task_prompt") or sample.get("prompt_template") or "",
        resources=resources,
    )


def _empty_output(task: Task) -> dict[str, Any]:
    return {
        "sample_id": task.task_id,
        "task_prompt": task.prompt_template,
        "router_input": task.prompt_template,
        "router_output": None,
        "router_thought_log": None,
        "file_locator_agent_input": None,
        "file_locator_agent_output": None,
        "file_locator_agent_thought_log": None,
        "planner_agent_input": None,
        "planner_agent_output": None,
        "planner_agent_thought_log": None,
        "extractor_agent_input": None,
        "extractor_agent_output": None,
        "extractor_agent_thought_log": None,
        "keyword_extractor_agent_input": None,
        "keyword_extractor_agent_output": None,
        "keyword_extractor_agent_thought_log": None,
        "file_organizer_agent_input": None,
        "file_organizer_agent_output": None,
        "file_organizer_agent_thought_log": None,
        "synthesizer_agent_input": None,
        "synthesizer_agent_output": None,
        "synthesizer_agent_thought_log": None,
        "reviewer_agent_input": None,
        "reviewer_agent_output": None,
        "reviewer_agent_thought_log": None,
        "final_answer": None,
        "extracted_evidence": [],
        "source_chunks": [],
        "file_metadata": [],
        "full_agent_trace": {},
        "error": None,
    }


def _artifact_from_execution(execution: dict[str, Any], task: Task) -> dict[str, Any]:
    trace = execution.get("full_agent_trace") or {}
    spans = trace.get("spans") or []
    by_agent = _spans_by_agent(spans)
    artifact = {
        "task_type": execution.get("task_type"),
        "full_agent_trace": trace,
        "router_output": execution.get("routing_result"),
        "router_thought_log": (execution.get("routing_result") or {}).get("reasoning"),
    }

    mapping = {
        "FileLocator": "file_locator_agent",
        "Planner": "planner_agent",
        "Extractor": "extractor_agent",
        "KeywordExtractor": "keyword_extractor_agent",
        "FileOrganizer": "file_organizer_agent",
        "Synthesizer": "synthesizer_agent",
        "Reviewer": "reviewer_agent",
    }
    for agent_name, prefix in mapping.items():
        selected = by_agent.get(agent_name, [])
        if not selected:
            continue
        artifact[f"{prefix}_input"] = [span.get("user_prompt") for span in selected]
        raw_outputs = [span.get("response_raw") for span in selected]
        artifact[f"{prefix}_output"] = raw_outputs[-1] if len(raw_outputs) == 1 else raw_outputs
        artifact[f"{prefix}_thought_log"] = _collect_thought_logs(raw_outputs)

    workflow_result = execution.get("workflow_result") or {}
    artifact["final_answer"] = workflow_result.get("final_answer") or workflow_result.get("answers")
    artifact["extracted_evidence"] = workflow_result.get("extracted_evidence") or _extract_evidence_from_spans(
        by_agent.get("Extractor", [])
    )
    return artifact


def _spans_by_agent(spans: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for span in spans:
        grouped.setdefault(span.get("agent_name") or "unknown", []).append(span)
    return grouped


def _collect_thought_logs(outputs: list[Any]) -> list[str] | str | None:
    logs = []
    for output in outputs:
        if isinstance(output, dict):
            value = output.get("thought_log") or output.get("reasoning")
            if value:
                logs.append(str(value))
    if not logs:
        return None
    return logs[0] if len(logs) == 1 else logs


def _extract_evidence_from_spans(spans: list[dict[str, Any]]) -> list[dict[str, Any]]:
    evidence = []
    for span in spans:
        output = span.get("response_raw")
        if isinstance(output, dict) and output.get("found_information"):
            evidence.append(
                {
                    "data": output.get("extracted_data"),
                    "confidence_score": output.get("confidence_score"),
                    "thought_log": output.get("thought_log"),
                }
            )
    return evidence


def _source_artifacts(task: Task) -> dict[str, Any]:
    source_chunks = []
    for resource in task.resources:
        local_path = Path(
            resource.local_path
            or Path(settings.DATA_DIR) / ProviderService.to_local_resource_name(resource.file_path)
        )
        if not local_path.exists():
            continue
        try:
            chunks = parse_file(str(local_path))
        except Exception:
            continue
        for chunk in chunks:
            content = chunk.content
            if chunk.chunk_type == "image":
                content = "[base64 image omitted]"
            elif len(content) > 4000:
                content = content[:4000] + "...[truncated]"
            source_chunks.append(
                {
                    "file_name": chunk.file_name,
                    "page_id": chunk.page_number,
                    "chunk_id": chunk.page_number,
                    "chunk_type": chunk.chunk_type,
                    "text": content,
                }
            )
    return {"source_chunks": source_chunks, "file_metadata": source_chunks}


def _latest_submission(task_id: str) -> dict[str, Any]:
    path = Path(settings.LOCAL_SUBMISSIONS_PATH)
    if not path.exists():
        return {}
    latest = None
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            if record.get("task_id") == task_id:
                latest = record
    if not latest:
        return {}
    return {
        "final_answer": latest.get("answers"),
        "submission_thought_log": latest.get("thought_log"),
        "used_tools": latest.get("used_tools"),
    }
