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
            f"🎯 **YÊU CẦU ĐỀ BÀI (Task):**\n{prompt_template}\n\n"
            f"📝 **NHẬT KÝ TƯ DUY HIỆN TẠI (Thought Log):**\n{thought_log}\n\n"
            f"✅ **ĐÁP ÁN DỰ KIẾN (Draft Answers):**\n{answers}\n\n"
            "Hãy đánh giá xem bản nháp này đã thỏa mãn tuyệt đối yêu cầu đề bài chưa. Có thông tin nào bịa đặt, suy luận sai hoặc thiếu sót không?"
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
            f"🎯 **YÊU CẦU ĐỀ BÀI (Task):**\n{prompt_template}\n\n"
            f"📝 **NHẬT KÝ PHÂN LỘ (Thought Log):**\n{thought_log}\n\n"
            "Hãy kiểm tra xem các file đã được phân loại vào đúng thư mục yêu cầu chưa. Lý do tổ chức file có hợp logic không?"
        )
        
        agent_logger.info("⚖️ [Reviewer] Đang thẩm định kết quả Organize...")
        return self.call_llm(
            system_prompt=self.system_prompt,
            user_prompt=user_prompt, 
            response_model=ReviewResult
        )
