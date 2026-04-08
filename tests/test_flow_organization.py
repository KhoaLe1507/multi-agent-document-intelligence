import pytest
from unittest.mock import patch, MagicMock
from dataProvider import ProviderService
from core.parsers.file_router import parse_file
from core.agents.task_router import TaskRouterAgent
from core.agents.file_organizer import FileOrganizerAgent

class TestOrganizationFlow:

    @patch('requests.get')
    @patch('requests.post')
    def test_full_org_flow(self, mock_post, mock_get):
        # 1. Giả lập dữ liệu từ DataProvider (Mẫu 5 của BTC)
        mock_get.return_value.json.return_value = {
            "task_id": "test_org_001",
            "prompt_template": "Hãy phân loại tệp này vào đúng thư mục kỹ thuật.",
            "resources": [{"file_path": "tests/sample_data/bang_tien_do.xlsx", "file_type": "excel", "token": "abc"}]
        }
        
        # 2. Bước Data Pipeline: Tải và Parse
        # (Ở đây ta dùng file local trong sample_data để thay cho việc download thật)
        task_file = "tests/sample_data/bang_tien_do.xlsx"
        chunks = parse_file(task_file)
        
        # 3. Bước Agent 1: TaskRouter (Quyết định luồng)
        router = TaskRouterAgent()
        route_result = router.classify_task("Hãy phân loại tệp này vào đúng thư mục kỹ thuật.")
        
        assert route_result.task_type == "ORGANIZE"
        
        # 4. Bước Agent 2: FileOrganizer (Phân loại vào Taxonomy)
        organizer = FileOrganizerAgent()
        # Lấy chunk đầu tiên của Excel để phân loại
        org_result = organizer.organize_files(chunks, "Phân loại theo quy định dự án")
        
        assert len(org_result.assignments) > 0
        print(f"\n✅ Luồng Organization OK. File được xếp vào: {org_result.assignments[0].folder_name}")