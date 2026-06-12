# CODEBASE FILE MAP

Tài liệu này mô tả công dụng của từng file code chính trong dự án `ocr_multi_agents`.

## Phạm vi

- Bao gồm các file Python trong `core/`, `dataProvider/`, `tests/` và `main.py`.
- Không liệt kê `__pycache__`, file dữ liệu mẫu, log, file môi trường, lockfile hay các tài liệu `.md` khác.

## Tổng quan kiến trúc

- `main.py` là điểm khởi động chương trình.
- `dataProvider/` phụ trách nạp task/resource từ dataset local và ghi submission local.
- `core/pipeline.py` định tuyến task vào một trong hai workflow chính:
  - `QAWorkflow`: đọc tài liệu để trả lời câu hỏi.
  - `OrganizeWorkflow`: phân loại tài liệu vào taxonomy thư mục.
- `core/agents/` chứa các agent LLM chuyên trách cho từng vai trò.
- `core/parsers/` chuyển file thô thành `DocumentChunk` để agent xử lý.
- `core/prompts/` chứa system prompt và hàm dựng user prompt cho từng agent.
- `core/schemas/` định nghĩa kiểu dữ liệu đầu vào và đầu ra chuẩn.
- `core/utils/` chứa logging, retry, cache, trace.

## Root

### `main.py`

- Entry point của ứng dụng.
- Load biến môi trường bằng `dotenv`.
- Khởi tạo `ProviderService` ở chế độ local.
- Khởi tạo `SystemPipeline` rồi chạy `process_single_task()` cho một task.
- Có comment sẵn để chuyển sang `run_continuous()` nếu muốn chạy vòng lặp liên tục.

## `core/`

### `core/pipeline.py`

- Điều phối luồng xử lý cấp cao của hệ thống.
- Lấy task mới từ `ProviderService`.
- Gọi `TaskRouterAgent` để phân loại task thành `QA` hoặc `ORGANIZE`.
- Gọi workflow tương ứng: `QAWorkflow` hoặc `OrganizeWorkflow`.
- Tích hợp `tracer` để mở, gán loại và đóng trace log cho từng task.

### `core/agents/__init__.py`

- File export tập trung cho các agent trong package `core.agents`.
- Giúp import gọn hơn ở các nơi khác trong codebase.

### `core/agents/base_agent.py`

- Lớp nền cho mọi agent dùng Google Gemini.
- Tạo `google-genai` client từ cấu hình hệ thống.
- Cung cấp `call_llm()` để gọi model theo 2 chế độ:
  - text thường
  - structured output theo `Pydantic` model
- Hỗ trợ vision qua `image_base64`.
- Gắn retry tự động bằng decorator `llm_retry`.
- Ghi trace đầu vào và đầu ra của mỗi lần gọi agent.

### `core/agents/task_router.py`

- Agent vào cổng của hệ thống.
- Đọc `task_prompt` và quyết định bài toán thuộc nhánh `QA` hay `ORGANIZE`.
- Dùng prompt trong `router_prompts.py`.
- Trả về `TaskRoutingResult`.

### `core/agents/file_locator.py`

- Agent “trinh sát” trong luồng QA.
- Xác định file nào thật sự liên quan tới câu hỏi trước khi extract sâu.
- Có 2 cách gọi:
  - `locate_files()` dùng text summary
  - `locate_files_advanced()` dùng content blocks có cả ảnh cho vision
- Trả về `FileLocatorResult`.

### `core/agents/planner.py`

- Agent lập kế hoạch trích xuất cho QA.
- Biến prompt người dùng thành hướng dẫn trích xuất chi tiết và danh sách từ khóa mục tiêu.
- Trả về `PlannerResult`.

### `core/agents/extractor.py`

- Agent “xạ thủ” trích xuất thông tin từ từng `DocumentChunk`.
- Hỗ trợ cả chunk text/table lẫn image.
- Với image chunk, không nhét base64 vào text prompt mà gửi riêng theo định dạng vision.
- Trả về `ExtractionResult`.

### `core/agents/synthesizer.py`

- Agent tổng hợp kết quả cuối trong luồng QA.
- Nhận các mảnh dữ liệu đã extract, hợp nhất thành câu trả lời cuối cùng theo format yêu cầu.
- Trả về `SynthesisResult`.

### `core/agents/reviewer.py`

- Agent kiểm định chất lượng trước khi nộp bài.
- Có 2 mode:
  - `review_qa()` để soát draft answer của luồng QA
  - `review_organize()` để soát lập luận phân loại file
- Trả về `ReviewResult`.

### `core/agents/file_organizer.py`

- Agent phân loại file vào taxonomy thư mục tiếng Nhật.
- Chứa `VALID_FOLDERS`: danh sách taxonomy hợp lệ của cuộc thi.
- Dùng keyword/summary của file để map mỗi file vào đúng một folder.
- Trả về `OrganizeResult`.

### `core/agents/keyword_extractor.py`

- Agent trích xuất keyword phục vụ bài toán phân loại file.
- Đọc nội dung tài liệu hoặc content blocks vision để lấy keyword đặc trưng.
- Có cờ `needs_more_chunks` để yêu cầu đọc thêm trang nếu chỉ mới thấy bìa/mục lục/nội dung nghèo tín hiệu.
- Trả về `KeywordExtractResult`.

### `core/workflows/__init__.py`

- File package marker cho `core.workflows`.

### `core/workflows/qa_workflow.py`

- Workflow hoàn chỉnh cho bài toán hỏi đáp.
- Các bước chính:
  - lấy file từ dataset local qua `ProviderService`
  - parse file thành chunk và tận dụng cache
  - dùng `FileLocatorAgent` để xác định file liên quan
  - dùng `PlannerAgent` để lập kế hoạch
  - chạy `ExtractorAgent` song song trên các chunk mục tiêu
  - dùng `SynthesizerAgent` tạo đáp án
  - dùng `ReviewerAgent` review và yêu cầu viết lại tối đa 2 vòng
  - ghi kết quả qua `ProviderService`
- Có lưu `thought_log` đầy đủ cho toàn bộ pipeline.

### `core/workflows/organize_workflow.py`

- Workflow hoàn chỉnh cho bài toán tổ chức file.
- Các bước chính:
  - lấy file từ dataset local qua `ProviderService`
  - parse từng file
  - dùng `KeywordExtractorAgent` để lấy keyword, có cache chéo task
  - dùng `FileOrganizerAgent` để phân loại
  - dùng `ReviewerAgent` để kiểm định tối đa 2 vòng
  - sao chép file vật lý vào `downloaded_data/organized_output/<task_id>/`
  - ghi thought log vào JSONL local
- Có xử lý song song khi rút keyword cho nhiều file.

### `core/parsers/__init__.py`

- File package marker cho `core.parsers`.

### `core/parsers/file_router.py`

- Bộ định tuyến parser theo phần mở rộng file.
- Chuyển file về danh sách `DocumentChunk`.
- Chọn parser cụ thể cho:
  - Excel/CSV
  - ảnh
  - Word/TXT
  - PDF
- Với PDF hiện tại ưu tiên convert trang thành ảnh để vision đọc.

### `core/parsers/table_extractor.py`

- Parser cho `.csv`, `.xlsx`, `.xls`.
- Đọc dữ liệu bảng bằng `pandas`.
- Chuyển sheet hoặc bảng CSV thành markdown table để LLM đọc dễ hơn.
- Trả về `DocumentChunk` loại `table`.

### `core/parsers/text_extractor.py`

- Parser cho `.docx`, `.doc`, `.txt`.
- Với `.docx`: đọc paragraph và table qua `python-docx`.
- Với `.doc`: thử đọc như docx trước, nếu thất bại thì fallback đọc raw binary rồi lọc text in được.
- Với `.txt`: đọc UTF-8 có bỏ qua lỗi encoding.
- Trả về `DocumentChunk` loại `text`.

### `core/parsers/vision_extractor.py`

- Parser cho ảnh và PDF.
- `encode_image_to_base64()` nén/resize ảnh và chuyển sang base64 JPEG.
- `extract_vision_chunks()`:
  - với ảnh: mã hóa thành một chunk image
  - với PDF: render từng trang bằng `PyMuPDF`, convert sang ảnh rồi base64 hóa
- Trả về `DocumentChunk` loại `image`.

### `core/parsers/data_types.py`

- Định nghĩa `DocumentChunk` ở mức parser.
- Mô tả một mảnh dữ liệu chuẩn gồm `chunk_type`, `content`, `file_name`, `page_number`.
- Có helper `get_context_description()` để tạo mô tả ngữ cảnh dễ nhúng vào prompt.
- File này đang bị trùng ý nghĩa với `core/schemas/data_types.py`, nhưng hiện code chính dùng bản trong `core.schemas`.

### `core/prompts/__init__.py`

- File package marker cho `core.prompts`.

### `core/prompts/router_prompts.py`

- Chứa `ROUTER_SYSTEM_PROMPT`.
- Có hàm `get_router_user_prompt()` để dựng user prompt cho `TaskRouterAgent`.

### `core/prompts/locator_prompts.py`

- Chứa `LOCATOR_SYSTEM_PROMPT`.
- Có hàm `get_locator_user_prompt()` cho `FileLocatorAgent`.
- Mô tả framework đánh giá file liên quan, không liên quan, hay cần thêm trang.

### `core/prompts/planner_prompts.py`

- Chứa `PLANNER_SYSTEM_PROMPT`.
- Có hàm `get_planner_user_prompt()` cho `PlannerAgent`.
- Tập trung vào biến yêu cầu bài toán thành blueprint trích xuất.

### `core/prompts/extraction_prompts.py`

- Chứa `EXTRACTOR_SYSTEM_PROMPT`.
- Có hàm `get_extractor_user_prompt()` cho `ExtractorAgent`.
- Nhấn mạnh nguyên tắc zero hallucination và confidence scoring.

### `core/prompts/synthesizer_prompts.py`

- Chứa `SYNTHESIZER_SYSTEM_PROMPT`.
- Có hàm `get_synthesizer_user_prompt()` để ghép các extracted pieces thành đầu vào cho `SynthesizerAgent`.

### `core/prompts/organizer_prompts.py`

- Chứa `ORGANIZER_SYSTEM_PROMPT`.
- Có hàm `get_organizer_user_prompt()` cho `FileOrganizerAgent`.
- Gồm rule map nội dung tài liệu sang taxonomy thư mục.

### `core/prompts/reviewer_prompts.py`

- Chứa 2 system prompt:
  - `REVIEW_QA_SYSTEM`
  - `REVIEW_ORG_SYSTEM`
- Định nghĩa tiêu chí review nghiêm ngặt cho 2 workflow.

### `core/schemas/__init__.py`

- File package marker cho `core.schemas`.

### `core/schemas/data_types.py`

- Định nghĩa model dữ liệu lõi dùng xuyên suốt hệ thống.
- `DocumentChunk`: đại diện cho một đoạn text, bảng hoặc ảnh sau parse.
- `TaskContext`: gom ngữ cảnh task, prompt gốc và danh sách chunks.

### `core/schemas/agent_outputs.py`

- Định nghĩa toàn bộ structured output của các agent bằng Pydantic.
- Gồm các model:
  - `TaskRoutingResult`
  - `KeywordExtractResult`
  - `PlannerResult`
  - `ExtractionResult`
  - `SynthesisResult`
  - `FileAllocation`
  - `OrganizeResult`
  - `FileLocatorResult`
  - `ReviewResult`
- Đây là contract dữ liệu giữa agent và workflow.

### `core/config/__init__.py`

- File package marker cho `core.config`.

### `core/config/settings.py`

- Quản lý cấu hình môi trường bằng `pydantic-settings`.
- Đọc local dataset path, Gemini API key, model name, nhiệt độ từng agent, giới hạn token, retry.
- Khởi tạo singleton `settings`.
- Nếu thiếu biến môi trường, ném `SystemConfigError` ngay lúc import.

### `core/exceptions/__init__.py`

- File package marker cho `core.exceptions`.

### `core/exceptions/agent_errors.py`

- Định nghĩa nhóm exception chuẩn cho hệ thống.
- Gồm:
  - `BaseSystemError`
  - `SystemConfigError`
  - `DataProviderError`
  - `LLMCommunicationError`
  - `ParsingError`

### `core/utils/__init__.py`

- File package marker cho `core.utils`.

### `core/utils/logger.py`

- Cấu hình `loguru` cho toàn hệ thống.
- Thiết lập log ra console và file `logs/agent_pipeline.log`.
- Trên Windows có bọc lại `stdout/stderr` để tránh lỗi encoding UTF-8.
- Export `agent_logger` dùng chung.

### `core/utils/retry.py`

- Cung cấp decorator retry cho các lệnh gọi LLM.
- Dùng `tenacity` với exponential backoff.
- Có callback `log_retry_attempt()` để log mỗi lần retry.

### `core/utils/cache_manager.py`

- Quản lý cache bộ nhớ và cache đĩa trong thư mục `cache/`.
- Cho phép tái sử dụng:
  - `chunks` đã parse
  - `keywords`
  - `thought_log`
  - các dữ liệu gắn theo tên file
- Hữu ích để tránh parse/LLM lại trên file lặp giữa nhiều task.

### `core/utils/tokens.py`

- Hàm tiện ích đếm token và cắt ngắn text theo model.
- `count_tokens()` dùng heuristic local cho Gemini chunking.
- `truncate_text()` cắt text nếu vượt `MAX_TOKENS_PER_CHUNK`.
- Hiện tại không thấy được gọi nhiều trong workflow chính.

### `core/utils/trace_logger.py`

- Ghi trace Markdown cực chi tiết cho từng task.
- `TaskTracer` là singleton lưu:
  - prompt gốc
  - danh sách resource
  - loại task
  - mọi span gọi agent
- Khi `end_task()`, xuất file Markdown vào `logs/traces/task_<task_id>.md`.

## `dataProvider/`

### `dataProvider/__init__.py`

- Export `ProviderService` để import gọn từ package gốc.

### `dataProvider/models/session.py`

- Dataclass `Session`.
- Lưu `session_id`, `access_token`, `expires_in`.

### `dataProvider/models/task.py`

- Dataclass `Resource`: thông tin file đính kèm của task.
- Dataclass `Task`: `task_id`, `prompt_template`, danh sách `resources`.

### `dataProvider/services/provider_service.py`

- Lớp service làm việc trực tiếp với `data/dump.json` và folder `data`.
- `create_session()` tạo session local tương thích với interface cũ.
- `get_next_task()` lấy task tiếp theo từ dump và map JSON sang dataclass `Task`.
- `download_file()` copy resource local sang path workflow yêu cầu.
- `submit_task()` ghi kết quả làm bài vào JSONL local.

## `tests/`

### `tests/test_agents.py`

- Test thủ công/online cho các agent lõi.
- Kiểm tra:
  - router phân nhánh đúng
  - locator tìm đúng file
  - organizer bám taxonomy đúng
- Cần môi trường có Gemini API key vì gọi agent thật.

### `tests/test_api.py`

- Script test tương tác `dataProvider` với dataset local.
- Kiểm tra biến môi trường, tạo session local, lấy task, resolve resource.
- Không dùng pytest chuẩn; thiên về chạy tay để xác minh kết nối hệ thống.

### `tests/test_data_pipeline.py`

- Kiểm tra parser và data provider theo hướng offline/local.
- Test parse file Excel và PDF mẫu thành chunk đúng loại.
- Test local provider:
  - lấy task từ dump
  - copy resource từ folder data
  - ghi submission local
- Không cần chạm API thật.

### `tests/test_flow_organization.py`

- Test luồng phân loại file ở mức gần integration.
- Dùng file mẫu Excel local.
- Đi qua các bước chính: parse, router, keyword extraction, organize.
- Mục tiêu là xác minh flow organize không vỡ ở các khâu nối.

### `tests/test_flow_qa.py`

- Test luồng QA ở mức gần integration.
- Parse PDF mẫu, cho locator đọc nhiều vòng chunk, rồi gọi `BaseAgent` trực tiếp để trả lời từ ảnh.
- Kiểm tra luồng vision-based QA không crash.

### `tests/test_image_excel_handling.py`

- Test riêng việc xử lý Excel và PDF ảnh.
- Kiểm tra:
  - parse Excel ra table/text chunk
  - parse PDF ra image chunk
  - keyword extraction trên dữ liệu bảng/ảnh
  - `ExtractorAgent` có đọc vision chunk được không
- Lưu ý: trong file này có lời gọi `KeywordExtractorAgent.extract_keywords(..., image_base64=...)`, nhưng method hiện tại chỉ nhận một tham số `content`; test này có khả năng lỗi nếu chạy nguyên trạng.

### `tests/test_logger.py`

- Test `TaskTracer` end-to-end.
- Dùng `monkeypatch` đổi `TRACE_DIR` sang thư mục tạm.
- Kiểm tra file Markdown trace được tạo đúng và có đủ task info, resource, agent span, vision marker.

### `tests/test_parsers.py`

- Bộ test unit cho parser.
- Bao phủ các trường hợp:
  - file lỗi/không tồn tại
  - ảnh tĩnh
  - `.docx`, `.txt`, `.doc` fallback
  - format không hỗ trợ

### `tests/test_pipeline.py`

- Script test end-to-end cho toàn pipeline với dataset local.
- Tạo file log riêng theo timestamp.
- Khởi tạo provider, tạo session, dựng pipeline, xử lý một task đầy đủ.
- Phù hợp để chạy xác minh toàn hệ thống với dữ liệu local.

### `tests/test_workflows_offline.py`

- Test offline cho 2 workflow chính bằng `MagicMock`.
- `test_offline_organize_workflow()`:
  - mock download
  - mock submit
  - xác minh cache và review loop hoạt động
- `test_offline_qa_workflow()`:
  - mock provider
  - chạy QA workflow end-to-end với PDF mẫu
  - xác minh có submit và có đủ tool name trong `used_tools`

## Ghi chú thêm

- Có sự trùng lặp model `DocumentChunk` giữa:
  - `core/parsers/data_types.py`
  - `core/schemas/data_types.py`
- Workflow chính hiện dùng `core.schemas.data_types.DocumentChunk`, nên file trong `core/parsers/data_types.py` nhiều khả năng là bản cũ hoặc chưa được dọn.

- Nhiều test trong `tests/` là integration test gọi LLM thật, không phải unit test thuần. Khi chạy cần phân biệt:
  - test offline/mock
  - test online cần Gemini cho các agent LLM
