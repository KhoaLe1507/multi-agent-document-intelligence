# core/agents/planner.py
from .base_agent import BaseAgent
from ..config.settings import settings
from ..prompts.planner_prompts import PLANNER_SYSTEM_PROMPT, get_planner_user_prompt
from ..schemas.agent_outputs import PlannerResult

class PlannerAgent(BaseAgent):
    def __init__(self):
        super().__init__(agent_name="Planner", temperature=settings.TEMP_ROUTER) # Cần sự logic cao

    def create_extraction_plan(self, task_prompt: str) -> PlannerResult:
        user_prompt = get_planner_user_prompt(task_prompt)
        
        return self.call_llm(
            system_prompt=PLANNER_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            response_model=PlannerResult
        )