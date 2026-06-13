from __future__ import annotations

from typing import Any, TypedDict

from dataProvider.models.task import Task
from ..schemas.data_types import DocumentChunk


class BaseWorkflowState(TypedDict, total=False):
    task: Task
    local_files: list[dict[str, str]]
    thought_log: list[str]
    submit_response: dict[str, Any]


class QAWorkflowState(BaseWorkflowState, total=False):
    all_chunks: list[DocumentChunk]
    chunks_by_file: dict[str, list[DocumentChunk]]
    file_read_index: dict[str, int]
    active_files: list[str]
    target_file_names: list[str]
    target_chunks: list[DocumentChunk]
    locator_loop_count: int
    max_locator_loops: int
    extraction_plan: Any
    extracted_pieces: list[dict[str, Any]]
    final_result: Any
    final_answers: list[str]
    review: Any
    review_issues: list[str]
    qa_attempt: int
    max_attempts: int


class OrganizeWorkflowState(BaseWorkflowState, total=False):
    enhanced_file_list: list[str]
    organize_result: Any
    review: Any
    review_issues: list[str]
    organize_attempt: int
    max_attempts: int
    organized_dir: str
