import pytest
from pathlib import Path
from unittest.mock import MagicMock

from core.workflows.qa_workflow import QAWorkflow
from core.workflows.organize_workflow import OrganizeWorkflow
from dataProvider.models.task import Task, Resource
from core.utils.cache_manager import CacheManager

@pytest.fixture(autouse=True)
def clear_cache():
    # Xoá cache tránh xung đột giữa các unit test
    CacheManager.clear_all()

@pytest.fixture
def mock_provider():
    provider = MagicMock()
    return provider

def test_offline_organize_workflow(mock_provider):
    """
    Kiểm tra Workflow phân loại (Organize) chạy end-to-end (không xài Internet).
    Đồng thời verify CacheManager và Review Loop chạy đúng.
    """
    # Cấu hình Mock DataProvider trả về file Excel Offline (Mô phỏng download_file thành công)
    sample_path = Path("tests/sample_data/bang_tien_do.xlsx").absolute()
    mock_provider.download_file.return_value = str(sample_path)
    
    # Giả lập phản hồi Submit thành công
    mock_provider.submit_task.return_value = {"status": "success", "score": 10}

    # Tạo Task rỗng
    mock_task = Task(
        task_id="mock_org_id",
        prompt_template="Phân loại file thi công xây dựng vào đúng thư mục",
        resources=[Resource(file_path="mock_file.xlsx", file_type="excel", token="fake_token")]
    )

    workflow = OrganizeWorkflow(provider=mock_provider)
    
    # THỰC THI (Luồng Lần 1: Chưa có Cache)
    workflow.execute(mock_task)
    
    # Verify:
    mock_provider.download_file.assert_called()
    mock_provider.submit_task.assert_called()
    
    submit_args = mock_provider.submit_task.call_args[1]
    assert "thought_log" in submit_args
    assert "Reviewer" in submit_args["used_tools"]
    
    # Kiểm tra CacheManager đã hoạt động không
    assert CacheManager.get_cached_item("mock_file.xlsx", "keywords") is not None
    
    # THỰC THI (Luồng Lần 2: Sử dụng Cache)
    workflow.execute(mock_task)
    # Nếu cache thành công, thought_log submit lần 2 sẽ phải chứa keyword "[Cache HIT]"
    submit_args_2 = mock_provider.submit_task.call_args[1]
    assert "[Cache HIT]" in submit_args_2["thought_log"]


def test_offline_qa_workflow(mock_provider):
    """
    Kiểm tra Workflow hỏi đáp (QA) chạy end-to-end với dữ liệu ảnh PDF.
    """
    sample_path = Path("tests/sample_data/tai_lieu_dac_ta.pdf").absolute()
    mock_provider.download_file.return_value = str(sample_path)
    mock_provider.submit_task.return_value = {"status": "success"}

    mock_task = Task(
        task_id="mock_qa_id",
        prompt_template="Tìm tên hệ thống phát điện",
        resources=[Resource(file_path="mock_pdf.pdf", file_type="pdf", token="fake_token")]
    )

    workflow = QAWorkflow(provider=mock_provider)
    
    workflow.execute(mock_task)
    
    mock_provider.download_file.assert_called()
    mock_provider.submit_task.assert_called()

    submit_args = mock_provider.submit_task.call_args[1]
    assert "thought_log" in submit_args
    assert "Reviewer" in submit_args["used_tools"]
    assert "FileLocator" in submit_args["used_tools"]
