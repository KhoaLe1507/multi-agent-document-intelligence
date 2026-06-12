from core.agents.file_organizer import FileOrganizerAgent
from core.agents.task_router import TaskRouterAgent
from core.parsers.file_router import parse_file


class TestOrganizationFlow:
    def test_full_org_flow(self):
        task_file = "tests/sample_data/bang_tien_do.xlsx"
        chunks = parse_file(task_file)

        router = TaskRouterAgent()
        route_result = router.classify_task("Hay phan loai tep nay vao dung thu muc ky thuat.")

        assert route_result.task_type == "ORGANIZE"

        from core.agents.keyword_extractor import KeywordExtractorAgent

        kw_extractor = KeywordExtractorAgent()
        kw_result = kw_extractor.extract_keywords(chunks[0].content)
        assert len(kw_result.keywords) > 0

        keywords_str = ", ".join(kw_result.keywords)
        enhanced_file_list = [f"bang_tien_do.xlsx (Keywords: {keywords_str})"]

        organizer = FileOrganizerAgent()
        org_result = organizer.organize_files("Phan loai theo quy dinh du an", enhanced_file_list)

        assert len(org_result.thought_log) > 0
