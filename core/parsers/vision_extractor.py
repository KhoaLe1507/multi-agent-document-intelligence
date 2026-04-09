# core/parsers/vision_extractor.py
import base64
import fitz  # PyMuPDF
from PIL import Image
import io
from pathlib import Path
from ..utils.logger import agent_logger
from ..exceptions.agent_errors import ParsingError
from ..schemas.data_types import DocumentChunk

def encode_image_to_base64(image: Image.Image, max_size: int = 1500) -> str:
    """Nén ảnh nếu quá lớn và chuyển thành Base64."""
    # Resize giữ nguyên tỷ lệ nếu ảnh to hơn max_size
    if max(image.size) > max_size:
        image.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
    
    # Chuyển sang RGB (bỏ Alpha channel nếu là PNG) để nén JPEG cho nhẹ
    if image.mode in ("RGBA", "P"):
        image = image.convert("RGB")
        
    buffered = io.BytesIO()
    image.save(buffered, format="JPEG", quality=85)
    return base64.b64encode(buffered.getvalue()).decode('utf-8')

def extract_vision_chunks(file_path: str) -> list[DocumentChunk]:
    path = Path(file_path)
    chunks = []
    
    try:
        # 1. Nếu là file ảnh trực tiếp
        if path.suffix.lower() in ['.png', '.jpg', '.jpeg']:
            img = Image.open(file_path)
            b64_str = encode_image_to_base64(img)
            chunks.append(DocumentChunk(
                chunk_type="image", content=b64_str, file_name=path.name, page_number=1
            ))
            agent_logger.success(f"Đã mã hóa ảnh {path.name}.")
            
        # 2. Nếu là file PDF, cắt từng trang thành ảnh
        elif path.suffix.lower() == '.pdf':
            doc = fitz.open(file_path)
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                # Tăng DPI lên chút để OCR chính xác hơn (zoom=2 là đủ sắc nét)
                pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                
                b64_str = encode_image_to_base64(img)
                chunks.append(DocumentChunk(
                    chunk_type="image", content=b64_str, file_name=path.name, page_number=page_num + 1
                ))
            doc.close()
            agent_logger.success(f"Đã cắt {path.name} thành {len(chunks)} ảnh Base64.")
            
        return chunks
        
    except Exception as e:
        agent_logger.error(f"Lỗi xử lý hình ảnh {path.name}: {e}")
        raise ParsingError(f"Không thể xử lý ảnh/PDF: {str(e)}")