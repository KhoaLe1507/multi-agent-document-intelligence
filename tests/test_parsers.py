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

def test_parse_text_formats(tmp_path):
    """Kiểm tra xử lý format văn bản (docx, txt)"""
    import docx
    
    # Tạo nội dung ảo cho .docx
    file_docx = tmp_path / "tailieu.docx"
    doc = docx.Document()
    doc.add_paragraph("Đây là dòng văn bản Word test.")
    doc.save(file_docx)
    
    chunks_docx = parse_file(str(file_docx))
    assert len(chunks_docx) == 1
    assert "Đây là dòng văn bản Word test" in chunks_docx[0].content
    assert chunks_docx[0].chunk_type == "text"
    
    # Tạo test cho .txt
    file_txt = tmp_path / "tailieu.txt"
    file_txt.write_text("Dữ liệu Text Test ảo", encoding="utf-8")
    
    chunks_txt = parse_file(str(file_txt))
    assert len(chunks_txt) == 1
    assert "Dữ liệu Text Test ảo" in chunks_txt[0].content

    # Tạo test cho .doc (dạng binary giả)
    file_doc = tmp_path / "tailieu.doc"
    # Ghi byte giả lập với một số chữ có nghĩa để test cơ chế fallback raw-text
    file_doc.write_bytes(b"\x00\x01\x02Fallback_word\x04\x05 \xFF \xFE text")
    
    chunks_doc = parse_file(str(file_doc))
    assert len(chunks_doc) == 1
    assert "Fallback_word" in chunks_doc[0].content
    assert "text" in chunks_doc[0].content

def test_parse_unsupported_format(tmp_path):
    """Kiểm tra xử lý format lạ (VD: .psd)"""
    file_path = tmp_path / "tailieu.psd"
    file_path.write_text("Dữ liệu rác ảo", encoding="utf-8")
    
    # Theo thiết kế ở file_router, định dạng không hỗ trợ trả về list []
    chunks = parse_file(str(file_path))
    assert len(chunks) == 0, "Không hỗ trợ thì phải skip và trả về rỗng"
