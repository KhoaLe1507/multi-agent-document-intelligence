import pytest
from unittest.mock import patch
from core.parsers.file_router import parse_file
from core.agents.task_router import TaskRouterAgent
from core.agents.file_locator import FileLocatorAgent
from core.agents.base_agent import BaseAgent # Hoặc ExtractorAgent cụ thể của bạn

class TestQAFlow:

    def test_full_qa_extract_flow(self):
        # Giả sử ta có yêu cầu về nội dung trong file PDF
        user_query = "Dự án này có tên là gì và do ai thực hiện?"
        pdf_path = "tests/sample_data/tai_lieu_dac_ta.pdf"
        
        # 1. Parse dữ liệu (Chuyển PDF thành Vision Chunks)
        chunks = parse_file(pdf_path)
        
        # 2. Router nhận diện Task
        router = TaskRouterAgent()
        route_result = router.classify_task(user_query)
        assert route_result.task_type == "QA"
        
        # 3. Locator tìm file liên quan (Dựa trên tóm tắt)
        locator = FileLocatorAgent()
        locate_result = locator.locate_relevant_files(chunks, user_query)
        
        # 4. QA/Extractor Agent đọc nội dung cụ thể
        # Ở đây ta gọi trực tiếp một Agent xử lý vision để test khả năng đọc
        qa_agent = BaseAgent(agent_name="QA_Tester", temperature=1.0) 
        
        # Giả sử ta gửi trang đầu tiên (thường chứa tên dự án) cho AI
        system_msg = "Bạn là chuyên gia đọc tài liệu xây dựng."
        user_msg = f"Dựa vào ảnh sau, trả lời câu hỏi: {user_query}"
        
        # Gửi kèm ảnh Base64 từ chunk
        response = qa_agent.call_llm(system_msg, f"{user_msg}\nContent: {chunks[0].content[:100]}...")
        
        assert response is not None
        print(f"\n✅ Luồng QA OK. AI phản hồi: {response[:100]}...")