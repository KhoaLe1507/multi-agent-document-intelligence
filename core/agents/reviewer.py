# core/agents/reviewer.py
from typing import List, Dict, Any, Optional
from .base_agent import BaseAgent
from ..schemas.agent_outputs import ReviewResult
from ..utils.logger import agent_logger
from ..prompts.reviewer_prompts import REVIEW_QA_SYSTEM, REVIEW_ORG_SYSTEM

class ReviewerAgent(BaseAgent):
    def __init__(self):
        # Reviewer cần độ lạnh lùng, nghiêm khắc để đánh giá logic
        super().__init__(agent_name="Reviewer", temperature=0.1)

    def review_qa(self, prompt_template: str, answers: List[str], thought_log: str) -> ReviewResult:
        """Đánh giá kết quả của luồng hỏi đáp (QA)"""
        self.system_prompt = REVIEW_QA_SYSTEM
        
        user_prompt = (
            f"🎯 **TASK INSTRUCTION:**\n{prompt_template}\n\n"
            f"📝 **CURRENT THOUGHT LOG:**\n{thought_log}\n\n"
            f"✅ **DRAFT ANSWERS:**\n{answers}\n\n"
            "Evaluate whether this draft perfectly satisfies the task instruction. Is there any fabricated information, faulty reasoning, or missing data?"
        )
        
        agent_logger.info("⚖️ [Reviewer] Đang thẩm định kết quả QA...")
        return self.call_llm(
            system_prompt=self.system_prompt,
            user_prompt=user_prompt, 
            response_model=ReviewResult
        )

    def review_organize(self, prompt_template: str, thought_log: str) -> ReviewResult:
        """Đánh giá kết quả phân loại file (Organization)"""
        self.system_prompt = REVIEW_ORG_SYSTEM
        
        user_prompt = (
            f"🎯 **TASK INSTRUCTION:**\n{prompt_template}\n\n"
            f"📝 **CLASSIFICATION THOUGHT LOG:**\n{thought_log}\n\n"
            "Verify that the files have been classified into the correct folders. Is the reasoning behind the file organization logical?"
        )
        
        agent_logger.info("⚖️ [Reviewer] Đang thẩm định kết quả Organize...")
        return self.call_llm(
            system_prompt=self.system_prompt,
            user_prompt=user_prompt, 
            response_model=ReviewResult
        )
