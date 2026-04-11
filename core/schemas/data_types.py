# core/schemas/data_types.py
from pydantic import BaseModel, Field
from typing import Literal, Optional

class DocumentChunk(BaseModel):
    """
    Đại diện cho 1 mảnh tài liệu đã được băm nhỏ (1 Ảnh, 1 Sheet Excel, hoặc 1 Đoạn Text).
    Đây là "vật liệu" sẽ được nạp cho Extractor Agent.
    """
    chunk_type: Literal["text", "image", "table"]
    content: str = Field(..., description="Nội dung Text, Markdown Table, hoặc Base64 Image")
    file_name: str
    page_number: Optional[int] = None
    
    def get_context_description(self) -> str:
        """Utility function to help the Agent understand what it is reading."""
        loc = f"Page {self.page_number}" if self.page_number else "Entire file"
        return f"[Document: {self.file_name} | Location: {loc} | Format: {self.chunk_type}]"

class TaskContext(BaseModel):
    """
    Lưu trữ ngữ cảnh của toàn bộ Task hiện tại. 
    Tránh việc truyền quá nhiều tham số lẻ tẻ vào các hàm.
    """
    task_id: str
    original_prompt: str
    chunks: list[DocumentChunk] = []