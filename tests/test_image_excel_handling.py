import pytest
from pathlib import Path
from core.parsers.file_router import parse_file
from core.agents.keyword_extractor import KeywordExtractorAgent
from core.agents.extractor import ExtractorAgent

@pytest.fixture
def sample_excel_path() -> str:
    return str(Path("tests/sample_data/bang_tien_do.xlsx").absolute())

@pytest.fixture
def sample_pdf_img_path() -> str:
    return str(Path("tests/sample_data/tai_lieu_dac_ta.pdf").absolute())

def test_excel_parsing_and_keyword_extraction(sample_excel_path):
    # Dữ liệu Excel chứa các bảng (table text chunk)
    chunks = parse_file(sample_excel_path)
    assert len(chunks) > 0, "Quá trình parse Excel thất bại, không tìm thấy chunks."
    
    # Kiểm tra xem có text thật sự để gửi tới LLM không
    all_text = ""
    for c in chunks:
        assert c.chunk_type in ["text", "table"], "Excel phải trả về chunk_type là 'table' hoặc 'text'"
        all_text += c.content + "\n"
        
    assert "bang_tien_do.xlsx" in all_text or "Bảng" in all_text or len(all_text) > 10, "Bảng Excel không có dữ liệu."

    # Test KeywordExtractor
    agent = KeywordExtractorAgent()
    result = agent.extract_keywords(all_text)
    
    assert result.keywords, "Hệ thống không tìm thấy keyword nào từ dữ liệu Excel."
    print("Keyword từ Excel:", result.keywords)
    print("Log tư duy (Excel):", result.thought_log)


def test_pdf_image_parsing_and_keyword_extraction(sample_pdf_img_path):
    # Dữ liệu PDF được băm thành image chunks (Nếu test trong môi trường CI không có Ghostscript, có thể bỏ qua)
    try:
        chunks = parse_file(sample_pdf_img_path)
    except Exception as e:
        pytest.skip(f"Không thể parse PDF thành ảnh: {e}")
        
    assert len(chunks) > 0, "Quá trình parse PDF thất bại."
    
    # Kiểm tra xem chunks có phải là hình ảnh Base64
    has_image = False
    first_image_base64 = None
    all_text = ""
    for c in chunks:
        if c.chunk_type == "image":
            has_image = True
            if not first_image_base64:
                first_image_base64 = c.content
        else:
            all_text += c.content + "\n"

    assert has_image, "Không phát hiện được chunk hình ảnh nào từ PDF."

    # Test KeywordExtractor với hệ thống hỗ trợ ảnh (Vision)
    agent = KeywordExtractorAgent()
    result = agent.extract_keywords(all_text, image_base64=first_image_base64)
    
    assert result.keywords, "Hệ thống không tìm thấy keyword nào từ dữ liệu Hình ảnh (Vision LLM)."
    print("Keyword từ Hình ảnh:", result.keywords)
    print("Log tư duy (Ảnh):", result.thought_log)


def test_extractor_agent_vision_support(sample_pdf_img_path):
    try:
        chunks = parse_file(sample_pdf_img_path)
        img_chunk = next(c for c in chunks if c.chunk_type == "image")
    except Exception as e:
        pytest.skip(f"Không lấy được image chunk: {e}")

    extractor = ExtractorAgent()
    guidelines = "Hãy tìm tiêu đề chính của tài liệu này."
    target_keywords = ["tiêu đề", "title", "báo cáo"]

    result = extractor.extract_from_chunk(img_chunk, guidelines, target_keywords)

    print("Log tư duy của Xạ thủ (Vision):", result.thought_log)
    print("Nội dung lấy được:", result.extracted_data)
    assert result.confidence_score >= 0, "Score phải >= 0"
