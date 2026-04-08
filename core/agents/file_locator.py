from .base_agent import BaseAgent
from ..config.settings import settings
from ..prompts.locator_prompts import LOCATOR_SYSTEM_PROMPT, get_locator_user_prompt
from ..schemas.agent_outputs import FileLocatorResult

class FileLocatorAgent(BaseAgent):
    def __init__(self):
        super().__init__(agent_name="FileLocator", temperature=0.0)

    def locate_files(self, task_prompt: str, document_summaries: str) -> FileLocatorResult:
        user_prompt = get_locator_user_prompt(task_prompt, document_summaries)
        
        return self.call_llm(
            system_prompt=LOCATOR_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            response_model=FileLocatorResult
        )

    def locate_files_advanced(self, content_blocks: list) -> FileLocatorResult:
        """Sử dụng mảng content_blocks để gửi trực tiếp cho LLM hỗ trợ Vision."""
        return self.call_llm(
            system_prompt=LOCATOR_SYSTEM_PROMPT,
            user_prompt=content_blocks,
            response_model=FileLocatorResult
        )
