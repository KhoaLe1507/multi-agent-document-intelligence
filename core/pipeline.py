# core/pipeline.py
import os
from pathlib import Path
from typing import List

from dataProvider import ProviderService
from .utils.logger import agent_logger
from .exceptions.agent_errors import ParsingError, LLMCommunicationError

# Import Parsers
from .parsers.file_router import parse_file
from .schemas.data_types import DocumentChunk

# Import Agents
from .agents import TaskRouterAgent, PlannerAgent, ExtractorAgent, SynthesizerAgent

class SystemPipeline:
    def __init__(self, provider: ProviderService):
        """Khởi tạo Pipeline với DataProvider và toàn bộ đội ngũ Agents."""
        self.provider = provider
        
        agent_logger.info("🤖 Đang khởi động đội ngũ Multi-Agents...")
        self.router = TaskRouterAgent()
        self.planner = PlannerAgent()
        self.extractor = ExtractorAgent()
        self.synthesizer = SynthesizerAgent()
        
        # Thư mục chứa dữ liệu tạm thời
        self.download_dir = Path("downloaded_data")
        self.download_dir.mkdir(exist_ok=True)

    def run_continuous(self):
        """Vòng lặp vô hạn: Lấy task -> Giải -> Nộp -> Lặp lại."""
        agent_logger.info("🚀 Bắt đầu vòng lặp thi đấu tự động!")
        while True:
            try:
                self.process_single_task()
            except Exception as e:
                agent_logger.critical(f"❌ Lỗi nghiêm trọng, dừng vòng lặp: {e}")
                break # Hoặc thêm time.sleep(10) rồi continue tùy chiến thuật của bạn

    def process_single_task(self):
        """Xử lý trọn vẹn 1 vòng đời của Task."""
        # 1. Lấy đề bài
        agent_logger.info("-" * 50)
        task = self.provider.get_next_task()
        agent_logger.info(f"📥 Đã nhận Task: {task.task_id}")
        agent_logger.info(f"📝 Yêu cầu: {task.prompt_template}")

        # 2. Định tuyến Task
        routing_result = self.router.classify_task(task.prompt_template)
        agent_logger.info(f"🔀 Quyết định rẽ nhánh: {routing_result.task_type} (Lý do: {routing_result.reasoning})")

        if routing_result.task_type == "ORGANIZE":
            self._handle_organize_flow(task)
        else:
            self._handle_qa_flow(task)

    def _handle_qa_flow(self, task):
        """Luồng xử lý Câu hỏi & Trích xuất (QA/Extraction)"""
        # --- BƯỚC 1: TẢI FILE ---
        local_files = []
        for res in task.resources:
            local_path = self.download_dir / res.file_path
            local_path.parent.mkdir(parents=True, exist_ok=True)
            
            agent_logger.debug(f"⬇️ Đang tải: {res.file_path}")
            saved_path = self.provider.download_file(res.token, str(local_path))
            local_files.append(saved_path)

        # --- BƯỚC 2: CHẾ BIẾN DỮ LIỆU (PARSING) ---
        all_chunks: List[DocumentChunk] = []
        for file_path in local_files:
            try:
                chunks = parse_file(file_path)
                all_chunks.extend(chunks)
            except ParsingError as e:
                agent_logger.error(f"Bỏ qua file lỗi {file_path}: {e}")
                
        if not all_chunks:
            agent_logger.warning("⚠️ Không có dữ liệu nào đọc được từ các file.")
            # Có thể báo cáo lỗi cho Synthesizer xử lý

        # --- BƯỚC 3: LẬP KẾ HOẠCH TÁC CHIẾN (PLANNING) ---
        plan = self.planner.create_extraction_plan(task.prompt_template)
        agent_logger.info(f"📋 Đã lập kế hoạch. Từ khóa trọng tâm: {', '.join(plan.target_keywords)}")

        # --- BƯỚC 4: TRÍCH XUẤT SONG SONG (MAPPING) ---
        extracted_pieces = []
        for idx, chunk in enumerate(all_chunks):
            agent_logger.debug(f"🕵️ Extractor đang đọc chunk {idx + 1}/{len(all_chunks)}...")
            try:
                result = self.extractor.extract_from_chunk(
                    chunk=chunk,
                    guidelines=plan.extraction_guidelines,
                    keywords=plan.target_keywords
                )
                if result.found_information and result.extracted_data:
                    extracted_pieces.append({
                        "data": result.extracted_data,
                        "confidence_score": result.confidence_score,
                        "source": chunk.get_context_description()
                    })
            except LLMCommunicationError:
                agent_logger.error(f"Lỗi gọi LLM ở chunk {idx+1}. Đang bỏ qua...")

        # --- BƯỚC 5: TỔNG HỢP & CHỐT ĐÁP ÁN (REDUCING) ---
        agent_logger.info(f"🧩 Đã tìm thấy {len(extracted_pieces)} mảnh thông tin. Đang tổng hợp...")
        final_result = self.synthesizer.synthesize_final_answer(task.prompt_template, extracted_pieces)
        
        agent_logger.success(f"🎯 Đáp án chốt: {final_result.final_answers}")

        # --- BƯỚC 6: NỘP BÀI (SUBMIT) ---
        submit_response = self.provider.submit_task(
            task_id=task.task_id,
            answers=final_result.final_answers,
            thought_log=final_result.thought_log,
            used_tools=["TaskRouter", "UniversalParser", "Planner", "Extractor", "Synthesizer"]
        )
        agent_logger.info(f"📤 Đã nộp bài thành công! Phản hồi từ server: {submit_response}")

    # Mở file core/pipeline.py và cập nhật hàm này:

    def _handle_organize_flow(self, task):
        """Luồng Sắp xếp thư mục (Theo đúng chuẩn tài liệu BTC)"""
        agent_logger.info("📁 Kích hoạt luồng File Organizer...")
        
        # Lấy danh sách tên file từ task.resources
        file_names = [res.file_path.split('/')[-1] for res in task.resources]
        
        # Khởi tạo Agent (hoặc bạn có thể khởi tạo ở __init__ của class)
        from .agents.file_organizer import FileOrganizerAgent
        organizer = FileOrganizerAgent()
        
        # Bắt AI suy luận để lấy thought_log
        agent_logger.info("🧠 Đang phân tích logic sắp xếp thư mục...")
        result = organizer.organize_files(task.prompt_template, file_names)
        
        # Submit ĐÚNG luật: answers là mảng rỗng, thought_log chứa nội dung
        submit_response = self.provider.submit_task(
            task_id=task.task_id,
            answers=[],  # <--- SỬA QUAN TRỌNG: Mảng rỗng theo yêu cầu
            thought_log=result.thought_log, # <--- SỬA QUAN TRỌNG: Nộp logic để BTC chấm điểm
            used_tools=["TaskRouter", "FileOrganizer"]
        )
        agent_logger.info(f"📤 Đã nộp bài luồng Organize! Phản hồi: {submit_response}")