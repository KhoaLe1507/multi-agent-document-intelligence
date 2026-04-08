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

Hệ thống xoay quanh hai (02) Workflow chính, được điều phối bởi **SystemPipeline**.

### Bước Khởi Nguồn Mọi Luồng (Pipeline Entry)
1. **Lấy Đề Bài (Task Fetching):** Lấy bài toán từ DataProvider.
2. **Định Tuyến Task (Task Routing):** Giao cho `TaskRouterAgent` đọc `prompt_template`. Agent này suy luận và quyết định hướng đi bằng cờ hiệu: `QA` hoặc `ORGANIZE`.

### 1. Luồng Hỏi Đáp & Trích Xuất (Question Answering - QA Workflow)
*Mục tiêu: Đọc hàng loạt tài liệu hỗn hợp và tìm chính xác câu trả lời hoặc trích xuất số liệu.*

1. **Tải File:** Download toàn bộ tài nguyên (PDF, Excel, Ảnh,..) vào thư mục `downloaded_data/`.
2. **Chế biến Dữ liệu (Parsing):** Gọi các Parser (`core.parsers`). Phân rã dữ liệu thô (ví dụ PDF cắt thành ảnh từng trang, Excel cắt text) tạo thành danh sách các `DocumentChunk`.
3. **Trinh sát & Khoanh vùng (File Locator):** `FileLocatorAgent` nhận một tóm tắt siêu ngắn gọn về tất cả các file. Nhiệm vụ của nó là loại bỏ các file không liên quan, trả về chính xác tên các file cần đưa vào quá trình "đọc kỹ".
4. **Lên Kế Hoạch Đọc (Planner):** `PlannerAgent` nhận Prompt từ hệ thống và tạo ra "Plan" bao gồm các Guidelines bắt lỗi & Keywords cần chú ý để truyền cho Extractor (Giúp việc trích xuất không bị lạc đề).
5. **Trích Xuất Chuyên Sâu (Extractor):** Tại đây, `ExtractorAgent` sẽ xử lý cẩn thận các chunk/ảnh (sử dụng khả năng Vision hoặc Text OCR) để đọc chi tiết dựa trên Guidelines.
6. **Tổng Hợp (Synthesizer):** `SynthesizerAgent` nhận toàn bộ các Output thô từ Extractor, suy luận lần cuối, chuẩn hoá câu văn và tạo câu trả lời cuối cùng (`final_answer` & `thought_log`).
7. **Nộp bài:** Đẩy về lại **DataProvider**.

### 2. Luồng Phân Loại Dữ Liệu (Organization Workflow)
*Mục tiêu: Đọc tên thư mục/yêu cầu và danh sách file, sắp xếp file vào đúng Taxonomy mà quy định dự án yêu cầu.*

1. Lấy danh sách tài nguyên và tên file.
2. **Brainstorming Phân Loại:** Ném cho `FileOrganizerAgent` đọc hiểu yêu cầu (Prompt) và danh sách file. Agent này tự thiết kế Taxonomy (Sơ đồ thư mục cấp độ nhánh cây) hợp lý dựa theo logic kỹ thuật/hành chính.
3. **Nộp bài:** Output của Organize này thường là các Thought Log về cách phân chia nhánh dữ liệu, nộp trực tiếp qua **DataProvider**.

---

## 🤖 Các Agents Trong Hệ Thống

Tất cả các Agent đều kế thừa tính năng từ `BaseAgent` để giao tiếp với LLM qua OpenAI (kèm logic thử lại `llm_retry` chống đứt gãy mạng).

1. **`TaskRouterAgent`:** Cảnh sát giao thông. Đọc yêu cầu đầu vào, trả về quyết định phân luồng.
2. **`FileLocatorAgent`:** Phân tích một lượt (skimming) và dự đoán tài liệu gốc chứa đáp án.
3. **`PlannerAgent`:** Dịch "câu hỏi của người dùng" thành "Chiến lược hành động cho AI trích xuất".
4. **`ExtractorAgent`:** Công nhân cày cuốc. Soi từng pixel, từng chữ nhằm tìm kiếm số liệu, text theo "Chiến lược" đã đề ra. (Hỗ trợ nhúng Base64 cho Vision Model).
5. **`SynthesizerAgent`:** Thư ký tổng hợp. Ghép mảnh kết quả từ nhiều Extractors (thậm chí giải quyết xung đột khi thông tin mâu thuẫn) để ra Báo cáo Cuối Cùng.
6. **`FileOrganizerAgent`:** Thủ thư. Chuyên lập quy tắc thư mục học và xếp file có logic.

---

## ⚙️ Cách Điều Chỉnh Agent (Agent Tuning)

Trọng tâm của hệ thống này là tính cấu hình và hướng dữ liệu của AI. Bạn có thể dễ dàng điều chỉnh hành vi của Agent:

- **Chỉnh sửa Prompts:** Hầu hết logic "tư duy" của AI nằm tại các System Prompts được thiết kế khi khởi tạo Agent hoặc gọi `.call_llm(system_prompt=...)`. Chỉnh sửa Prompt để Agent chạy tuân thủ theo rule của bạn hơn.
- **Cấu hình Model & Temperature:** 
  - Mở `core/config/settings.py` (hoặc cấu hình file `.env`).
  - Mỗi Agent con có thể truyền `temperature` vào bộ khởi tạo `super().__init__(agent_name, temperature)`.
  - Nhiệm vụ phân loại cứng nhắc (`Router`, `Organizer`): Nên để `Temperature = 0.0 - 0.2`.
  - Nhiệm vụ sáng tạo/Tổng hợp văn (`Synthesizer`): Nên để `Temperature = 0.5 - 0.7`.
- **Định Nghĩa Lại Pydantic Models:** Cấu trúc Output luôn ép trả về Object (Structured Output). Vào `core/schemas/` hoặc bên trong các file agent để thay đổi `pydantic.BaseModel` nhằm thêm các Data Field AI cần trả về.

---

## 🧪 Cách Cài Đặt Khởi Chạy và Kiểm Thử (Testing)

### 1. Cài Đặt Môi Trường
Dự án được khuyến nghị dùng Python >=3.10 và công cụ quản lý package **uv** (tối ưu nhất).

**Sử dụng `uv` (Khuyên dùng):**
```bash
# Cài đặt toàn bộ dependencies và tạo môi trường ảo tự động
uv sync

# Kích hoạt môi trường ảo
source .venv/bin/activate
```

**Sử dụng `pip` truyền thống:**
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt  # (Nếu bạn đã xuất requirements.txt)
```

**Cấu hình API Keys:**
Copy file mẫu và điền thông tin:
```bash
cp .env.example .env
```
Mở tệp `.env` và nhập `OPENAI_API_KEY` cũng như các thông tin cấu hình Server.

### 2. Chạy Hệ Thống Thực Tế
```bash
python main.py
```
*(Hệ thống sẽ chạy liên tục, tự đợi và fetch các task mới từ máy chủ nhờ lệnh `run_continuous()` hoặc `process_single_task()`)*.

### 3. Cách Test (Testing Bằng Pytest)
Hệ thống đi kèm module `tests/` sử dụng `unittest.mock` và `pytest` giúp đảm bảo khả năng logic mà không cần đốt tiền Token.

Chạy toàn bộ Test:
```bash
pytest tests/ -v
```

**Các nhóm Test chính (Mocking Flow):**
- `test_flow_qa.py`: Giả lập toàn bộ luồng QA (từ Chunk -> Router -> Locator -> QA/Extract LLM).
- `test_flow_organization.py`: Giả lập luồng File Organization Taxonomy.
- `test_data_pipeline.py` & `test_agents.py`: Test từng rãnh của Data Pipeline và Agent output format độc lập.

*(Để chạy một luồng test chuyên biệt)*:
```bash
pytest tests/test_flow_qa.py -s
```
> Thêm cờ `-s` để in các output print log từ Agent ra màn hình theo thời gian thực.
