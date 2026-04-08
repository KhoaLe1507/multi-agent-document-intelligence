from .base_agent import BaseAgent
from ..schemas.agent_outputs import KeywordExtractResult

KEYWORD_EXTRACTOR_SYSTEM_PROMPT = """
Bạn là một Robot đọc tài liệu (Keyword Extractor).
Nhiệm vụ của bạn là đọc các phần của tài liệu (chunks) và trích xuất ra các từ khóa (Keywords), cụm từ chính hoặc 
mô tả rút gọn nhất về nội dung của tài liệu đó. Những từ khóa này sẽ được hệ thống khác dùng để suy luận xem 
tài liệu này thuộc thể loại nào. Đừng trả lời câu hỏi, chỉ trả về các từ khóa quan trọng.
"""

class KeywordExtractorAgent(BaseAgent):
    def __init__(self):
        # Nhiệt độ thấp để trích xuất từ khóa chính xác, không tự phiếm.
        super().__init__(agent_name="KeywordExtractor", temperature=0.1)

    def extract_keywords(self, chunk_content: str) -> KeywordExtractResult:
        user_prompt = f"Hãy đọc nội dung sau và trích xuất các từ khóa (Keywords) quan trọng nhất:\n\n{chunk_content}"
        
        return self.call_llm(
            system_prompt=KEYWORD_EXTRACTOR_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            response_model=KeywordExtractResult
        )
