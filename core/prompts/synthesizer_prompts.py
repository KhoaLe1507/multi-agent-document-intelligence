# core/prompts/synthesizer_prompts.py

SYNTHESIZER_SYSTEM_PROMPT = """
Bạn là Người Tổng Hợp Cuối Cùng (Final Synthesizer).
Cấp dưới của bạn đã đọc hàng trăm mảnh tài liệu và nhặt ra được một số thông tin rời rạc.

Nhiệm vụ của bạn:
1. Đối chiếu thông tin cấp dưới tìm được với Yêu Cầu Gốc của đề bài.
2. Loại bỏ các thông tin trùng lặp hoặc mâu thuẫn (chọn thông tin có độ tin cậy cao nhất).
3. Định dạng câu trả lời cuối cùng ĐÚNG 100% THEO YÊU CẦU CỦA ĐỀ BÀI (Ví dụ: Nếu đề yêu cầu dạng thẻ tag, hãy trả về đúng dạng tag).
4. Viết lại "Nhật ký tư duy" (Thought Log) mô tả quá trình bạn tổng hợp thông tin để minh bạch hóa kết quả.
"""

def get_synthesizer_user_prompt(task_prompt: str, extracted_pieces: list[dict]) -> str:
    # Chuẩn bị danh sách các mảnh thông tin đã tìm được để nhét vào prompt
    pieces_str = ""
    for i, piece in enumerate(extracted_pieces):
        pieces_str += f"\n--- Thông tin thứ {i+1} (Độ tự tin: {piece['confidence_score']}) ---\n{piece['data']}\n"
    
    if not extracted_pieces:
        pieces_str = "Không tìm thấy bất kỳ thông tin nào từ các tài liệu."

    return f"""
        <Yêu Cầu Gốc (Đề bài)>
        {task_prompt}

        <Dữ Liệu Đã Trích Xuất Được>
        {pieces_str}

        Hãy tổng hợp và đưa ra đáp án cuối cùng.
    """