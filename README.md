# 🌟 Hệ Thống OCR Multi-Agents (AI Automation)

Dự án này là một hệ thống **Multi-Agents tự động** chuyên dụng cho các nhiệm vụ trích xuất dữ liệu, hỏi đáp (QA) trên tài liệu phức tạp (bao gồm OCR/Vision cho file PDF, Hình ảnh, Excel) và phân loại dữ liệu (Data Organization). Hệ thống dựa trên kiến trúc của OpenAI Chat Completions với Pydantic Structured Outputs để luồng dữ liệu chuẩn xác, thiết kế pipeline dạng module để dễ dàng tích hợp và tinh chỉnh.

---

## 🏗 Mô tả Hệ Thống Kiến Trúc

Hệ thống hoạt động như một cỗ máy tự vận hành thay vì một script đơn lẻ thông thường. 
- **DataProvider** đóng vai trò là cầu nối với hệ thống hoặc API máy chủ (lấy Task, tải xuống File và Nộp kết quả). 
- **SystemPipeline** thiết lập nhịp điệu tự động, liên tục lắng nghe và phân phối nhiệm vụ (Tasks).
- **Core Agents** là các bộ não riêng biệt, mỗi "Agent" chuyên biệt hóa cho một nhiệm vụ cụ thể và hỗ trợ lẫn nhau trong WorkFlow chung.

### Sơ đồ tương tác tổng quan:
`Server/API` 🔄 **DataProvider** ➡️ **SystemPipeline** ➡️ **Workflow (QA / ORGANIZE)** ➡️ `Báo cáo lại Server`

---

## 🌊 Các Luồng Hoạt Động (Data Flow & Pipeline)

Hệ thống xoay quanh hai (02) Workflow chính, được điều phối bởi **SystemPipeline** sau khi **TaskRouterAgent** phân loại đề bài.

### 1. Luồng Phân Loại Dữ Liệu (Organization Workflow)
*Mục tiêu: Đọc nội dung file và sắp xếp file vào đúng Taxonomy (thư mục) yêu cầu.*

1. **Tải & Parse:** Tải file về và sử dụng bộ Parse (PDF/Excel) để băm nhỏ file thành các Chunks.
2. **Trích xuất Đặc trưng (Keyword Extraction):** `KeywordExtractorAgent` đọc nội dung các chunks để rút ra các từ khóa (Keywords) và ý chính mô tả file.
3. **Phân loại Thông minh:** `FileOrganizerAgent` nhận vào danh sách file kèm theo bộ Keywords vừa trích xuất. Dựa vào yêu cầu (Prompt) và Keywords nội dung, Agent thực hiện phân bổ file vào đúng thư mục hợp lệ.
4. **Nộp bài:** Gửi báo cáo suy luận (Thought Log) về **DataProvider**.

### 2. Luồng Hỏi Đáp & Trích Xuất (Question Answering - QA Workflow)
*Mục tiêu: Tìm chính xác file chứa thông tin và trích xuất đáp án cuối cùng.*

1. **Tải & Parse:** Tải file và băm nhỏ thành `DocumentChunk`.
2. **Trinh sát Vòng lặp (Iterative File Locator):** 
   - `FileLocatorAgent` đọc nội dung trang đầu tiên của các file.
   - **Cơ chế đặc biệt:** Nếu Agent cảm thấy thông tin ở trang 1 chưa đủ (ví dụ trang bìa, mục lục), nó sẽ báo hiệu `requires_more_info = True`.
   - Hệ thống tự động nạp trang (chunk) kế tiếp và hỏi lại Agent cho đến khi danh sách file mục tiêu được xác định chắc chắn.
3. **Lên Kế Hoạch (QA Hint/Planner):** `PlannerAgent` tạo ra các Hint và vị trí chunks cần thiết giúp OCR Agent làm việc cẩn thận nhất.
4. **Xạ Thủ Trích Xuất (QA OCR Agent):** `ExtractorAgent` xử lý chi tiết từng chunk/ảnh được chỉ định để lấy dữ liệu thô.
5. **Tổng Hợp (QA Agent):** `SynthesizerAgent` gom các mảnh dữ liệu lại, trả lời câu hỏi của đề bài một cách logic nhất.
6. **Nộp bài:** Đẩy kết quả cuối cùng về **DataProvider**.

---

## 🤖 Các Agents Trong Hệ Thống

Tất cả các Agent đều kế thừa từ `BaseAgent` (hỗ trợ logic thử lại `llm_retry` và Structured Outputs).

1. **`TaskRouterAgent`**: Công cụ định tuyến nhiệm vụ (QA vs Organize).
2. **`KeywordExtractorAgent`**: Robot đọc lướt, rút trích từ khóa chính từ các chunks nội dung.
3. **`FileOrganizerAgent`**: Chuyên gia quản lý thư mục, phân loại file dựa trên nội dung tóm tắt.
4. **`FileLocatorAgent`**: Trinh sát viên, có khả năng yêu cầu nạp thêm dữ liệu (trang kế tiếp) nếu chưa chắc chắn.
5. **`PlannerAgent`**: Chiến lược gia, đưa ra các hint và chỉ dẫn OCR chi tiết.
6. **`ExtractorAgent`**: Công nhân OCR, soi chi tiết từng chunk dữ liệu.
7. **`SynthesizerAgent`**: Người tổng hợp kết quả và viết báo cáo cuối cùng.

---

## ⚙️ Cách Điều Chỉnh Agent (Agent Tuning)

Hệ thống được thiết kế để dễ dàng thay đổi hành vi AI mà không cần sửa cấu trúc code chính:

### 1. Thay đổi Tư duy (Prompts)
- Logic chính của mỗi Agent nằm ở **System Prompt** và **User Prompt** trong thư mục `core/prompts/`.
- Nếu Agent phân loại sai hoặc trích xuất thiếu, hãy điều chỉnh văn bản chỉ dẫn trong các file `.py` tương ứng tại đây.

### 2. Thay đổi Cấu trúc Dữ liệu (Schemas)
- Các Agent sử dụng **Structured Outputs** dựa trên Pydantic. 
- Để AI trả về thêm thông tin (ví dụ: điểm tự tin, mã màu, tag mới), hãy cập nhật Class tương ứng trong `core/schemas/agent_outputs.py`.

### 3. Cấu hình Model & Độ sáng tạo (Settings)
- Mở `core/config/settings.py` hoặc file `.env` để đổi Model (GPT-4o, GPT-4o-mini, v.v.).
- Chỉnh `temperature` trong hàm `__init__` của từng Agent:
  - **Cold (0.0 - 0.2)**: Dành cho Task cần chính xác tuyệt đối (Router, Locator, Organizer).
  - **Warm (0.5 - 0.7)**: Dành cho Task cần hành văn tự nhiên (Synthesizer, Planner).

---

## 🧪 Cách Cài Đặt và Kiểm Thử

### 1. Cài Đặt
```bash
# Cài đặt qua uv (Khuyên dùng)
uv sync
source .venv/bin/activate

# Cấu hình môi trường
cp .env.example .env
```

### 2. Chạy Kiểm Thử (Pytest)
Hệ thống có bộ test giả lập chính xác các luồng Logic mới (bao gồm Keyword Extraction và Vòng lặp Locator):
```bash
# Test toàn bộ
pytest tests/ -v -s

# Test cụ thể luồng QA (Xem logic vòng lặp Locator)
pytest tests/test_flow_qa.py -s
```

---
*Ghi chú: Luôn đảm bảo `OPENAI_API_KEY` của bạn có đủ quota để chạy các mô hình Vision.*
