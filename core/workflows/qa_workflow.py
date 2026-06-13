# core/workflows/qa_workflow.py
from pathlib import Path
from typing import List

from dataProvider import ProviderService
from ..utils.logger import agent_logger
from ..exceptions.agent_errors import ParsingError, LLMCommunicationError
from ..parsers.file_router import parse_file
from ..schemas.data_types import DocumentChunk

# Import các Agent liên quan đến luồng QA
from ..agents import FileLocatorAgent, PlannerAgent, ExtractorAgent, SynthesizerAgent, ReviewerAgent
from ..utils.cache_manager import CacheManager

from ..graphs.qa_graph import QAWorkflowGraph as _QAWorkflowGraph


class QAWorkflow:
    """Compatibility wrapper around the LangGraph QA workflow."""

    def __init__(self, provider: ProviderService):
        self.graph = _QAWorkflowGraph(provider)

    def execute(self, task):
        agent_logger.info("Starting Question Answering (QA) LangGraph workflow...")
        return self.graph.execute(task)


class LegacyQAWorkflow:
    def __init__(self, provider: ProviderService):
        self.provider = provider
        self.locator = FileLocatorAgent()
        self.planner = PlannerAgent()
        self.extractor = ExtractorAgent()
        self.synthesizer = SynthesizerAgent()
        self.reviewer = ReviewerAgent()
        
        self.download_dir = Path("downloaded_data")
        self.download_dir.mkdir(exist_ok=True)

    def execute(self, task):
        agent_logger.info("Bắt đầu luồng Question Answering (QA)...")
        
        # --- BƯỚC 1: TẢI FILE ---
        local_files = []
        for res in task.resources:
            local_path = self.download_dir / res.file_path
            local_path.parent.mkdir(parents=True, exist_ok=True)
            saved_path = self.provider.download_file(res.token, str(local_path))
            local_files.append(saved_path)

        # --- BƯỚC 2: CHẾ BIẾN DỮ LIỆU ---
        all_chunks: List[DocumentChunk] = []
        for file_path in local_files:
            file_name = file_path.split('/')[-1] if isinstance(file_path, str) else Path(file_path).name
            
            cached_chunks = CacheManager.get_cached_item(file_name, "chunks")
            if cached_chunks:
                agent_logger.info(f"⚡ [Cache HIT] Dùng lại dữ liệu parse của {file_name}.")
                all_chunks.extend(cached_chunks)
            else:
                try:
                    chunks = parse_file(str(file_path))
                    CacheManager.update_cache(file_name, "chunks", chunks)
                    all_chunks.extend(chunks)
                except ParsingError as e:
                    agent_logger.error(f"Bỏ qua file lỗi {file_path}: {e}")

        # --- BƯỚC 3: TRINH SÁT (FILE LOCATOR) ---
        target_file_names = set()
        
        # Tạo mapping file_name -> list_of_chunks
        chunks_by_file = {}
        for chunk in all_chunks:
            chunks_by_file.setdefault(chunk.file_name, []).append(chunk)
            
        # Khởi tạo context đọc (bắt đầu bằng index 0 cho mỗi file)
        file_read_index = {fname: 0 for fname in chunks_by_file.keys()}
        active_files = set(chunks_by_file.keys())  # Các file cần phân tích
        
        max_locator_loops = 5
        loop_count = 0
        
        agent_logger.info("Trinh sát đang quét mục tiêu...")
        full_thought_logs = []
        
        while active_files and loop_count < max_locator_loops:
            loop_count += 1
            
            # Khởi tạo mảng content blocks hỗ trợ Vision
            user_content_blocks = [
                {"type": "text", "text": f"<Task Instruction>\n{task.prompt_template}\n\n<Document List and Current Content>\n"}
            ]

            for fname in active_files:
                idx = file_read_index[fname]
                if idx < len(chunks_by_file[fname]):
                    chunk = chunks_by_file[fname][idx]
                    
                    if chunk.chunk_type == "image":
                        user_content_blocks.append({
                            "type": "text",
                            "text": f"\n- File: {fname} (Page/Chunk {idx+1}) | Image content attached:"
                        })
                        user_content_blocks.append({
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{chunk.content}",
                                "detail": "auto" 
                            }
                        })
                    else:
                        text_excerpt = chunk.content[:1500]
                        user_content_blocks.append({
                            "type": "text",
                            "text": f"\n- File: {fname} (Page/Chunk {idx+1}) | Text content:\n{text_excerpt}..."
                        })
                else:
                    user_content_blocks.append({
                        "type": "text",
                        "text": f"\n- File: {fname} | [END OF DOCUMENT CONTENT]"
                    })
                    
            user_content_blocks.append({
                "type": "text",
                "text": "\nAnalyze the document pages above.\nDetermine which files are CONFIRMED RELEVANT, which are CONFIRMED IRRELEVANT, and which NEED MORE PAGES to decide."
            })
            
            locator_result = self.locator.locate_files_advanced(user_content_blocks)
            full_thought_logs.append(f"[FileLocator - Round {loop_count}]: {locator_result.reasoning}")
            
            # Gộp các file target mà Agent đã chắc chắn
            for f in locator_result.target_file_names:
                target_file_names.add(f)
            
            if not locator_result.requires_more_info:
                break
                
            # Cập nhật danh sách các file cần đọc thêm ở vòng lặp sau
            next_active_files = set()
            for fname in locator_result.files_needing_more_chunks:
                if fname in chunks_by_file and file_read_index[fname] + 1 < len(chunks_by_file[fname]):
                    file_read_index[fname] += 1
                    next_active_files.add(fname)
                    
            active_files = next_active_files
            
        agent_logger.info(f"Mục tiêu đã khóa: {list(target_file_names)}")
        
        # Lọc chunk theo mục tiêu (Fallback nếu trinh sát xịt)
        target_chunks = [c for c in all_chunks if c.file_name in target_file_names]
        if not target_chunks:
            target_chunks = all_chunks

        # --- BƯỚC 4: LÊN KẾ HOẠCH ---
        plan = self.planner.create_extraction_plan(task.prompt_template)
        full_thought_logs.append(f"[Planner]: {plan.thought_log}")
        
        import concurrent.futures
        
        # --- BƯỚC 5: XẠ THỦ TRÍCH XUẤT ---
        extracted_pieces = []
        
        def process_chunk_extraction(item):
            idx, chunk = item
            agent_logger.debug(f"Đa luồng: Đang soi chunk {idx + 1}/{len(target_chunks)}...")
            try:
                result = self.extractor.extract_from_chunk(chunk, plan.extraction_guidelines, plan.target_keywords)
                return {"success": True, "idx": idx, "chunk": chunk, "result": result}
            except Exception as e:
                return {"success": False, "idx": idx, "chunk": chunk, "error": str(e)}

        agent_logger.info(f"Kích hoạt {len(target_chunks)} Xạ thủ trích xuất (Chế độ đa luồng)...")
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            items = list(enumerate(target_chunks))
            results = executor.map(process_chunk_extraction, items)
            
        for res in results:
            idx = res["idx"]
            chunk = res["chunk"]
            if res["success"]:
                result = res["result"]
                full_thought_logs.append(f"[Extractor - {chunk.file_name} Page {idx+1}]: {result.thought_log}")
                if result.found_information and result.extracted_data:
                    extracted_pieces.append({
                        "data": result.extracted_data,
                        "confidence_score": result.confidence_score,
                        "source": chunk.get_context_description()
                    })
            else:
                agent_logger.error(f"Lỗi gọi LLM ở chunk {idx+1}: {res['error']}. Bỏ qua.")

        # --- BƯỚC 6: TỔNG HỢP CÓ REVIEW ---
        agent_logger.info("🧠 Đang tổng hợp kết quả...")
        max_attempts = 2
        attempt = 0
        is_acceptable = False
        issues_history = []
        
        while attempt < max_attempts and not is_acceptable:
            attempt += 1
            if issues_history:
                feedback = "\n\n[REVIEWER FEEDBACK FROM PREVIOUS ROUND]:\n- " + "\n- ".join(issues_history)
                prompt_with_feedback = task.prompt_template + feedback
            else:
                prompt_with_feedback = task.prompt_template
                
            final_result = self.synthesizer.synthesize_final_answer(prompt_with_feedback, extracted_pieces)
            
            # Đánh giá
            review = self.reviewer.review_qa(task.prompt_template, final_result.final_answers, final_result.thought_log)
            if review.is_acceptable:
                is_acceptable = True
                full_thought_logs.append(f"[Synthesizer - Attempt {attempt}]: {final_result.thought_log}\n[Reviewer Audit]: OK. Answer accepted.")
            else:
                issues_history.extend(review.issues)
                full_thought_logs.append(f"[Synthesizer - Attempt {attempt}]: {final_result.thought_log}\n[Reviewer REJECTED]: {review.issues}")
                agent_logger.warning(f"⚠️ Reviewer phát hiện lỗi QA: {review.issues}. Yêu cầu Synthesizer viết lại đáp án...")

        submit_response = self.provider.submit_task(
            task_id=task.task_id,
            answers=final_result.final_answers,
            thought_log="\n".join(full_thought_logs),
            used_tools=["FileLocator", "Planner", "Extractor", "Synthesizer", "Reviewer"]
        )
        agent_logger.info(f"Đã lưu kết quả QA: {submit_response}")

