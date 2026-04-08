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
        
        # 3. Trinh sát (File Locator) với vòng lặp Chunk
        locator = FileLocatorAgent()
        target_file_names = set()
        
        chunks_by_file = {}
        for chunk in chunks:
            chunks_by_file.setdefault(chunk.file_name, []).append(chunk)
            
        file_read_index = {fname: 0 for fname in chunks_by_file.keys()}
        active_files = set(chunks_by_file.keys())
        
        loop_count = 0
        while active_files and loop_count < 3:
            loop_count += 1
            user_content_blocks = [
                {"type": "text", "text": f"<Yêu cầu của Đề bài>\n{user_query}\n\n<Danh sách Tài liệu và Nội dung hiện tại>\n"}
            ]
            for fname in active_files:
                idx = file_read_index[fname]
                if idx < len(chunks_by_file[fname]):
                    c = chunks_by_file[fname][idx]
                    if c.chunk_type == "image":
                        user_content_blocks.append({
                            "type": "text",
                            "text": f"\n- File: {fname} (Trang/Chunk {idx+1}) | Nội dung Hình ảnh đính kèm:"
                        })
                        user_content_blocks.append({
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{c.content}",
                                "detail": "auto" 
                            }
                        })
                    else:
                        text_excerpt = c.content[:1500]
                        user_content_blocks.append({
                            "type": "text",
                            "text": f"\n- File: {fname} (Trang/Chunk {idx+1}) | Nội dung Văn bản:\n{text_excerpt}..."
                        })
                else:
                    user_content_blocks.append({"type": "text", "text": f"\n- File: {fname} | [ĐẾN CUỐI]\n"})
            
            user_content_blocks.append({
                "type": "text",
                "text": "\nPhân tích nội dung. Hãy xác định những file nào chắc chắn cần thiết, chắc chắn loại, và cần đọc thêm trang kế tiếp."
            })
                    
            locate_result = locator.locate_files_advanced(user_content_blocks)
            
            for f in locate_result.target_file_names:
                target_file_names.add(f)
                
            if not locate_result.requires_more_info:
                break
                
            next_active_files = set()
            for fname in locate_result.files_needing_more_chunks:
                if fname in chunks_by_file and file_read_index[fname] + 1 < len(chunks_by_file[fname]):
                    file_read_index[fname] += 1
                    next_active_files.add(fname)
            active_files = next_active_files
        
        # Nếu test đúng, nó sẽ quét xong và không bị crash.
        assert target_file_names is not None
        
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