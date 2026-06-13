from __future__ import annotations

import concurrent.futures
import shutil
from pathlib import Path
from typing import Literal

from dataProvider import ProviderService

from ..agents.file_organizer import FileOrganizerAgent
from ..agents.keyword_extractor import KeywordExtractorAgent
from ..agents.reviewer import ReviewerAgent
from ..parsers.file_router import parse_file
from ..utils.cache_manager import CacheManager
from ..utils.logger import agent_logger
from .state import OrganizeWorkflowState

try:
    from langgraph.graph import END, START, StateGraph
except ImportError:
    END = START = StateGraph = None


class OrganizeWorkflowGraph:
    """Stateful LangGraph orchestration for folder organization tasks."""

    def __init__(self, provider: ProviderService):
        self.provider = provider
        self.organizer = FileOrganizerAgent()
        self.keyword_extractor = KeywordExtractorAgent()
        self.reviewer = ReviewerAgent()

        self.download_dir = Path("downloaded_data")
        self.download_dir.mkdir(exist_ok=True)
        self.graph = self._compile_graph()

    def execute(self, task) -> OrganizeWorkflowState:
        initial_state: OrganizeWorkflowState = {
            "task": task,
            "local_files": [],
            "enhanced_file_list": [],
            "thought_log": [],
            "review_issues": [],
            "organize_attempt": 0,
            "max_attempts": 2,
        }
        if self.graph is None:
            return self._run_fallback(initial_state)
        return self.graph.invoke(initial_state, {"recursion_limit": 30})

    def _compile_graph(self):
        if StateGraph is None:
            agent_logger.warning(
                "LangGraph is not installed. Falling back to imperative organize workflow."
            )
            return None

        builder = StateGraph(OrganizeWorkflowState)
        builder.add_node("download_files", self.download_files)
        builder.add_node("extract_keywords", self.extract_keywords)
        builder.add_node("organize_files", self.organize_files)
        builder.add_node("review_organization", self.review_organization)
        builder.add_node("copy_organized_files", self.copy_organized_files)
        builder.add_node("submit_organization", self.submit_organization)

        builder.add_edge(START, "download_files")
        builder.add_edge("download_files", "extract_keywords")
        builder.add_edge("extract_keywords", "organize_files")
        builder.add_edge("organize_files", "review_organization")
        builder.add_conditional_edges(
            "review_organization",
            self.route_after_review,
            {
                "retry": "organize_files",
                "copy": "copy_organized_files",
                "submit": "submit_organization",
            },
        )
        builder.add_edge("copy_organized_files", "submit_organization")
        builder.add_edge("submit_organization", END)
        return builder.compile()

    def download_files(self, state: OrganizeWorkflowState) -> dict:
        task = state["task"]
        local_files: list[dict[str, str]] = []
        for res in task.resources:
            local_path = self.download_dir / res.file_path
            local_path.parent.mkdir(parents=True, exist_ok=True)
            saved_path = self.provider.download_file(res.token, str(local_path))
            pure_name = res.file_path.replace("\\", "/").split("/")[-1]
            local_files.append({"path": saved_path, "name": pure_name})
        return {"local_files": local_files}

    def extract_keywords(self, state: OrganizeWorkflowState) -> dict:
        thought_log = list(state.get("thought_log", []))

        def process_file_keyword(file_info):
            file_path = file_info["path"]
            file_name = file_info["name"]

            cached_keywords = CacheManager.get_cached_item(file_name, "keywords")
            cached_thought = CacheManager.get_cached_item(file_name, "keyword_thought_log")
            if cached_keywords and cached_thought:
                return {
                    "success": True,
                    "file_name": file_name,
                    "thought_log": (
                        "[Cache HIT] Skipping extraction, reusing cached result. "
                        f"Log: {cached_thought}"
                    ),
                    "keywords": cached_keywords,
                }

            try:
                chunks = parse_file(file_path)
                if not chunks:
                    return {"success": False, "file_name": file_name, "error": "Empty file"}

                content_blocks = []
                offset = 0
                step = 3
                max_iterations = 5
                iteration = 0
                last_kw_result = None

                while iteration < max_iterations and offset < len(chunks):
                    current_chunks = chunks[offset : offset + step]
                    if not current_chunks:
                        break

                    for idx, chunk in enumerate(current_chunks):
                        actual_page = offset + idx + 1
                        if chunk.chunk_type == "image":
                            content_blocks.append(
                                {
                                    "type": "text",
                                    "text": f"\n- Page {actual_page} (Image attachment):",
                                }
                            )
                            content_blocks.append(
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:image/jpeg;base64,{chunk.content}",
                                        "detail": "auto",
                                    },
                                }
                            )
                        else:
                            content_blocks.append(
                                {
                                    "type": "text",
                                    "text": (
                                        f"\n- Page {actual_page} (Text content):\n"
                                        f"{chunk.content[:3000]}..."
                                    ),
                                }
                            )

                    kw_result = self.keyword_extractor.extract_keywords(content_blocks)
                    last_kw_result = kw_result
                    if not kw_result.needs_more_chunks:
                        break
                    offset += step
                    iteration += 1

                keywords = ", ".join(last_kw_result.keywords) if last_kw_result else ""
                keyword_thought = (
                    last_kw_result.thought_log if last_kw_result else "Document has no content."
                )
                CacheManager.update_cache(file_name, "keywords", keywords)
                CacheManager.update_cache(file_name, "keyword_thought_log", keyword_thought)
                return {
                    "success": True,
                    "file_name": file_name,
                    "thought_log": keyword_thought,
                    "keywords": keywords,
                }
            except Exception as exc:
                return {"success": False, "file_name": file_name, "error": str(exc)}

        agent_logger.info(
            f"Launching {len(state['local_files'])} keyword agents through the organize graph."
        )
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            results = executor.map(process_file_keyword, state["local_files"])

        enhanced_file_list: list[str] = []
        for res in results:
            if res["success"]:
                enhanced_file_list.append(
                    f"{res['file_name']} (Content Summary / Keywords: {res['keywords']})"
                )
                thought_log.append(
                    f"[KeywordExtractor - {res['file_name']}]: {res['thought_log']}"
                )
            else:
                if res.get("error") != "No text":
                    agent_logger.error(
                        f"Keyword extraction failed for {res['file_name']}: {res.get('error')}"
                    )
                enhanced_file_list.append(res["file_name"])

        return {"enhanced_file_list": enhanced_file_list, "thought_log": thought_log}

    def organize_files(self, state: OrganizeWorkflowState) -> dict:
        attempt = state.get("organize_attempt", 0) + 1
        review_issues = state.get("review_issues", [])
        if review_issues:
            feedback = "\n\n[REVIEWER FEEDBACK FROM PREVIOUS ROUND]:\n- " + "\n- ".join(
                review_issues
            )
            prompt = state["task"].prompt_template + feedback
        else:
            prompt = state["task"].prompt_template

        result = self.organizer.organize_files(prompt, state.get("enhanced_file_list", []))
        return {"organize_result": result, "organize_attempt": attempt}

    def review_organization(self, state: OrganizeWorkflowState) -> dict:
        result = state["organize_result"]
        review = self.reviewer.review_organize(state["task"].prompt_template, result.thought_log)
        thought_log = list(state.get("thought_log", []))
        if review.is_acceptable:
            thought_log.append(
                f"[FileOrganizer - Attempt {state.get('organize_attempt', 1)}]: "
                f"{result.thought_log}\n[Reviewer Audit]: OK. Accepted."
            )
        else:
            thought_log.append(
                f"[FileOrganizer - Attempt {state.get('organize_attempt', 1)}]: "
                f"{result.thought_log}\n[Reviewer REJECTED]: {review.issues}"
            )
            agent_logger.warning(
                "Reviewer rejected organization result: "
                f"{review.issues}. Retrying if budget remains."
            )

        return {
            "review": review,
            "review_issues": list(state.get("review_issues", [])) + list(review.issues),
            "thought_log": thought_log,
        }

    def route_after_review(
        self, state: OrganizeWorkflowState
    ) -> Literal["retry", "copy", "submit"]:
        review = state.get("review")
        if review is not None and review.is_acceptable:
            return "copy"
        if (
            review is not None
            and not review.is_acceptable
            and state.get("organize_attempt", 0) < state.get("max_attempts", 2)
        ):
            return "retry"
        return "submit"

    def copy_organized_files(self, state: OrganizeWorkflowState) -> dict:
        result = state.get("organize_result")
        if result is None:
            return {}

        organized_dir = self.download_dir / "organized_output" / state["task"].task_id
        name_to_path = {file_info["name"]: file_info["path"] for file_info in state["local_files"]}

        try:
            for allocation in result.file_allocations:
                filename = allocation.file_name
                folder_desc = allocation.folder_name
                if filename not in name_to_path:
                    continue

                clean_folder_name = folder_desc.split(":")[0].strip()
                clean_folder_name = "".join(
                    char for char in clean_folder_name if char not in r'\/:*?"<>|'
                )

                target_folder = organized_dir / clean_folder_name
                target_folder.mkdir(parents=True, exist_ok=True)
                shutil.copy2(name_to_path[filename], target_folder / filename)
                agent_logger.debug(f"Copied {filename} into '{clean_folder_name}'.")
            agent_logger.info(f"Saved organized files to {organized_dir}.")
        except Exception as exc:
            agent_logger.error(f"Failed to copy organized files: {exc}")

        return {"organized_dir": str(organized_dir)}

    def submit_organization(self, state: OrganizeWorkflowState) -> dict:
        submit_response = self.provider.submit_task(
            task_id=state["task"].task_id,
            answers=[],
            thought_log="\n".join(state.get("thought_log", [])),
            used_tools=["LangGraph", "KeywordExtractor", "FileOrganizer", "Reviewer"],
        )
        agent_logger.info(f"Saved organization result: {submit_response}")
        return {"submit_response": submit_response}

    def _run_fallback(self, state: OrganizeWorkflowState) -> OrganizeWorkflowState:
        state.update(self.download_files(state))
        state.update(self.extract_keywords(state))
        while True:
            state.update(self.organize_files(state))
            state.update(self.review_organization(state))
            route = self.route_after_review(state)
            if route == "retry":
                continue
            if route == "copy":
                state.update(self.copy_organized_files(state))
            break
        state.update(self.submit_organization(state))
        return state
