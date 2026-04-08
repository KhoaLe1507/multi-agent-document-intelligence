# core/agents/base_agent.py
from openai import OpenAI
from pydantic import BaseModel
from typing import Type, TypeVar, Optional, Any
from ..config.settings import settings
from ..utils.logger import agent_logger
from ..utils.retry import llm_retry
from ..exceptions.agent_errors import LLMCommunicationError

T = TypeVar('T', bound=BaseModel)

class BaseAgent:
    """Class nền tảng cung cấp khả năng tư duy cho mọi Agent con."""
    
    def __init__(self, agent_name: str, temperature: float):
        self.agent_name = agent_name
        self.client = OpenAI(
            api_key=settings.OPENAI_API_KEY      
        )
        self.model = settings.GPT_MODEL_NAME
        self.temperature = temperature

    @llm_retry() # Tự động thử lại nếu OpenAI quá tải hoặc sập mạng
    def call_llm(
        self, 
        system_prompt: str, 
        user_prompt: str, 
        response_model: Optional[Type[T]] = None
    ) -> T | str:
        """
        Gọi OpenAI API. 
        Nếu truyền response_model (Pydantic Class), nó sẽ trả về Object.
        Nếu không, nó trả về text thuần.
        """
        agent_logger.debug(f"[{self.agent_name}] Đang phân tích...")
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        try:
            if response_model:
                # Ép trả về JSON định dạng chuẩn (Structured Outputs)
                response = self.client.beta.chat.completions.parse(
                    model=self.model,
                    messages=messages,
                    response_format=response_model
                )
                agent_logger.success(f"[{self.agent_name}] Đã xuất dữ liệu chuẩn (Structured Output).")
                return response.choices[0].message.parsed
            else:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                )
                agent_logger.success(f"[{self.agent_name}] Đã sinh xong phản hồi text.")
                return response.choices[0].message.content
                
        except Exception as e:
            agent_logger.error(f"[{self.agent_name}] Thất bại sau nhiều lần thử: {str(e)}")
            raise LLMCommunicationError(f"Lỗi giao tiếp LLM tại {self.agent_name}: {str(e)}")