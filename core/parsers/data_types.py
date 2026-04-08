# core/schemas/data_types.py
from pydantic import BaseModel
from typing import Literal, Optional

class DocumentChunk(BaseModel):
    """Một mảnh dữ liệu đã được cắt gọt để nạp vào AI."""
    chunk_type: Literal["text", "image", "table"]
    content: str  # Chứa Text, Markdown hoặc chuỗi Base64 của ảnh
    file_name: str
    page_number: Optional[int] = None
    
    # Metadata giúp Agent hiểu ngữ cảnh (VD: "Đây là bảng biểu trang 3")
    def get_context_description(self) -> str:
        loc = f"Trang {self.page_number}" if self.page_number else "Toàn bộ file"
        return f"[File: {self.file_name} | Vị trí: {loc} | Loại hình: {self.chunk_type}]"
    