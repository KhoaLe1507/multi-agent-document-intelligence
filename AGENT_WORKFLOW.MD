# Multi-Agent Workflow Documentation

Dưới đây là mô tả chi tiết về luồng hoạt động và vai trò của từng Agent trong hệ thống xử lý tài liệu thông minh.

---

## Tổng quan Workflow

Hệ thống được thiết kế theo hai luồng chính, được quyết định bởi **TaskRouterAgent** dựa trên yêu cầu của người dùng:

1.  **Luồng QA (Question-Answering)**: Trích xuất thông tin cụ thể từ tài liệu để trả lời câu hỏi.
2.  **Luồng Organize (File Organization)**: Phân loại tài liệu vào các thư mục được định nghĩa trước.

Mỗi luồng sẽ kích hoạt một chuỗi các Agent chuyên biệt để hoàn thành nhiệm vụ. Cuối cùng, **ReviewerAgent** sẽ đánh giá chất lượng kết quả trước khi trả về cho người dùng.

---

## 1. TaskRouter Agent

-   **Vai trò**: Đóng vai trò là "tổng đài", phân loại yêu cầu ban đầu của người dùng vào một trong các luồng xử lý chính của hệ thống (QA hoặc Organize). Đây là Agent đầu tiên trong mọi chu trình.
-   **Flow của Agent**:
    1.  Tiếp nhận yêu cầu (task prompt) từ người dùng.
    2.  Sử dụng LLM để phân tích và xác định bản chất của yêu cầu.
    3.  Quyết định xem đây là nhiệm vụ "Hỏi-Đáp" (QA) hay "Phân loại file" (Organize).
-   **Input**: `task_prompt` (Chuỗi văn bản chứa yêu cầu của người dùng).
-   **Output**: `TaskRoutingResult` (Một đối tượng chứa kết quả phân loại, ví dụ: `task_type: "QA"`).

---

## 2. Planner Agent (Chỉ trong luồng QA)

-   **Vai trò**: Lập kế hoạch chi tiết để trả lời câu hỏi của người dùng. Agent này chia nhỏ một câu hỏi phức tạp thành một danh sách các mục tiêu trích xuất (extraction goals) đơn giản hơn.
-   **Flow của Agent**:
    1.  Nhận yêu cầu đã được phân loại là "QA".
    2.  Phân tích câu hỏi và xác định những thông tin cụ thể nào cần được tìm thấy trong tài liệu.
    3.  Tạo ra một "kế hoạch trích xuất" dưới dạng JSON, liệt kê từng trường dữ liệu cần tìm.
-   **Input**: `task_prompt` (Yêu cầu ban đầu của người dùng).
-   **Output**: `PlannerResult` (Một đối tượng chứa danh sách các bước/trường thông tin cần trích xuất).

---

## 3. FileLocator Agent

-   **Vai trò**: Xác định (các) tài liệu nào trong kho lưu trữ có khả năng chứa thông tin cần thiết cho nhiệm vụ hiện tại.
-   **Flow của Agent**:
    1.  Nhận yêu cầu và bản tóm tắt nội dung của tất cả các tài liệu có sẵn.
    2.  Đối chiếu yêu cầu với các bản tóm tắt để tìm ra những tài liệu liên quan nhất.
-   **Input**: `task_prompt` và `document_summaries` (Tóm tắt nội dung các file).
-   **Output**: `FileLocatorResult` (Danh sách các đường dẫn file được cho là có liên quan).

---

## 4. KeywordExtractor Agent (Chỉ trong luồng Organize)

-   **Vai trò**: Đọc lướt nội dung của một tài liệu và rút ra các từ khóa chính giúp xác định loại tài liệu đó (ví dụ: "Báo cáo thử nghiệm", "Bản vẽ", "Bảo hành").
-   **Flow của Agent**:
    1.  Nhận nội dung của một file (văn bản hoặc hình ảnh).
    2.  Phân tích nội dung để tìm các thuật ngữ, tiêu đề, hoặc cụm từ đặc trưng.
    3.  Quyết định xem có cần đọc thêm các phần khác của tài liệu hay không (`needs_more_chunks`).
-   **Input**: `content` (Nội dung của một hoặc nhiều trang/chunk tài liệu).
-   **Output**: `KeywordExtractResult` (Một đối tượng chứa danh sách từ khóa và cờ `needs_more_chunks`).

---

## 5. FileOrganizer Agent (Chỉ trong luồng Organize)

-   **Vai trò**: Dựa trên các từ khóa do `KeywordExtractorAgent` cung cấp, quyết định chính xác thư mục mà tài liệu nên được chuyển vào.
-   **Flow của Agent**:
    1.  Nhận danh sách từ khóa và danh sách các thư mục hợp lệ.
    2.  Sử dụng LLM để "map" các từ khóa với mô tả của thư mục phù hợp nhất.
-   **Input**: `task_prompt`, `file_list` (từ khóa), và `VALID_FOLDERS` (danh sách thư mục).
-   **Output**: `OrganizeResult` (Kết quả phân loại, chỉ định file nào thuộc thư mục nào).

---

## 6. Extractor Agent (Chỉ trong luồng QA)

-   **Vai trò**: "Thợ mỏ" chuyên cần, thực hiện việc trích xuất thông tin chi tiết từ một phần nhỏ (chunk) của tài liệu, tuân thủ nghiêm ngặt theo chỉ dẫn từ `PlannerAgent`.
-   **Flow của Agent**:
    1.  Nhận một chunk tài liệu (văn bản hoặc hình ảnh), chỉ dẫn trích xuất (guidelines), và các từ khóa liên quan.
    2.  Quét chunk để tìm chính xác thông tin được yêu cầu.
    3.  Trích xuất dữ liệu một cách trung thực, không suy diễn, không bịa đặt. Nếu không tìm thấy, nó sẽ báo cáo là không có.
-   **Input**: `DocumentChunk` (một phần tài liệu), `guidelines` (chỉ dẫn), `keywords` (từ khóa).
-   **Output**: `ExtractionResult` (Đối tượng chứa dữ liệu trích xuất được, cờ `found_information`, và điểm tin cậy).

---

## 7. Synthesizer Agent (Chỉ trong luồng QA)

-   **Vai trò**: Tổng hợp tất cả các mảnh thông tin riêng lẻ do `ExtractorAgent` thu thập từ nhiều chunk khác nhau để tạo thành một câu trả lời cuối cùng, mạch lạc và hoàn chỉnh.
-   **Flow của Agent**:
    1.  Nhận yêu cầu ban đầu và một danh sách các kết quả trích xuất (`ExtractionResult`).
    2.  Sắp xếp, kết hợp và định dạng lại các mảnh dữ liệu thành một câu trả lời tự nhiên, đáp ứng đúng câu hỏi của người dùng.
-   **Input**: `task_prompt` và `extracted_pieces` (danh sách các kết quả trích xuất).
-   **Output**: `SynthesisResult` (Câu trả lời cuối cùng và thought log tổng hợp).

---

## 8. Reviewer Agent

-   **Vai trò**: Thanh tra viên chất lượng, kiểm tra lại kết quả cuối cùng của luồng QA hoặc Organize để đảm bảo tính chính xác, logic và đầy đủ.
-   **Flow của Agent**:
    1.  Nhận kết quả cuối cùng (từ `SynthesizerAgent` hoặc `FileOrganizerAgent`) và toàn bộ "dòng suy nghĩ" (thought log) của chu trình.
    2.  Đánh giá xem kết quả có đáp ứng hoàn hảo yêu cầu ban đầu không, có dấu hiệu "ảo giác" (hallucination) hay sai sót logic không.
    3.  Đưa ra phán quyết: `passed` (đạt) hoặc `failed` (không đạt), kèm theo lý do. Nếu không đạt, hệ thống có thể chạy lại quy trình.
-   **Input**: `prompt_template`, `answers`/`thought_log`.
-   **Output**: `ReviewResult` (Đối tượng chứa kết quả đánh giá `passed`/`failed` và nhận xét).
