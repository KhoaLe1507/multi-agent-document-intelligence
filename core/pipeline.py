# core/pipeline.py
from dataProvider import ProviderService
from .utils.logger import agent_logger
from .agents.task_router import TaskRouterAgent
from .utils.trace_logger import tracer

# Import các Workflow đã tách
from .workflows.qa_workflow import QAWorkflow
from .workflows.organize_workflow import OrganizeWorkflow

class SystemPipeline:
    def __init__(self, provider: ProviderService):
        self.provider = provider
        self.router = TaskRouterAgent()
        
        # Khởi tạo các cỗ máy xử lý luồng
        self.qa_workflow = QAWorkflow(provider)
        self.organize_workflow = OrganizeWorkflow(provider)

    def run_continuous(self):
        agent_logger.info("Bắt đầu vòng lặp thi đấu tự động!")
        while True:
            try:
                self.process_single_task()
            except Exception as e:
                agent_logger.critical(f"Lỗi nghiêm trọng: {e}")
                break

    def process_single_task(self):
        # 1. Lấy đề bài
        agent_logger.info("-" * 50)
        task = self.provider.get_next_task()
        agent_logger.info(f"Đã nhận Task: {task.task_id}")
        tracer.start_task(task.task_id, task.prompt_template, task.resources)

        # 2. Định tuyến Task
        routing_result = self.router.classify_task(task.prompt_template)
        tracer.set_task_type(routing_result.task_type)
        agent_logger.info(f"Rẽ nhánh: {routing_result.task_type} ({routing_result.reasoning})")

        # 3. Phân phối cho Workflow xử lý
        if routing_result.task_type == "ORGANIZE":
            self.organize_workflow.execute(task)
        else:
            self.qa_workflow.execute(task)
            
        tracer.end_task()