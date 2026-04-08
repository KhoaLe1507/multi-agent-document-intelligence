# 🌟 Hệ Thống OCR Multi-Agents (AI Automation)

Dự án này là một hệ thống **Multi-Agents tự động** toàn diện, chuyên xử lý các nhiệm vụ phức tạp trên tài liệu. Hệ thống vận dụng sức mạnh kết hợp giữa kiến trúc Đa Tác Vụ (Multi-Modal Vision LLMs như OpenAI/Gemini), cấu trúc dữ liệu nghiêm ngặt (Pydantic Structured Outputs) và luồng định tuyến thông minh để đọc, phân loại thư mục, và trích xuất số liệu trên các định dạng (PDF OCR, Hình ảnh, Excel).

---

## 🏗 Mô tả Hệ Thống Kiến Trúc

Hệ thống được thiết kế như một cỗ máy tự vận hành vĩnh viễn (autonomous loop), tối ưu hóa việc sử dụng chung 1 HTTP Session để tiết kiệm tài nguyên.
- **DataProvider**: Là cầu nối giao tiếp với máy chủ của Ban Tổ Chức (BTC). Tự động lấy Đề bài (Fetch Task), streaming file (tiết kiệm RAM) và nộp kết quả ngay trong quá trình chạy.
- **SystemPipeline**: "Trái tim" điều phối vòng lặp (`run_continuous`). Nhận task và phân phối công việc tương ứng.
- **Core Agents**: Các "Bộ não" AI chuyên biệt hóa, hỗ trợ lẫn nhau trong các WorkFlow.

### Sơ đồ tương tác tổng quan:
`Server/API` 🔄 **DataProvider** ➡️ **SystemPipeline** ➡️ **Workflow (QA / ORGANIZE)** ➡️ `Nộp toàn bộ đáp án + Nhật ký tư duy`

---

## 🌊 Các Luồng Hoạt Động Cốt Lõi (Workflows)

Sau khi **TaskRouterAgent** phân loại đề bài, Task sẽ đi vào 1 trong 2 luồng:

### 1. Luồng Phân Loại Dữ Liệu (Organization Workflow)
*Mục tiêu: Đọc nội dung file, đánh giá "nhãn" và sắp xếp file vào đúng thư mục Taxonomy yêu cầu.*

1. **Tải & Parse:** Tải file về và băm nhỏ thành các Chunks văn bản/hình ảnh (`DocumentChunk`).
2. **Trích xuất Từ Khóa (Keyword Extraction):** `KeywordExtractorAgent` đọc siêu tốc nội dung các Text Chunks để tóm lược thành các cụm từ khóa (Keywords) cốt lõi mô tả file, nhằm tối ưu hóa độ dài ngữ cảnh.
3. **Phân loại Thông minh:** `FileOrganizerAgent` nhận một danh sách file kèm theo bộ Keywords tương ứng. Dựa vào yêu cầu (Prompt) của đề bài, Agent phân bổ file vào đúng thư mục hợp lý một cách khách quan nhất.
4. **Nộp bài (Submit):** Trả về server thư mục tương ứng + Lưu lại quá trình suy luận dán nhãn (`thought_log`).

### 2. Luồng Hỏi Đáp & Trích Xuất (Question Answering - QA Workflow)
*Mục tiêu: Tìm chính xác file chứa bộ dữ liệu, cào dữ liệu chi tiết và tổng hợp đáp án cuối cùng.*

1. **Tải & Parse:** Băm file thành `DocumentChunk` (cả chữ lẫn ảnh Vision Base64).
2. **Trinh sát Đa phương tiện (Iterative Multimodal Locator):** 
   - `FileLocatorAgent` áp dụng kỹ thuật **Vision Batching**, gom hàng loạt ảnh trang đầu tiên của nhiều file khác nhau để LLM "nhìn" trực tiếp bằng hệ thị giác quang học trong một Request duy nhất.
   - **Vòng lặp (Iterative Loop):** Nếu Agent phát hiện thông tin trang đầu bị thiếu (ví dụ: chỉ có trang bìa), cờ hiệu `requires_more_info = True` báo cho hệ thống tự động nạp nối tiếp trang/chunk kế tiếp đến khi chốt được chính xác file mục tiêu.
3. **Chiến lược (Planner):** `PlannerAgent` dịch đề bài thành các hướng dẫn và Hint cào dữ liệu.
4. **Xạ Thủ Trích Xuất (Extractor):** `ExtractorAgent` hoạt động như công nhân OCR, nhận lệnh từ Planner và soi chi tiết nội dung của từng Chunk (bảng biểu/hình ảnh) để móc dữ liệu.
5. **Tổng Hợp (Synthesizer):** `SynthesizerAgent` kết nối các bằng chứng thô và sắp xếp lại đáp án chuẩn format định dạng đầu ra.
6. **Nộp bài (Submit):** Hệ thống gộp toàn bộ Nhật ký tư duy (`thought_log`) từ Trinh sát -> Lên kế hoạch -> Xạ thủ -> Tổng hợp... và bắn thẳng lên server để lưu lại logic hành trình cực kì rành mạch.

---

## 🤖 Các Đặc Vụ AI (Agents)

Toàn bộ các Agent đều khởi chạy thừa kế từ class `BaseAgent` – Class đảm bảo khả năng Gọi Lại (Retry) chống sập lỗi mạng, nạp Vision API, và trả về Output chuẩn Pydantic.

1. **`TaskRouterAgent`**: Hệ thống phân loại (Dispatcher) – Quyết định chạy luồng QA hay ORGANIZE.
2. **`KeywordExtractorAgent`**: Máy đọc siêu tốc – Sinh từ khóa vắn tắt từ dữ liệu lớn.
3. **`FileOrganizerAgent`**: Chuyên gia quản lý thư mục – Sắp xếp danh mục file hiệu quả.
4. **`FileLocatorAgent`**: Lính trinh sát – Lọc và duyệt mắt các file cực nhanh, điều hành nạp thêm dữ liệu thông minh.
5. **`PlannerAgent`**: Tham mưu trưởng hành động – Dịch yêu cầu bài thi thành thuật toán tìm kiếm thô.
6. **`ExtractorAgent`**: Kỹ thuật viên nhặt sạn – Tác chiến trên từng Fragment/Table để bóc tách metrics.
7. **`SynthesizerAgent`**: Người duyệt báo cáo – Đóng gói đáp án & Viết suy luận.

---

## ⚙️ Cách Tinh Chỉnh Agent (Agent Tuning)

Hệ thống được thiết kế linh động cao, dễ thay thế thuật toán não bộ bằng cách:

### 1. Thay đổi Tư duy (Prompts)
- Logic lõi của Agent nằm trong thư mục `core/prompts/`. Tại đây bạn có thể cập nhật các câu lệnh AI sang tiếng Việt hay bất kì ngôn ngữ chiến thuật nào để Agent tỉnh táo hơn.

### 2. Sửa Cấu trúc Dữ liệu Trả Về (Schemas)
- Tất cả Agent sử dụng luồng thiết lập chặt từ **Pydantic**. Cập nhật `core/schemas/agent_outputs.py` để bổ sung các thuộc tính phân tích sâu hơn (VD: cờ độ chênh lệch, độ tin cậy của file). 

### 3. Tối ưu Token và Nhiệt Độ
- Tại `core/config/settings.py` (hoặc `.env`): Chuyển đổi Model AI dễ dàng (GPT-4o, GPT-4o-mini, Gemini 3.1 Pro).
- Chỉnh tham số `temperature` ngay trong cấu hình của từng Agent:
  - **Lạnh (0.0 - 0.2)**: Các Agent cần phán đoán logic/phân dòng (Locator, Organizer).
  - **Ấm (0.5 - 0.7)**: Các Agent mô tả, diễn giải (Synthesizer, Planner).

---

## 🧪 Hướng Dẫn Kích Hoạt Nhanh

### 1. Cài Đặt Môi Trường
```bash
# Thiết lập với UV Sync (Cực nhanh và nhẹ)
uv sync
source .venv/bin/activate

# Khởi tạo File biến máy (Env)
cp .env.example .env
# Mở .env và đặt vào OPENAI_API_KEY
```

### 2. Chạy Kiểm Thử (Pytest - Unit/E2E test)
Bộ Tests giả lập API máy chủ và mock luồng logic Pipeline cực kỳ bảo mật (Không trừ Token, an toàn tuyết đối):
```bash
# Chạy Test tổng hợp mọi Workflow
uv run pytest tests/ -v -s

# Test cục bộ mô phỏng luồng QA
uv run pytest tests/test_flow_qa.py -s
```

### 3. Khởi Chạy Thi Đấu Tự Động (Main Loop)
```bash
uv run python main.py
```
*(Hiện tại biến môi trường đang gọi tới cấu hình chạy cục bộ `process_single_task()`. Để kích hoạt vòng lặp Server bất tận, hãy mở file `main.py` và sửa thành lệnh: `pipeline.run_continuous()`).*

---
> [!IMPORTANT]
> Cần lưu ý việc duy trì Quota (Giới hạn Ngân sách) liên tục trên `OPENAI_API_KEY` cũng như tốc độ mạng LAN của Server thi đấu khi hệ thống Multi-Modal Vision tải luồng dữ liệu hình ảnh độ phân giải cao (`detail: auto`).
