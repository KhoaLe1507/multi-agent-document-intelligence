# core/workflows/qa_workflow.py
from pathlib import Path
from typing import List

from dataProvider import ProviderService
from ..utils.logger import agent_logger
from ..exceptions.agent_errors import ParsingError, LLMCommunicationError
from ..parsers.file_router import parse_file
from ..schemas.data_types import DocumentChunk

# Import các Agent liên quan đến luồng QA
from ..agents import FileLocatorAgent, PlannerAgent, ExtractorAgent, SynthesizerAgent

class QAWorkflow:
    def __init__(self, provider: ProviderService):
        self.provider = provider
        self.locator = FileLocatorAgent()
        self.planner = PlannerAgent()
        self.extractor = ExtractorAgent()
        self.synthesizer = SynthesizerAgent()
        
        self.download_dir = Path("downloaded_data")
        self.download_dir.mkdir(exist_ok=True)

    def execute(self, task):
        agent_logger.info("🔬 Bắt đầu luồng Question Answering (QA)...")
        
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
            try:
                chunks = parse_file(file_path)
                all_chunks.extend(chunks)
            except ParsingError as e:
                agent_logger.error(f"Bỏ qua file lỗi {file_path}: {e}")

        # --- BƯỚC 3: TRINH SÁT (FILE LOCATOR) ---
        doc_summaries = ""
        processed_files = set()
        for chunk in all_chunks:
            if chunk.file_name not in processed_files:
                doc_summaries += f"- File: {chunk.file_name} | Đoạn đầu: {chunk.content[:300]}...\n"
                processed_files.add(chunk.file_name)
                
        agent_logger.info("🔭 Trinh sát đang quét mục tiêu...")
        locator_result = self.locator.locate_files(task.prompt_template, doc_summaries)
        agent_logger.info(f"🎯 Mục tiêu đã khóa: {locator_result.target_file_names}")
        
        # Lọc chunk theo mục tiêu (Fallback nếu trinh sát xịt)
        target_chunks = [c for c in all_chunks if c.file_name in locator_result.target_file_names]
        if not target_chunks:
            target_chunks = all_chunks

        # --- BƯỚC 4: LÊN KẾ HOẠCH ---
        plan = self.planner.create_extraction_plan(task.prompt_template)
        
        # --- BƯỚC 5: XẠ THỦ TRÍCH XUẤT ---
        extracted_pieces = []
        for idx, chunk in enumerate(target_chunks):
            agent_logger.debug(f"🕵️ Đang soi chunk {idx + 1}/{len(target_chunks)}...")
            try:
                result = self.extractor.extract_from_chunk(chunk, plan.extraction_guidelines, plan.target_keywords)
                if result.found_information and result.extracted_data:
                    extracted_pieces.append({
                        "data": result.extracted_data,
                        "confidence_score": result.confidence_score,
                        "source": chunk.get_context_description()
                    })
            except LLMCommunicationError:
                agent_logger.error(f"Lỗi gọi LLM ở chunk {idx+1}. Bỏ qua.")

        # --- BƯỚC 6: TỔNG HỢP & NỘP BÀI ---
        final_result = self.synthesizer.synthesize_final_answer(task.prompt_template, extracted_pieces)
        
        submit_response = self.provider.submit_task(
            task_id=task.task_id,
            answers=final_result.final_answers,
            thought_log=final_result.thought_log,
            used_tools=["FileLocator", "Planner", "Extractor", "Synthesizer"]
        )
        agent_logger.info(f"📤 Đã nộp bài QA! Server: {submit_response}")

