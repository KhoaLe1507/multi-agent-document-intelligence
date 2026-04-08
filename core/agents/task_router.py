# core/agents/task_router.py
from .base_agent import BaseAgent
from ..config.settings import settings
from ..prompts.router_prompts import ROUTER_SYSTEM_PROMPT, get_router_user_prompt
from ..schemas.agent_outputs import TaskRoutingResult

class TaskRouterAgent(BaseAgent):
    def __init__(self):
        # Nhiệt độ 0.0 để kết quả luôn ổn định và logic nhất
        super().__init__(agent_name="TaskRouter", temperature=settings.TEMP_ROUTER)

    def classify_task(self, task_prompt: str) -> TaskRoutingResult:
        user_prompt = get_router_user_prompt(task_prompt)
        
        return self.call_llm(
            system_prompt=ROUTER_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            response_model=TaskRoutingResult
        )