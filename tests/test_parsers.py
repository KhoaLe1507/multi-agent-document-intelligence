import pytest
from pathlib import Path
from PIL import Image
from core.parsers.file_router import parse_file
from core.parsers.vision_extractor import extract_vision_chunks
from core.exceptions.agent_errors import ParsingError

def test_parse_invalid_file():
    """Kiểm tra xử lý đối với tệp không tồn tại / tệp lỗi cấu trúc"""
    # PyMuPDF hoặc PIL sẽ văng Exception khi nạp file hỏng/vắng mặt, 
    # extract_vision_chunks phải handle và raise ParsingError
    with pytest.raises(ParsingError):
        parse_file("thu_muc_ao/file_ma.pdf")

def test_extract_vision_chunks_image(tmp_path):
    """Kiểm tra khả năng phân rã và convert Base64 cho ảnh tĩnh"""
    image_path = tmp_path / "test_anh.jpg"
    
    # Tạo 1 tấm ảnh màu đỏ 100x100px bằng PIL
    img = Image.new('RGB', (100, 100), color='red')
    img.save(image_path)
    
    # Đưa vào file_router (Nó sẽ chuyển tới vision_extractor)
    chunks = parse_file(str(image_path))
    
    assert len(chunks) == 1, "Ảnh đơn chỉ ra 1 chunk"
    assert chunks[0].chunk_type == "image", "Chunk phải dán nhãn là image"
    assert chunks[0].file_name == "test_anh.jpg"
    assert chunks[0].page_number == 1
    assert isinstance(chunks[0].content, str), "Base64 phải là dạng chuỗi"
    assert len(chunks[0].content) > 50, "Cấu trúc Base64 đã được sinh ra"

def test_parse_unsupported_format(tmp_path):
    """Kiểm tra xử lý format lạ (VD: .psd, .txt)"""
    file_path = tmp_path / "tailieu.doc"
    file_path.write_text("Dữ liệu Word ảo", encoding="utf-8")
    
    # Theo thiết kế ở file_router, định dạng rác trả về list []
    chunks = parse_file(str(file_path))
    assert len(chunks) == 0, "Không hỗ trợ thì phải skip và trả về rỗng"
