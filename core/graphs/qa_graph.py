from __future__ import annotations

import concurrent.futures
from pathlib import Path
from typing import Literal

from dataProvider import ProviderService

from ..agents import (
    ExtractorAgent,
    FileLocatorAgent,
    PlannerAgent,
    ReviewerAgent,
    SynthesizerAgent,
)
from ..exceptions.agent_errors import ParsingError
from ..parsers.file_router import parse_file
from ..schemas.data_types import DocumentChunk
from ..utils.cache_manager import CacheManager
from ..utils.logger import agent_logger
from .state import QAWorkflowState

try:
    from langgraph.graph import END, START, StateGraph
except ImportError:
    END = START = StateGraph = None


class QAWorkflowGraph:
    """Stateful LangGraph orchestration for the QA workflow."""

    def __init__(self, provider: ProviderService):
        self.provider = provider
        self.locator = FileLocatorAgent()
        self.planner = PlannerAgent()
        self.extractor = ExtractorAgent()
        self.synthesizer = SynthesizerAgent()
        self.reviewer = ReviewerAgent()

        self.download_dir = Path("downloaded_data")
        self.download_dir.mkdir(exist_ok=True)
        self.graph = self._compile_graph()

    def execute(self, task) -> QAWorkflowState:
        initial_state: QAWorkflowState = {
            "task": task,
            "local_files": [],
            "thought_log": [],
            "all_chunks": [],
            "chunks_by_file": {},
            "file_read_index": {},
            "active_files": [],
            "target_file_names": [],
            "extracted_pieces": [],
            "review_issues": [],
            "locator_loop_count": 0,
            "max_locator_loops": 5,
            "qa_attempt": 0,
            "max_attempts": 2,
        }
        if self.graph is None:
            return self._run_fallback(initial_state)
        return self.graph.invoke(initial_state, {"recursion_limit": 40})

    def _compile_graph(self):
        if StateGraph is None:
            agent_logger.warning(
                "LangGraph is not installed. Falling back to imperative QA workflow."
            )
            return None

        builder = StateGraph(QAWorkflowState)
        builder.add_node("download_files", self.download_files)
        builder.add_node("parse_files", self.parse_files)
        builder.add_node("locate_files", self.locate_files)
        builder.add_node("plan_extraction", self.plan_extraction)
        builder.add_node("extract_chunks", self.extract_chunks)
        builder.add_node("synthesize_answer", self.synthesize_answer)
        builder.add_node("review_answer", self.review_answer)
        builder.add_node("submit_qa", self.submit_qa)

        builder.add_edge(START, "download_files")
        builder.add_edge("download_files", "parse_files")
        builder.add_edge("parse_files", "locate_files")
        builder.add_conditional_edges(
            "locate_files",
            self.route_after_locate,
            {
                "more_info": "locate_files",
                "plan": "plan_extraction",
            },
        )
        builder.add_edge("plan_extraction", "extract_chunks")
        builder.add_edge("extract_chunks", "synthesize_answer")
        builder.add_edge("synthesize_answer", "review_answer")
        builder.add_conditional_edges(
            "review_answer",
            self.route_after_review,
            {
                "retry": "synthesize_answer",
                "submit": "submit_qa",
            },
        )
        builder.add_edge("submit_qa", END)
        return builder.compile()

    def download_files(self, state: QAWorkflowState) -> dict:
        task = state["task"]
        local_files: list[dict[str, str]] = []
        for res in task.resources:
            local_path = self.download_dir / res.file_path
            local_path.parent.mkdir(parents=True, exist_ok=True)
            saved_path = self.provider.download_file(res.token, str(local_path))
            local_files.append({"path": saved_path, "name": Path(saved_path).name})
        return {"local_files": local_files}

    def parse_files(self, state: QAWorkflowState) -> dict:
        all_chunks: list[DocumentChunk] = []
        thought_log = list(state.get("thought_log", []))

        for file_info in state["local_files"]:
            file_path = file_info["path"]
            file_name = file_info["name"]
            cached_chunks = CacheManager.get_cached_item(file_name, "chunks")
            if cached_chunks:
                agent_logger.info(f"[Cache HIT] Reusing parsed chunks for {file_name}.")
                all_chunks.extend(cached_chunks)
                thought_log.append(f"[Parse - {file_name}]: Cache hit.")
                continue

            try:
                chunks = parse_file(str(file_path))
                CacheManager.update_cache(file_name, "chunks", chunks)
                all_chunks.extend(chunks)
                thought_log.append(f"[Parse - {file_name}]: Parsed {len(chunks)} chunks.")
            except ParsingError as exc:
                agent_logger.error(f"Skipping failed file {file_path}: {exc}")
                thought_log.append(f"[Parse - {file_name}]: Failed with error {exc}.")

        chunks_by_file: dict[str, list[DocumentChunk]] = {}
        for chunk in all_chunks:
            chunks_by_file.setdefault(chunk.file_name, []).append(chunk)

        return {
            "all_chunks": all_chunks,
            "chunks_by_file": chunks_by_file,
            "file_read_index": {fname: 0 for fname in chunks_by_file},
            "active_files": list(chunks_by_file.keys()),
            "thought_log": thought_log,
        }

    def locate_files(self, state: QAWorkflowState) -> dict:
        task = state["task"]
        chunks_by_file = state.get("chunks_by_file", {})
        file_read_index = dict(state.get("file_read_index", {}))
        active_files = list(state.get("active_files", []))
        target_file_names = list(state.get("target_file_names", []))
        loop_count = state.get("locator_loop_count", 0) + 1

        if not active_files:
            return {
                "target_chunks": list(state.get("all_chunks", [])),
                "locator_loop_count": loop_count,
            }

        user_content_blocks = [
            {
                "type": "text",
                "text": (
                    f"<Task Instruction>\n{task.prompt_template}\n\n"
                    "<Document List and Current Content>\n"
                ),
            }
        ]

        for fname in active_files:
            idx = file_read_index.get(fname, 0)
            chunks = chunks_by_file.get(fname, [])
            if idx < len(chunks):
                chunk = chunks[idx]
                if chunk.chunk_type == "image":
                    user_content_blocks.append(
                        {
                            "type": "text",
                            "text": (
                                f"\n- File: {fname} (Page/Chunk {idx + 1}) "
                                "| Image content attached:"
                            ),
                        }
                    )
                    user_content_blocks.append(
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{chunk.content}",
                                "detail": "auto",
                            },
                        }
                    )
                else:
                    user_content_blocks.append(
                        {
                            "type": "text",
                            "text": (
                                f"\n- File: {fname} (Page/Chunk {idx + 1}) "
                                f"| Text content:\n{chunk.content[:1500]}..."
                            ),
                        }
                    )
            else:
                user_content_blocks.append(
                    {"type": "text", "text": f"\n- File: {fname} | [END OF DOCUMENT CONTENT]"}
                )

        user_content_blocks.append(
            {
                "type": "text",
                "text": (
                    "\nAnalyze the document pages above.\nDetermine which files are "
                    "CONFIRMED RELEVANT, which are CONFIRMED IRRELEVANT, and which "
                    "NEED MORE PAGES to decide."
                ),
            }
        )

        locator_result = self.locator.locate_files_advanced(user_content_blocks)
        for file_name in locator_result.target_file_names:
            if file_name not in target_file_names:
                target_file_names.append(file_name)

        next_active_files: list[str] = []
        if locator_result.requires_more_info:
            for fname in locator_result.files_needing_more_chunks:
                chunks = chunks_by_file.get(fname, [])
                idx = file_read_index.get(fname, 0)
                if idx + 1 < len(chunks):
                    file_read_index[fname] = idx + 1
                    next_active_files.append(fname)

        thought_log = list(state.get("thought_log", []))
        thought_log.append(f"[FileLocator - Round {loop_count}]: {locator_result.reasoning}")

        target_chunks = [c for c in state.get("all_chunks", []) if c.file_name in target_file_names]
        if not target_chunks and (
            not locator_result.requires_more_info
            or not next_active_files
            or loop_count >= state.get("max_locator_loops", 5)
        ):
            target_chunks = list(state.get("all_chunks", []))

        return {
            "file_read_index": file_read_index,
            "active_files": next_active_files,
            "target_file_names": target_file_names,
            "target_chunks": target_chunks,
            "locator_loop_count": loop_count,
            "thought_log": thought_log,
        }

    def route_after_locate(self, state: QAWorkflowState) -> Literal["more_info", "plan"]:
        if (
            state.get("active_files")
            and state.get("locator_loop_count", 0) < state.get("max_locator_loops", 5)
        ):
            return "more_info"
        return "plan"

    def plan_extraction(self, state: QAWorkflowState) -> dict:
        plan = self.planner.create_extraction_plan(state["task"].prompt_template)
        thought_log = list(state.get("thought_log", []))
        thought_log.append(f"[Planner]: {plan.thought_log}")
        return {"extraction_plan": plan, "thought_log": thought_log}

    def extract_chunks(self, state: QAWorkflowState) -> dict:
        target_chunks = list(state.get("target_chunks") or state.get("all_chunks", []))
        plan = state["extraction_plan"]
        extracted_pieces: list[dict] = []
        thought_log = list(state.get("thought_log", []))

        def process_chunk_extraction(item):
            idx, chunk = item
            try:
                result = self.extractor.extract_from_chunk(
                    chunk, plan.extraction_guidelines, plan.target_keywords
                )
                return {"success": True, "idx": idx, "chunk": chunk, "result": result}
            except Exception as exc:
                return {"success": False, "idx": idx, "chunk": chunk, "error": str(exc)}

        agent_logger.info(
            f"Launching {len(target_chunks)} extraction agents through the QA graph."
        )
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            results = executor.map(process_chunk_extraction, list(enumerate(target_chunks)))

        for res in results:
            idx = res["idx"]
            chunk = res["chunk"]
            if res["success"]:
                result = res["result"]
                thought_log.append(
                    f"[Extractor - {chunk.file_name} Page {idx + 1}]: {result.thought_log}"
                )
                if result.found_information and result.extracted_data:
                    extracted_pieces.append(
                        {
                            "data": result.extracted_data,
                            "confidence_score": result.confidence_score,
                            "source": chunk.get_context_description(),
                        }
                    )
            else:
                agent_logger.error(f"Extractor failed on chunk {idx + 1}: {res['error']}")

        return {"extracted_pieces": extracted_pieces, "thought_log": thought_log}

    def synthesize_answer(self, state: QAWorkflowState) -> dict:
        attempt = state.get("qa_attempt", 0) + 1
        review_issues = state.get("review_issues", [])
        if review_issues:
            feedback = "\n\n[REVIEWER FEEDBACK FROM PREVIOUS ROUND]:\n- " + "\n- ".join(
                review_issues
            )
            prompt = state["task"].prompt_template + feedback
        else:
            prompt = state["task"].prompt_template

        final_result = self.synthesizer.synthesize_final_answer(
            prompt, state.get("extracted_pieces", [])
        )
        return {
            "final_result": final_result,
            "final_answers": final_result.final_answers,
            "qa_attempt": attempt,
        }

    def review_answer(self, state: QAWorkflowState) -> dict:
        final_result = state["final_result"]
        review = self.reviewer.review_qa(
            state["task"].prompt_template,
            final_result.final_answers,
            final_result.thought_log,
        )
        thought_log = list(state.get("thought_log", []))
        if review.is_acceptable:
            thought_log.append(
                f"[Synthesizer - Attempt {state.get('qa_attempt', 1)}]: "
                f"{final_result.thought_log}\n[Reviewer Audit]: OK. Answer accepted."
            )
        else:
            thought_log.append(
                f"[Synthesizer - Attempt {state.get('qa_attempt', 1)}]: "
                f"{final_result.thought_log}\n[Reviewer REJECTED]: {review.issues}"
            )
            agent_logger.warning(
                f"Reviewer rejected QA answer: {review.issues}. Retrying if budget remains."
            )

        return {
            "review": review,
            "review_issues": list(state.get("review_issues", [])) + list(review.issues),
            "thought_log": thought_log,
        }

    def route_after_review(self, state: QAWorkflowState) -> Literal["retry", "submit"]:
        review = state.get("review")
        if (
            review is not None
            and not review.is_acceptable
            and state.get("qa_attempt", 0) < state.get("max_attempts", 2)
        ):
            return "retry"
        return "submit"

    def submit_qa(self, state: QAWorkflowState) -> dict:
        final_result = state.get("final_result")
        answers = state.get("final_answers") or (
            final_result.final_answers if final_result is not None else []
        )
        submit_response = self.provider.submit_task(
            task_id=state["task"].task_id,
            answers=answers,
            thought_log="\n".join(state.get("thought_log", [])),
            used_tools=[
                "LangGraph",
                "FileLocator",
                "Planner",
                "Extractor",
                "Synthesizer",
                "Reviewer",
            ],
        )
        agent_logger.info(f"Saved QA result: {submit_response}")
        return {"submit_response": submit_response}

    def _run_fallback(self, state: QAWorkflowState) -> QAWorkflowState:
        state.update(self.download_files(state))
        state.update(self.parse_files(state))
        while True:
            state.update(self.locate_files(state))
            if self.route_after_locate(state) == "plan":
                break
        state.update(self.plan_extraction(state))
        state.update(self.extract_chunks(state))
        while True:
            state.update(self.synthesize_answer(state))
            state.update(self.review_answer(state))
            if self.route_after_review(state) == "submit":
                break
        state.update(self.submit_qa(state))
        return state
