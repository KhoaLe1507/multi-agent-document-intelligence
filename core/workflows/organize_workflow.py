# core/workflows/organize_workflow.py
from dataProvider import ProviderService
from ..utils.logger import agent_logger
from ..agents.file_organizer import FileOrganizerAgent

class OrganizeWorkflow:
    def __init__(self, provider: ProviderService):
        self.provider = provider
        self.organizer = FileOrganizerAgent()

    def execute(self, task):
        agent_logger.info("📁 Bắt đầu luồng File Organization...")
        
        # Lấy danh sách tên file
        file_names = [res.file_path.split('/')[-1] for res in task.resources]
        
        # Gọi Agent để lấy Thought Log
        agent_logger.info("🧠 Đang suy luận cách phân bổ thư mục...")
        result = self.organizer.organize_files(task.prompt_template, file_names)
        
        # Nộp bài (answers rỗng theo quy định)
        submit_response = self.provider.submit_task(
            task_id=task.task_id,
            answers=[],  
            thought_log=result.thought_log,
            used_tools=["FileOrganizer"]
        )
        agent_logger.info(f"📤 Đã nộp bài Organize! Server: {submit_response}")

