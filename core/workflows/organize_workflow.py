# core/workflows/organize_workflow.py
from pathlib import Path
from typing import List

from dataProvider import ProviderService
from ..utils.logger import agent_logger
from ..exceptions.agent_errors import ParsingError, LLMCommunicationError
from ..parsers.file_router import parse_file
from ..schemas.data_types import DocumentChunk

# Import Agents
from ..agents.file_organizer import FileOrganizerAgent
from ..agents.keyword_extractor import KeywordExtractorAgent
from ..agents.reviewer import ReviewerAgent
from ..utils.cache_manager import CacheManager

class OrganizeWorkflow:
    def __init__(self, provider: ProviderService):
        self.provider = provider
        self.organizer = FileOrganizerAgent()
        self.keyword_extractor = KeywordExtractorAgent()
        self.reviewer = ReviewerAgent()
        
        self.download_dir = Path("downloaded_data")
        self.download_dir.mkdir(exist_ok=True)

    def execute(self, task):
        agent_logger.info("Bắt đầu luồng File Organization...")
        
        # --- BƯỚC 1: TẢI FILE ---
        local_files = []
        for res in task.resources:
            local_path = self.download_dir / res.file_path
            local_path.parent.mkdir(parents=True, exist_ok=True)
            saved_path = self.provider.download_file(res.token, str(local_path))
            local_files.append({"path": saved_path, "name": res.file_path.split('/')[-1]})

        # --- BƯỚC 2: CHẾ BIẾN DỮ LIỆU & LẤY KEYWORD ---
        enhanced_file_list = []
        full_thought_logs = []
        
        import concurrent.futures

        def process_file_keyword(file_info):
            file_path = file_info["path"]
            file_name = file_info["name"]
            
            # Check Cache
            cached_keywords = CacheManager.get_cached_item(file_name, "keywords")
            cached_thought = CacheManager.get_cached_item(file_name, "keyword_thought_log")
            if cached_keywords and cached_thought:
                return {
                    "success": True,
                    "file_name": file_name,
                    "thought_log": f"[Cache HIT] Bỏ qua trích xuất, dùng lại kết quả cũ. Log: {cached_thought}",
                    "keywords": cached_keywords
                }
            
            try:
                chunks = parse_file(file_path)
                if not chunks:
                    return {"success": False, "file_name": file_name, "error": "Tập tin rỗng"}
                
                content_blocks = []
                # Chỉ lấy 3 chunk đầu tiên để tránh bị quá tải Token, 3 trang là đủ biết file là gì.
                for idx, chunk in enumerate(chunks[:3]):
                    if chunk.chunk_type == "image":
                        content_blocks.append({
                            "type": "text",
                            "text": f"\n- Trang {idx+1} (Hình ảnh đính kèm):"
                        })
                        content_blocks.append({
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{chunk.content}",
                                "detail": "auto"
                            }
                        })
                    else:
                        text_excerpt = chunk.content[:3000]
                        content_blocks.append({
                            "type": "text",
                            "text": f"\n- Trang {idx+1} (Dạng Văn bản):\n{text_excerpt}..."
                        })
                
                kw_result = self.keyword_extractor.extract_keywords(content_blocks)
                
                kws_str = ", ".join(kw_result.keywords)
                CacheManager.update_cache(file_name, "keywords", kws_str)
                CacheManager.update_cache(file_name, "keyword_thought_log", kw_result.thought_log)
                
                return {
                    "success": True, 
                    "file_name": file_name, 
                    "thought_log": kw_result.thought_log, 
                    "keywords": kws_str
                }
            except Exception as e:
                return {"success": False, "file_name": file_name, "error": str(e)}

        agent_logger.info(f"Đang nạp {len(local_files)} files vào KeywordExtractor (Chế độ đa luồng)...")
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            results = executor.map(process_file_keyword, local_files)
            
        for res in results:
            if res["success"]:
                enhanced_file_list.append(f"{res['file_name']} (Tóm tắt nội dung/Keyword: {res['keywords']})")
                full_thought_logs.append(f"[KeywordExtractor - {res['file_name']}]: {res['thought_log']}")
            else:
                if "error" in res and res["error"] != "No text":
                    agent_logger.error(f"Lỗi rút keyword file {res['file_name']}: {res['error']}")
                enhanced_file_list.append(res['file_name'])

        # --- BƯỚC 3: PHÂN LOẠI THƯ MỤC CÓ REVIEW ---
        agent_logger.info("🧠 Đang suy luận cách phân bổ thư mục...")
        max_attempts = 2
        attempt = 0
        is_acceptable = False
        issues_history = []
        
        while attempt < max_attempts and not is_acceptable:
            attempt += 1
            if issues_history:
                feedback = "\n\n[LƯU Ý TỪ REVIEWER LẦN TRƯỚC]:\n- " + "\n- ".join(issues_history)
                prompt_with_feedback = task.prompt_template + feedback
            else:
                prompt_with_feedback = task.prompt_template
                
            result = self.organizer.organize_files(prompt_with_feedback, enhanced_file_list)
            
            # Đánh giá kết quả
            review = self.reviewer.review_organize(task.prompt_template, result.thought_log)
            if review.is_acceptable:
                is_acceptable = True
                full_thought_logs.append(f"[FileOrganizer - Lần {attempt}]: {result.thought_log}\n[Reviewer Thẩm định]: OK. Chấp nhận.")
            else:
                issues_history.extend(review.issues)
                full_thought_logs.append(f"[FileOrganizer - Lần {attempt}]: {result.thought_log}\n[Reviewer TỪ CHỐI]: {review.issues}")
                agent_logger.warning(f"⚠️ Reviewer phát hiện lỗi phân loại: {review.issues}. Yêu cầu FileOrganizer sửa lỗi...")

        # Nộp bài
        submit_response = self.provider.submit_task(
            task_id=task.task_id,
            answers=[],  
            thought_log="\n".join(full_thought_logs),
            used_tools=["KeywordExtractor", "FileOrganizer", "Reviewer"]
        )
        agent_logger.info(f"Đã nộp bài Organize! Server: {submit_response}")


