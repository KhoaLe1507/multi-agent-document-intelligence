# core/schemas/agent_outputs.py
from pydantic import BaseModel, Field
from typing import List, Literal, Optional

class TaskRoutingResult(BaseModel):
    """Output của TaskRouterAgent: Xác định rẽ nhánh pipeline."""
    task_type: Literal["QA", "ORGANIZE"] = Field(
        ..., 
        description="Nếu yêu cầu là sắp xếp/di chuyển file, chọn ORGANIZE. Nếu là trích xuất thông tin/trả lời câu hỏi, chọn QA."
    )
    reasoning: str = Field(
        ..., 
        description="Giải thích ngắn gọn lý do tại sao lại phân loại task này vào nhóm trên."
    )

class PlannerResult(BaseModel):
    """Output của PlannerAgent: Kế hoạch tác chiến cho đàn em."""
    extraction_guidelines: str = Field(
        ..., 
        description="Hướng dẫn chi tiết, từng bước một để Extractor Agent biết cách tìm kiếm thông tin trong tài liệu."
    )
    target_keywords: List[str] = Field(
        ..., 
        description="Danh sách các từ khóa hoặc mẫu (pattern) cần đặc biệt chú ý."
    )

class ExtractionResult(BaseModel):
    """Output của ExtractorAgent (Công nhân): Kết quả cào dữ liệu từ 1 chunk."""
    found_information: bool = Field(
        ..., 
        description="True nếu tìm thấy thông tin hữu ích đáp ứng được yêu cầu của đề bài, False nếu chunk này không chứa thông tin liên quan."
    )
    extracted_data: Optional[str] = Field(
        None, 
        description="Dữ liệu trích xuất được. Giữ nguyên định dạng gốc nếu có thể. Trả về null nếu found_information là False."
    )
    confidence_score: float = Field(
        ..., 
        description="Độ tự tin của Agent vào thông tin trích xuất được, thang điểm từ 0.0 đến 1.0."
    )

class SynthesisResult(BaseModel):
    """Output của SynthesizerAgent: Chốt hạ kết quả cuối cùng để Submit."""
    final_answers: List[str] = Field(
        ..., 
        description="Danh sách các câu trả lời cuối cùng, đúng định dạng yêu cầu của hệ thống (ví dụ: dạng tag)."
    )
    thought_log: str = Field(
        ..., 
        description="Nhật ký tư duy: AI đã phân tích tài liệu như thế nào để đưa ra đáp án này? (Dùng để BTC chấm điểm minh bạch)."
    )

class OrganizeResult(BaseModel):
    """Output của FileOrganizerAgent: Trọng tâm là thought_log để BTC chấm điểm."""
    thought_log: str = Field(
        ..., 
        description="Toàn bộ quá trình suy luận và danh sách phân bổ file vào các thư mục. (Ví dụ: 'Dựa vào yêu cầu, tôi phân loại file A vào thư mục X vì...')"
    )

class FileLocatorResult(BaseModel):
    """Output của FileLocatorAgent: Nhận diện đúng file cần xử lý."""
    target_file_names: list[str] = Field(
        ..., 
        description="Danh sách tên các file (file_name) khớp với yêu cầu tìm kiếm của đề bài. Trả về mảng rỗng nếu không có file nào khớp."
    )
    reasoning: str = Field(
        ..., 
        description="Giải thích lý do tại sao lại chọn (các) file này."
    )