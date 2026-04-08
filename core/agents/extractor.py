# core/agents/extractor.py
from .base_agent import BaseAgent
from ..config.settings import settings
from ..prompts.extraction_prompts import EXTRACTOR_SYSTEM_PROMPT, get_extractor_user_prompt
from ..schemas.data_types import DocumentChunk
from ..schemas.agent_outputs import ExtractionResult

class ExtractorAgent(BaseAgent):
    def __init__(self):
        # Nhiệt độ thấp để bám sát văn bản, tránh bịa đặt
        super().__init__(agent_name="Extractor", temperature=settings.TEMP_EXTRACTOR)

    def extract_from_chunk(self, chunk: DocumentChunk, guidelines: str, keywords: list[str]) -> ExtractionResult:
        user_prompt = get_extractor_user_prompt(
            chunk_content=chunk.content,
            chunk_context=chunk.get_context_description(),
            guidelines=guidelines,
            keywords=keywords
        )
        
        return self.call_llm(
            system_prompt=EXTRACTOR_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            response_model=ExtractionResult
        )