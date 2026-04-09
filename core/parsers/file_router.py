# core/parsers/file_router.py
from pathlib import Path
from ..utils.logger import agent_logger
from .table_extractor import extract_tables
from .vision_extractor import extract_vision_chunks
from ..schemas.data_types import DocumentChunk

def parse_file(file_path: str) -> list[DocumentChunk]:
    """
    Hệ thống định tuyến đa năng.
    Nhận vào file tải về từ DataProvider -> Trả về danh sách DocumentChunk chuẩn.
    """
    path = Path(file_path)
    agent_logger.info(f"Đang phân tích định dạng file: {path.name}")
    
    ext = path.suffix.lower()
    
    if ext in ['.xlsx', '.xls', '.csv']:
        return extract_tables(file_path)
        
    elif ext in ['.png', '.jpg', '.jpeg', '.gif', '.webp', '.tiff', '.tif']:
        return extract_vision_chunks(file_path)
        
    elif ext == '.pdf':
        # Lưu ý: Hiện tại đang ép toàn bộ PDF thành ảnh để giải quyết Prompt tiếng Nhật của bạn.
        # Nếu sau này có file Text thuần, bạn có thể gọi thư viện fitz.get_text() ở đây.
        return extract_vision_chunks(file_path)
        
    else:
        agent_logger.warning(f"Chưa hỗ trợ định dạng {ext} cho file {path.name}. Bỏ qua.")
        return []