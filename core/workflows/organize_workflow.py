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

class OrganizeWorkflow:
    def __init__(self, provider: ProviderService):
        self.provider = provider
        self.organizer = FileOrganizerAgent()
        self.keyword_extractor = KeywordExtractorAgent()
        
        self.download_dir = Path("downloaded_data")
        self.download_dir.mkdir(exist_ok=True)

    def execute(self, task):
        agent_logger.info("📁 Bắt đầu luồng File Organization...")
        
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
            
            try:
                chunks = parse_file(file_path)
                all_text = ""
                for chunk in chunks:
                    if chunk.chunk_type == "image":
                        continue
                    all_text += f"\n{chunk.content}"
                
                if not all_text.strip():
                    return {"success": False, "file_name": file_name, "error": "No text"}
                    
                all_text = all_text[:8000]
                kw_result = self.keyword_extractor.extract_keywords(all_text)
                return {
                    "success": True, 
                    "file_name": file_name, 
                    "thought_log": kw_result.thought_log, 
                    "keywords": ", ".join(kw_result.keywords)
                }
            except Exception as e:
                return {"success": False, "file_name": file_name, "error": str(e)}

        agent_logger.info(f"🔎 Đang nạp {len(local_files)} files vào KeywordExtractor (Chế độ đa luồng)...")
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

        # --- BƯỚC 3: PHÂN LOẠI THƯ MỤC ---
        agent_logger.info("🧠 Đang suy luận cách phân bổ thư mục...")
        result = self.organizer.organize_files(task.prompt_template, enhanced_file_list)
        full_thought_logs.append(f"[FileOrganizer]: {result.thought_log}")
        
        # Nộp bài
        submit_response = self.provider.submit_task(
            task_id=task.task_id,
            answers=[],  
            thought_log="\n".join(full_thought_logs),
            used_tools=["KeywordExtractor", "FileOrganizer"]
        )
        agent_logger.info(f"📤 Đã nộp bài Organize! Server: {submit_response}")


