# core/agents/synthesizer.py
from .base_agent import BaseAgent
from ..config.settings import settings
from ..prompts.synthesizer_prompts import SYNTHESIZER_SYSTEM_PROMPT, get_synthesizer_user_prompt
from ..schemas.agent_outputs import SynthesisResult

class SynthesizerAgent(BaseAgent):
    def __init__(self):
        # Nhiệt độ hơi nhích lên một chút để có thể viết văn bản / thought log mượt mà
        super().__init__(agent_name="Synthesizer", temperature=settings.TEMP_SYNTHESIZER)

    def synthesize_final_answer(self, task_prompt: str, extracted_pieces: list[dict]) -> SynthesisResult:
        user_prompt = get_synthesizer_user_prompt(task_prompt, extracted_pieces)
        
        return self.call_llm(
            system_prompt=SYNTHESIZER_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            response_model=SynthesisResult
        )