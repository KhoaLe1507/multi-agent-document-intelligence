# 🌟 OCR Multi-Agents System

Dự án này là hệ thống **Multi-Agent tự động hoàn toàn**, chuyên xử lý các tác vụ bóc tách tài liệu phức tạp, hỏi đáp (QA) và tự động phân loại thư mục (Organization). Hệ thống sử dụng LangGraph để điều phối workflow có state, LangChain cho prompt utility, Google Gemini Vision và structured output kết hợp với schema Pydantic, giúp nó hoạt động trơn tru trên mọi loại file: PDF, Hình ảnh Scan, và cả Table Excel.

---

## 🏗 Kiến Trúc Hệ Thống & Tính Năng Cốt Lõi

- **Điều phối stateful & đa luồng (LangGraph + Multi-threading)**: Hệ thống dùng LangGraph để điều phối agent nodes, conditional transitions và review loops; `ThreadPoolExecutor` được dùng trong các node rút keyword/trích xuất bằng chứng để chạy song song khi độ trễ mạng là điểm nghẽn.
- **Bộ nhớ đệm Toàn cục (CacheManager)**: Lịch sử đọc chunk, kết quả ép kiểu (parse) và list từ khóa được lưu trữ chặt chẽ trong RAM (`[Cache HIT]`). Khi một file lặp lại (VD: một tập tài liệu quy chuẩn xuất hiện ở 5 câu hỏi khác nhau), hệ thống tốn 0 (không) API token và trả về kết quả trong chưa tới 1 mili-giây.
- **Tự Sửa Lỗi (Self-Correction Review Loop)**: Trước khi chốt đáp án, tất cả kết quả đều được ném cho **ReviewerAgent** (Quan lớn thẩm định). Mọi sự kiện suy diễn phi logic hoặc phân loại vô lý đều sẽ bị đánh trượt và ép buộc hệ thống tự động suy luận lại dựa trên phản hồi lỗi.
- **Phổ cập Hệ File (Universal Intake)**: Bộ xử lý không bị trói buộc ở Text. Nó phân tách Excel `.xlsx` thành Bảng Markdown nguyên bản, và tự động gọi API Vision để AI sử dụng "mắt người" phân tích với các loại file PDF rỗng text (Scanned JPG, v.v).

---

## 🌊 Luồng Xử Lý Chi Tiết (Detailed Workflows)

### 1. Luồng Tổ Chức Dữ Liệu (File Organization Workflow)
*Mục tiêu: Đọc lướt nội dung, nắm bắt keywords và điều hướng hàng loạt file vào đúng cấu trúc cây thư mục (Taxonomy).*

- **Bước 1: Cơ quan Phân tích (Parse & Cache):** 
  - Hệ thống tải xuống các tài liệu đính kèm. Khối `file_router.py` biến Excel thành Markdown và PDF/Images thành mảng `DocumentChunk` (có đánh dấu text / image chunk). 
  - Lập tức tra cứu `CacheManager`, nếu tệp đã tồn tại, dữ liệu được rút thẳng từ RAM.
- **Bước 2: Quét Khóa 360 Độ (Text & Vision):** 
  - Khởi tạo khối `ThreadPoolExecutor`. Mỗi tệp sẽ triệu hồi một tiểu đặc vụ `KeywordExtractorAgent`. Tiểu đặc vụ này có khả năng "nhìn" bức ảnh đầu tiên (Vision) HOẶC đọc chuỗi Markdown, để đúc kết ra file này thuộc nhóm kỹ thuật, báo cáo hay tài chính...
  - Danh sách keyword sau đó được lưu ngược lại vào `CacheManager` để dùng cho tương lai.
- **Bước 3: Suy luận Tập trung (Smart Classification):** 
  - Tên file đính kèm với Metadata Keyword của chúng được gói gọn thành một danh sách gửi cho `FileOrganizerAgent`. Agent này so sánh chéo với Quy định thư mục của đề bài, ép kiểu dữ liệu thành danh sách Phân Lộ (JSON).
- **Bước 4: Trọng tài Thẩm định (Self-Correction Loop):** 
  - `ReviewerAgent` đứng ngoài rà soát chéo Output của Agent tổ chức. Nếu nó phát hiện 1 file bị xếp nhầm thư mục (VD: hóa đơn xếp vào thư mục thiết kế), nó sẽ từ chối (`is_acceptable = False`) và cung cấp chuỗi lý do vi phạm (`issues`).
  - LangGraph conditional edges lúc này route chuỗi lỗi quay lại `FileOrganizerAgent` dưới dạng `[LƯU Ý TỪ REVIEWER LẦN TRƯỚC]:...`. Agent Tổ Chức lúc này giác ngộ và sửa đáp án. Quá trình bọc lót này giới hạn tối đa 2 lần.
- **Bước 5: Báo Cáo:** Chốt danh sách cuối cùng và ghi kèm toàn bộ Dòng Suy Nghĩ (Thought Log) vào file submission local.

### 2. Luồng Hỏi Đáp Tiên Tiến (QA Extraction Workflow)
*Mục tiêu: Lục soát đống hồ sơ khổng lồ để tìm kiếm các con số hoặc đáp án cực kỳ chi tiết theo yêu cầu (VD: Tìm Tên Công Trình, Chi phí thi công...).*

- **Bước 1: Chuẩn bị Nguyên Liệu & Cache:** Tương tự như quy trình File Organization, PDF biến thành các khung ảnh (Chunk) và nạp vào máy chủ.
- **Bước 2: Chiến Thuật Trinh Sát (The Scout Loop):** 
  - Khi gặp 10 file tài liệu dài hạn, việc đọc toàn bộ là quá tốn kém Token. Hệ thống thả `FileLocatorAgent` vào trận với một mảng (Batch) các trang đầu tiên từ tất cả các file.
  - Nhờ cơ chế **Iterative Look-ahead**, nếu trang bìa không cung cấp đủ bằng chứng phân loại (chỉ là tờ bìa rỗng), LocatorAgent trả về cờ "Cần Đọc Tiếp" (`requires_more_info = True`). Vòng lặp tự động tiến độ thêm 1 trang / chunk nữa của những file nghi vấn. Nó lặp đến khi khoá gọn lại 1-2 file mục tiêu thực sự chứa đáp án.
- **Bước 3: Tham mưu Tác chiến (Strategic Planning):** 
  - Nhận thấy câu hỏi có thể phức tạp, bù nhìn `PlannerAgent` được kích hoạt để chia rẽ Prompt ban đầu thành Mã Luật (Extraction guidelines) và Bộ Từ Khóa Trọng Tâm (Target keywords) để đám lính dễ đánh hơi hơn.
- **Bước 4: Bắn Tỉa Đa Luồng (The Sniper):** 
  - Đây là khâu tốn thời gian nhất. Với 10 trang của File mục tiêu, thay vì gọi lần lượt, `ThreadPoolExecutor` mở đa luồng cực đại (max 5-10 threads), ném từng trang một cho một clone của `ExtractorAgent` đánh giá độc lập. 
  - `ExtractorAgent` quét nhanh bằng Vision và Text match, và trả về đoạn dữ liệu nếu nó tự tin tìm thấy.
- **Bước 5: Tổng Hợp & Phản Biện Khắt Khe:** 
  - Mọi viên gạch dữ liệu nhặt được từ các Xạ thủ được gom chung về `SynthesizerAgent`. MC này nhào nặn lại thành một câu trả lời hoàn chỉnh mạch lạc.
  - Lập tức gửi qua cửa ngõ của `ReviewerAgent`. Nếu thông tin bịa đặt, lạc đề, hoặc không giải quyết được core Prompt, Reviewer sẽ vứt kết quả đi và bắt MC viết lại dựa trên dòng Log chê trách!
- **Bước 6: Nộp bài:** Định dạng cuối cùng, nộp thẳng cho DataProvider.

---

## 🤖 Bản Phả Hệ Tiên Tiến Của Các AI Agents

Mọi đặc vụ đều "kế thừa" khả năng bẩm sinh từ `BaseAgent`. Khối Base này xử lý ngầm việc `llm_retry` tự hồi sinh khi Model bị bóp băng thông, và ép Model phải trả về đúng Pydantic Schema theo cài đặt.

1. **`TaskRouterAgent`**: Người bảo vệ cửa Ải. Nhiệm vụ duy nhất: Tiêm prompt vào để đọc và quyết định câu lệnh bắt máy phải chạy thuật toán Tổ Chức (Organization) hay Hỏi Đáp (QA).
2. **`KeywordExtractorAgent`**: Điệp viên chớp nhoáng. Khả năng đặc biệt: Gắn thêm tham số `image_base64` để nó nhận dạng cả các file là ảnh chụp / pdf mã hóa để rút ra chùm keywords chỉ trong tích tắc.
3. **`FileOrganizerAgent`**: Quản gia sắp xếp dữ liệu. Đầu vào: Rules và Tên file + Keywords. Đầu ra: JSON map 1-1 giữa Tên File và Thư Mục.
4. **`FileLocatorAgent`**: Trinh sát tài liệu. Đầu vào: Bức tường (Batch) hàng loạt hình ảnh/text trang đầu. Đầu ra: Xác suất % file liên quan, và mệnh lệnh giữ lại / ném đi file tương ứng.
5. **`PlannerAgent`**: Tướng quân chỉ huy. Đầu vào: Prompt thuần của user. Đầu ra: Guidelines siêu tối ưu (chặt chẽ hơn) dùng riêng cho Xạ thủ Extractor.
6. **`ExtractorAgent`**: Xạ thủ đánh thuê. Đầu vào: Một hình ảnh / Một đoạn văn, phối hợp với Guidelines từ Planner. Đầu ra: Giá trị Data đích với mốc `confidence_score` (Độ tự tin).
7. **`SynthesizerAgent`**: MC hội thao. Sẽ nhặt nh наз tất cả các Data mảnh rời do dàn Extractor trả về để gom thành kết quả Final duy nhất.
8. **`ReviewerAgent`**: Tính tình sát thủ (`temperature: 0.1`). Là Đặc vụ độc lập không nhúng tay vào việc tạo lập, chỉ đi kiểm tra lỗi logic người khác. Nó đọc cả Prompt + Đáp án Nháp + Log Quy trình, cung cấp mảng phân tích các `issues` yếu kém để hệ thống tự sửa đổi vòng lặp.

---

## ⚙️ Hiệu Chỉnh Thông Số (Customization & Extensions)

Kiến trúc rời rạc hóa (Decoupled Platform) đưa quyền lực tối đa vào tay lập trình viên:
- **Muốn chỉnh sửa "bản tính" Agent (LLM Hacking)**: Update chữ viết trong `core/prompts/`. Mọi Agent đều bị điều khiển linh hồn bởi dòng chữ này.
- **Muốn AI buộc phải trả lời thêm một biến (ví dụ: `ma_hop_dong`)**: Đừng sửa hàm phức tạp! Mở class Pydantic trong `core/schemas/agent_outputs.py` và thêm field `ma_hop_dong: str = Field(description="Mã HĐ gồm 8 chữ số")`.
- **Đổi model**: Sửa `GEMINI_MODEL_NAME` trong `.env` để chọn model Gemini phù hợp.

---

## 🧪 Cài Đặt & Chạy Kiểm Thử Tự Động Toàn Hệ Thống

Chúng tôi đã thiết lập mạng lưới Test Case nội bộ để bạn an tâm đập đi xây lại không bao giờ sụp:

### 1. Khởi tạo Không gian chạy ảo
```bash
# Ưu tiên sử dụng 'uv' để cắm thư viện siêu nhanh
uv sync
cp .env.example .env
# Chắc chắn điền DATA_DIR, DATA_DUMP_PATH và GEMINI_API_KEY vào .env
```

### 2. Danh sách các File Kiểm Thử (The Test Suite)
Mọi file test nằm tại thư mục `tests/`. Chức năng cụ thể của chúng:
- **`test_agents.py`**: Chuyên kiểm tra độ thông minh độc lập của từng AI Agent (VD: FileLocator có nhìn ra file rác không? Router có phân loại task chuẩn không?).
- **`test_data_pipeline.py`**: Kiểm tra parser, mapping tên resource local, copy file từ `data`, và ghi submission JSONL.
- **`test_image_excel_handling.py`**: Đặc nhiệm xử lý dị thường. Chuyên ném vào file Excel siêu to hoặc PDF Full ảnh Scan để đo khả năng phân tích Vision/Table của AI.
- **`test_workflows_offline.py`**: Trùm cuối Integration Test. Giả lập toàn bộ luồng Organize & QA Workflow nhưng không tốn Token, nhằm chứng minh `ReviewerAgent` và `CacheManager` hoạt động ăn khớp với nhau.
- **`test_flow_qa.py` & `test_flow_organization.py`**: Các ca giả lập độc lập chuyên biệt về tư duy của hai luồng quy trình chính.

### 3. Hướng dẫn chạy Test

**Cách 1: Chạy toàn bộ hệ thống (Quét tất cả test cases)**
```bash
# Quét toàn bộ lỗi tiềm ẩn bằng 1 lệnh duy nhất
uv run pytest tests/ -v -s
```

**Cách 2: Chạy kiểm thử một Module cụ thể khi dev tính năng**
```bash
# Ví dụ: Chỉ muốn chạy test về đọc ảnh Excel
uv run pytest tests/test_image_excel_handling.py -v -s
```

### 4. Kích Hoạt Động Cơ Thực Chiến
```bash
# Lệnh kết nối mạng với Ban tổ chức và tải file thật
uv run python main.py
```
*(Hiện tại lệnh `main.py` đang nạp đúng 1 tín hiệu nhiệm vụ `pipeline.process_single_task()`. Để thả xích cho hệ thống farm task liên hoàn, hãy đổi lệnh sang `pipeline.run_continuous()`).*
