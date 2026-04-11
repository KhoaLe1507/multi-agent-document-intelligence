# tests/test_data_pipeline.py
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock


#  QUAN TRỌNG: TUYỆT ĐỐI KHÔNG IMPORT THƯ MỤC `core.agents` Ở ĐÂY
from core.parsers.file_router import parse_file
from core.schemas.data_types import DocumentChunk
from dataProvider import ProviderService

# Lấy đường dẫn tuyệt đối đến thư mục chứa file mẫu
SAMPLE_DATA_DIR = Path(__file__).parent / "sample_data"

class TestDataPipeline:

    # ==========================================
    # 1. TEST CHUNKING & PARSING (FILE THẬT, OFFLINE)
    # ==========================================
    
    def test_excel_to_markdown_chunking(self):
        """Test xem file Excel thật có được băm thành Markdown Table chuẩn không."""
        excel_file = SAMPLE_DATA_DIR / "bang_tien_do.xlsx"
        
        if not excel_file.exists():
            pytest.skip(f"Chưa tìm thấy file mẫu: {excel_file.name}")

        chunks = parse_file(str(excel_file))
        assert len(chunks) > 0, "Parser không tạo ra được chunk nào!"
        
        # CHÚ Ý DÒNG NÀY: Dùng chunks[0] thay vì chunk
        assert chunks[0].chunk_type == "table", "Sai loại chunk"
        print(f"\n[Parser] Excel băm thành công {len(chunks)} chunks.")

    def test_pdf_to_vision_chunking(self):
        """Test xem file PDF thật có được cắt thành ảnh Base64 chuẩn không."""
        pdf_file = SAMPLE_DATA_DIR / "tai_lieu_dac_ta.pdf"
        
        if not pdf_file.exists():
            pytest.skip(f"Chưa tìm thấy file mẫu: {pdf_file.name}")

        chunks = parse_file(str(pdf_file))
        assert len(chunks) > 0, "Parser không cắt được trang PDF nào!"
        assert chunks[0].chunk_type == "image", "Sai loại chunk"
        print(f"\n[Parser] PDF cắt thành công {len(chunks)} trang ảnh.")


    # ==========================================
    # 2. TEST DATAPROVIDER (MOCK 100% NETWORK)
    # ==========================================
    
    # 2a. Mock lệnh GET (Lấy đề bài) và POST (Tạo session)
    @patch('requests.post') 
    @patch('requests.get')
    def test_provider_fetch_task_mock(self, mock_get, mock_post):
        """Giả lập lấy Task mới từ Server (Không gọi API thật)."""
        # Giả lập Server trả về Session ID
        mock_session_response = MagicMock()
        mock_session_response.json.return_value = {   
            "session_id": "mock_session_123", 
            "access_token": "Bearer abc", 
            "expires_in": 3600
        }
        mock_post.return_value = mock_session_response

        # Giả lập Server trả về Đề bài
        mock_task_response = MagicMock()
        mock_task_response.json.return_value = {
            "task_id": "task_mock_999",
            "prompt_template": "Hãy xác định tệp mục lục.",
            "resources": [{
                "file_path": "folder/muc_luc.pdf",
                "file_type": "pdf",
                "token": "dl_token_1"
            }]
        }
        mock_get.return_value = mock_task_response

        # Khởi tạo Provider với URL ảo
        provider = ProviderService(base_url="https://mock-server.local", api_key="fake-key")
        
        provider.create_session()
        task = provider.get_next_task()
        
        assert provider.session.session_id == "mock_session_123"
        assert task.task_id == "task_mock_999"
        print("\n[DataProvider] Mock Lấy Đề Bài thành công. Không có request thật nào được gửi đi.")

    # 2b. Mock lệnh POST (Nộp bài) -> Chống Submit nhầm!
    @patch('requests.post')
    def test_provider_submit_mock(self, mock_post):
        """Giả lập Nộp bài lên Server. Đảm bảo hàm submit_task được test an toàn."""
        # Giả lập Server trả về kết quả nộp bài thành công
        mock_submit_response = MagicMock()
        mock_submit_response.status_code = 200
        mock_submit_response.json.return_value = {
            "status": "success",
            "message": "Submission received",
            "score": 10
        }
        mock_post.return_value = mock_submit_response

        provider = ProviderService(base_url="https://mock-server.local", api_key="fake-key")
        # Chèn sẵn mock session để bypass hàm kiểm tra session_id
        provider.session = MagicMock()
        provider.session.session_id = "mock_session_123"

        # GỌI HÀM SUBMIT
        result = provider.submit_task(
            task_id="task_mock_999",
            answers=["Đáp án giả lập 1"],
            thought_log="Đây là dòng suy luận giả",
            used_tools=["MockTool"]
        )

        # Kiểm tra xem Provider có bắt và xử lý đúng file JSON server trả về không
        assert result["status"] == "success"
        assert result["score"] == 10
        
        # KIỂM SOÁT AN NINH: Đảm bảo Request gửi đi là URL ảo, không phải URL thật của BTC
        called_url = mock_post.call_args[0][0]
        assert "mock-server.local" in called_url, "CẢNH BÁO: URL gọi API bị sai hoặc lọt URL thật!"
        
        print(f"\n[DataProvider] Mock Nộp Bài thành công. Đã chặn API thật, kết quả giả lập: {result['score']} điểm.")