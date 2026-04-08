LOCATOR_SYSTEM_PROMPT = """
Bạn là một Đặc vụ Trinh sát Tài liệu (Document Locator).
Nhiệm vụ của bạn là đọc yêu cầu của người dùng (thường bắt đầu bằng "Hãy xác định tập tin..."), sau đó xem xét danh sách các tài liệu hiện có và CHỈ RA CHÍNH XÁC tài liệu nào cần được xử lý.

QUY TẮC:
- Hãy dựa vào ngữ cảnh, tiêu đề, hoặc đoạn nội dung đầu tiên của tài liệu để đưa ra quyết định.
- Chỉ trả về tên file thực sự liên quan. Loại bỏ hoàn toàn các file rác.
"""

def get_locator_user_prompt(task_prompt: str, document_summaries: str) -> str:
    return f"""
<Yêu cầu của Đề bài>
{task_prompt}

<Danh sách Tài liệu và Nội dung tóm tắt>
{document_summaries}

Hãy xác định những file nào cần thiết để giải quyết yêu cầu trên.
"""