# tests/test_agents.py
import pytest
from dotenv import load_dotenv

# Import các Agents từ hệ thống core của bạn
from core.agents.task_router import TaskRouterAgent
from core.agents.file_locator import FileLocatorAgent
from core.agents.file_organizer import FileOrganizerAgent

# Load biến môi trường (API Key) trước khi chạy test
load_dotenv()

class TestMultiAgents:
    
    # ---------------------------------------------------------
    # 1. TEST TASK ROUTER AGENT (Người Gác Cổng)
    # ---------------------------------------------------------
    def test_router_organize_flow(self):
        """Test xem Router có nhận diện đúng yêu cầu Sắp xếp thư mục không."""
        router = TaskRouterAgent()
        prompt = "Vui lòng phân loại các tài liệu được cung cấp vào đúng thư mục tương ứng."
        
        result = router.classify_task(prompt)
        
        # Kiểm tra kiểu dữ liệu trả về và kết quả phân loại
        assert result.task_type == "ORGANIZE", "Router nhận diện sai luồng ORGANIZE"
        print(f"\n[Router - Organize] Lý do: {result.reasoning}")

    def test_router_qa_flow(self):
        """Test xem Router có nhận diện đúng yêu cầu Trích xuất thông tin không."""
        router = TaskRouterAgent()
        prompt = "Hãy xác định bảng tiến độ thi công và đọc thời gian bắt đầu, kết thúc."
        
        result = router.classify_task(prompt)
        
        assert result.task_type == "QA", "Router nhận diện sai luồng QA"
        print(f"\n[Router - QA] Lý do: {result.reasoning}")

    # ---------------------------------------------------------
    # 2. TEST FILE LOCATOR AGENT (Đặc vụ Trinh Sát)
    # ---------------------------------------------------------
    def test_file_locator_accuracy(self):
        """Test xem Trinh sát có tìm đúng file Mục lục giữa một đống file rác không."""
        locator = FileLocatorAgent()
        
        task_prompt = "Hãy xác định tệp mục lục (Index) và kiểm tra cấu trúc tài liệu."
        document_summaries = """
        - File: ban_ve_tang_1.pdf | Nội dung: Bản vẽ thiết kế kỹ thuật thi công tầng 1...
        - File: muc_luc_du_an.pdf | Nội dung: 1. Giới thiệu dự án, 2. 目次・インデックス, 3. Các bên liên quan...
        - File: hoa_don_dien_nuoc.pdf | Nội dung: Hóa đơn thanh toán tiền điện tháng 10...
        """
        
        result = locator.locate_files(task_prompt, document_summaries)
        
        # Phải trả về đúng tên file mục lục
        assert "muc_luc_du_an.pdf" in result.target_file_names, "Trinh sát chọn sai file mục tiêu!"
        assert "hoa_don_dien_nuoc.pdf" not in result.target_file_names, "Trinh sát bị nhầm lẫn file rác!"
        print(f"\n[Locator] Target: {result.target_file_names} | Lý do: {result.reasoning}")

    # ---------------------------------------------------------
    # 3. TEST FILE ORGANIZER AGENT (Người Sắp Xếp)
    # ---------------------------------------------------------
    def test_file_organizer_taxonomy(self):
        """Test xem Agent Sắp xếp có tuân thủ đúng Taxonomy tiếng Nhật không."""
        organizer = FileOrganizerAgent()
        
        task_prompt = "Phân loại các bản vẽ thi công và hình ảnh công trường."
        file_list = [
            "ban_ve_thi_cong_mai_nha.pdf",
            "anh_chup_ngay_15_10.jpg"
        ]
        
        result = organizer.organize_files(task_prompt, file_list)
        
        # Đảm bảo Agent có sinh ra nhật ký tư duy
        assert result.thought_log is not None
        assert len(result.thought_log) > 20, "Nhật ký tư duy quá ngắn!"
        
        # Đảm bảo Agent sử dụng đúng tên thư mục từ VALID_FOLDERS
        assert "6. 竣工図面・施工図面" in result.thought_log, "Không phân loại đúng bản vẽ!"
        assert "19. 工事写真・写真帳" in result.thought_log, "Không phân loại đúng hình ảnh!"
        print(f"\n[Organizer] Thought Log:\n{result.thought_log}")