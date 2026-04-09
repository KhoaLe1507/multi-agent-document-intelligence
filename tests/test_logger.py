import os
import pytest
from pathlib import Path
from core.utils.trace_logger import TaskTracer

@pytest.fixture
def tracer():
    # Khởi tạo Tracer mới hoàn toàn trước mỗi ca test (Xóa cache Singleton)
    TaskTracer._instance = None
    return TaskTracer()

class MockResource:
    """Class giả lập Resource giống cấu trúc dataProvider.models.Task"""
    def __init__(self, path, ftype):
        self.file_path = path
        self.file_type = ftype
        self.token = "abc123token"

def test_task_tracer_end_to_end(tracer, tmp_path, monkeypatch):
    """Giả lập 1 kịch bản chạy Task và kiểm tra xuất file Nhật ký Markdown"""
    # 1. Đổi thư mục lưu xuất TRACE_DIR tới thư mục rác (tmp_path)
    monkeypatch.setattr("core.utils.trace_logger.TRACE_DIR", tmp_path)
    
    mock_resources = [
        MockResource("ho_so_xay_dung.pdf", "pdf"),
        MockResource("anh_ky.jpg", "image")
    ]
    
    # 2. Khởi động Task
    task_id = "test-uuid-5678"
    tracer.start_task(task_id, "Yêu cầu: Lấy toàn bộ số liệu", resources=mock_resources)
    tracer.set_task_type("QA_WORKFLOW")
    
    # 3. Ghi chép 2 log từ 2 con Agent
    tracer.add_agent_span(
        agent_name="TaskRouter",
        system_prompt="Mày là bộ định tuyến",
        user_prompt="Hãy chọn đường đi",
        response={"task_type": "QA"}  # Demo ném Object vào thử
    )
    
    tracer.add_agent_span(
        agent_name="Extractor",
        system_prompt="Mày là máy trích xuất",
        user_prompt=[{"type": "image_url"}],  # Demo ném 1 khối list kiểu Vision vào thử
        response="Không tìm thấy gì"
    )
    
    # 4. End Task và kiểm tra File Dump
    tracer.end_task()
    
    output_file = tmp_path / f"task_{task_id}.md"
    assert output_file.exists(), f"Không tìm thấy file output ở {output_file}"
    
    # 5. Phân tích nội dung MD có bị rỗng/thiết sót không
    logs = output_file.read_text(encoding="utf-8")
    
    assert task_id in logs, "Mất tiêu đề ID"
    assert "Yêu cầu: Lấy toàn bộ số liệu" in logs, "Mất đề bài gốc"
    assert "QA_WORKFLOW" in logs, "Mất định danh Task Type"
    assert "ho_so_xay_dung.pdf" in logs, "Mất Resource số 1"
    assert "anh_ky.jpg" in logs, "Mất Resource số 2"
    
    assert "TaskRouter" in logs, "Mất Agent 1"
    assert "Extractor" in logs, "Mất Agent 2"
    assert "Mày là máy trích xuất" in logs
    assert "[Đã nén và gửi 1 hình ảnh Vision Base64]" in logs, "Lỗi format xử lý Vision prompt"
    assert "Không tìm thấy gì" in logs
