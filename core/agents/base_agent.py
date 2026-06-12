# core/agents/base_agent.py
from openai import OpenAI
from pydantic import BaseModel
from typing import Type, TypeVar, Optional, Any
from ..config.settings import settings
from ..utils.logger import agent_logger
from ..utils.retry import llm_retry
from ..exceptions.agent_errors import LLMCommunicationError
from ..utils.trace_logger import tracer

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
        user_prompt: str | list, 
        response_model: Optional[Type[T]] = None,
        image_base64: Optional[str] = None
    ) -> T | str:
        """
        Gọi OpenAI API. 
        Nếu có image_base64, nó sẽ được gửi dưới dạng Vision content block.
        Nếu user_prompt là list, nó sẽ truyền thô mảng content block đó (hỗ trợ gom nhóm text và ảnh).
        """
        agent_logger.debug(f"[{self.agent_name}] Đang phân tích...")
        
        if isinstance(user_prompt, str):
            user_content = []
            user_content.append({"type": "text", "text": user_prompt})
            
            if image_base64:
                    user_content.append({
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{image_base64}",
                            "detail": "high" # Đảm bảo độ phân giải tốt nhất cho OCR
                        }
                    })
        else:
            user_content = user_prompt
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
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
                parsed_res = response.choices[0].message.parsed
                tracer.add_agent_span(
                    agent_name=self.agent_name,
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    response=parsed_res
                )
                return parsed_res
            else:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                )
                agent_logger.success(f"[{self.agent_name}] Đã sinh xong phản hồi text.")
                text_res = response.choices[0].message.content
                tracer.add_agent_span(
                    agent_name=self.agent_name,
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    response=text_res
                )
                return text_res
                
        except Exception as e:
            agent_logger.error(f"[{self.agent_name}] Thất bại sau nhiều lần thử: {str(e)}")
            raise LLMCommunicationError(f"Lỗi giao tiếp LLM tại {self.agent_name}: {str(e)}")