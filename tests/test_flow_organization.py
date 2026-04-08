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
        
        # 4. Keyword Extractor
        from core.agents.keyword_extractor import KeywordExtractorAgent
        kw_extractor = KeywordExtractorAgent()
        kw_result = kw_extractor.extract_keywords(chunks[0].content)
        assert len(kw_result.keywords) > 0
        
        keywords_str = ", ".join(kw_result.keywords)
        enhanced_file_list = [f"bang_tien_do.xlsx (Keywords: {keywords_str})"]
        
        # 5. Bước Agent 2: FileOrganizer (Phân loại vào Taxonomy)
        organizer = FileOrganizerAgent()
        org_result = organizer.organize_files("Phân loại theo quy định dự án", enhanced_file_list)
        
        assert len(org_result.thought_log) > 0
        print(f"\n✅ Luồng Organization OK. AI suy luận:\n{org_result.thought_log[:100]}...")