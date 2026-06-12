# Evaluate OCR Multi-Agent System Without Ground Truth

## Mục tiêu

Dataset hiện tại không có ground truth, nên không thể evaluate theo kiểu accuracy/F1 truyền thống. Cách phù hợp là xây dựng một evaluation pipeline nhiều tầng để đo:

- Hệ thống có chạy hết workflow không.
- Có dùng đúng resource không.
- Output có đúng schema/format không.
- Câu trả lời có bám tài liệu không.
- Reasoning của từng agent có nhất quán không.
- Chi phí, latency, lỗi parse, lỗi agent có nằm trong ngưỡng chấp nhận không.

Evaluation nên chạy offline trên `data/dump.json` và các file trong `data/`.

## Kết quả cần tạo ra

Nên implement một thư mục:

```text
eval/
  run_eval.py
  metrics.py
  judges.py
  report.py
  rubrics/
    qa_rubric.md
    organize_rubric.md
  outputs/
    eval_runs/
```

Mỗi lần chạy evaluate sinh ra:

```text
eval/outputs/eval_runs/<timestamp>/
  submissions.jsonl
  task_metrics.jsonl
  judge_scores.jsonl
  summary.md
  failures.jsonl
```

## Tầng 1: Dataset Readiness Check

Trước khi chạy agent, kiểm tra dataset local.

Metrics:

- `total_tasks`
- `runnable_tasks`
- `missing_resource_tasks`
- `total_resources`
- `missing_resources`
- `parseable_resources`
- `unparseable_resources`

Rule bắt buộc:

```python
local_name = resource.file_path.replace("/", "_")
local_path = data_dir / local_name
```

Task chỉ được đưa vào eval nếu toàn bộ resource tồn tại.

## Tầng 2: Execution Metrics

Chạy workflow thật trên từng task, nhưng không cần submit server. Hệ thống hiện đã ghi local vào:

```text
logs/local_submissions.jsonl
```

Cần capture thêm:

- `task_id`
- `task_type`: `QA` hoặc `ORGANIZE`
- `num_resources`
- `num_parsed_files`
- `num_chunks`
- `num_agent_calls`
- `num_errors`
- `latency_seconds`
- `used_tools`
- `output_empty`
- `exception`

Fail nếu:

- Workflow crash.
- Không tạo submission.
- `thought_log` rỗng.
- QA task trả answer rỗng.
- Organize task không tạo allocation hoặc thought log không có quyết định phân loại.

## Tầng 3: Schema And Format Validation

Không cần ground truth vẫn kiểm tra được output có hợp lệ hay không.

QA output:

- `answers` phải là list.
- Không được là `None`.
- Nếu prompt yêu cầu tag format như `[物件名]`, `[工期]`, output phải chứa đúng pattern.
- Không được chứa placeholder kiểu `unknown`, `not found`, `N/A` nếu tài liệu có evidence rõ trong thought log.

Organize output:

- Mọi file được nhắc trong allocation phải thuộc danh sách resource của task.
- Không được phân loại file không tồn tại.
- Folder name không được chứa ký tự invalid Windows: `\/:*?"<>|`.
- Nếu task có `N` resource, số file được phân loại nên gần `N`, trừ khi prompt yêu cầu loại bỏ.

## Tầng 4: Evidence Grounding Check

Vì không có ground truth, tiêu chí quan trọng nhất là output có được chứng minh bởi tài liệu hay không.

Implement một judge tự động:

Input cho judge:

- Prompt gốc.
- Final answer.
- Top evidence chunks mà workflow đã dùng.
- Thought log.

Judge trả JSON:

```json
{
  "grounded_score": 1-5,
  "completeness_score": 1-5,
  "format_score": 1-5,
  "consistency_score": 1-5,
  "issues": ["..."],
  "verdict": "pass|weak_pass|fail"
}
```

Rubric:

- `5`: Answer được support trực tiếp bởi text/image evidence.
- `4`: Answer hợp lý, có evidence gần đủ.
- `3`: Có một phần evidence nhưng thiếu chi tiết.
- `2`: Answer chủ yếu suy đoán.
- `1`: Không thấy evidence hoặc trái tài liệu.

Ngưỡng đề xuất:

```text
PASS      grounded >= 4 and completeness >= 4 and format >= 4
WEAK_PASS grounded >= 3 and no critical issue
FAIL      grounded <= 2 or format <= 2
```

## Tầng 5: Self-Consistency Evaluation

Với mỗi task, chạy hệ thống nhiều lần:

```text
n = 3
temperature giữ nguyên theo config hiện tại
```

So sánh output giữa các lần chạy.

QA:

- Normalize text.
- So exact/semantic similarity.
- Nếu 3 lần trả 3 đáp án khác nhau, task bị đánh dấu unstable.

Organize:

- So mapping `file_name -> folder_name`.
- Tính agreement:

```text
agreement = số allocation giống nhau / tổng số allocation
```

Ngưỡng:

```text
agreement >= 0.8: stable
0.5 <= agreement < 0.8: review_needed
agreement < 0.5: unstable
```

## Tầng 6: Cross-Agent Consistency

Kiểm tra các agent có mâu thuẫn nhau không.

Ví dụ QA:

- `FileLocatorAgent` nói file A irrelevant nhưng `ExtractorAgent` lại lấy answer từ file A.
- `PlannerAgent` yêu cầu tìm `工期` nhưng final answer không có `工期`.
- `ReviewerAgent` reject nhưng workflow vẫn ghi submission như pass.

Ví dụ Organize:

- `KeywordExtractorAgent` nhận diện file là invoice nhưng `FileOrganizerAgent` đưa vào design folder.
- Reviewer nêu issue nhưng final allocation không sửa.

Các lỗi này nên ghi vào `failures.jsonl`.

## Tầng 7: Human Audit Sampling

Không có ground truth thì vẫn cần human audit một phần.

Chọn mẫu:

- 100% task fail.
- 100% task weak_pass.
- 20-30% task pass ngẫu nhiên.
- Tất cả task có latency/cost bất thường.

Human rubric đơn giản:

```text
0 = sai rõ ràng
1 = một phần đúng
2 = đúng và đủ
```

Human review file nên có format:

```csv
task_id,task_type,auto_verdict,human_score,human_note
```

## Tầng 8: Regression Evaluation

Sau mỗi lần sửa code hoặc prompt, chạy lại cùng một tập task.

Lưu baseline:

```text
eval/baselines/baseline_<date>.json
```

So sánh:

- pass rate tăng/giảm
- fail count tăng/giảm
- latency trung bình
- số task crash
- self-consistency
- judge score trung bình

Không merge thay đổi nếu:

- Crash rate tăng.
- Pass rate giảm mạnh.
- Cost tăng bất thường.
- Một nhóm task trước đây pass nay fail.

## Metrics Tổng Hợp

File `summary.md` nên có:

```text
# Eval Summary

Total tasks:
Runnable tasks:
Completed tasks:
Crashed tasks:

Auto judge:
- Pass:
- Weak pass:
- Fail:

Average scores:
- Grounded:
- Completeness:
- Format:
- Consistency:

Stability:
- Stable:
- Review needed:
- Unstable:

Performance:
- Avg latency:
- P95 latency:
- Total agent calls:

Top failure reasons:
1.
2.
3.
```

## Implementation Plan

### Step 1: Add Eval Runner

`eval/run_eval.py`:

- Load `ProviderService`.
- Iterate tasks.
- Run `SystemPipeline.process_single_task()`.
- Capture logs/submission.
- Write per-task metrics.

Nên thêm method mới vào pipeline:

```python
def process_task(self, task):
    ...
```

Sau đó `process_single_task()` chỉ gọi:

```python
task = self.provider.get_next_task()
return self.process_task(task)
```

Lý do: eval runner có thể kiểm soát danh sách task mà không phá workflow hiện tại.

### Step 2: Add Submission Capture

Hiện local provider đã ghi submission JSONL. Eval runner chỉ cần đọc dòng mới nhất theo `task_id`.

Nên mở rộng `ProviderService.submit_task()` để return:

```json
{
  "status": "saved",
  "mode": "local",
  "task_id": "...",
  "path": "logs/local_submissions.jsonl"
}
```

### Step 3: Add Metrics Collector

`eval/metrics.py`:

- Đếm resource.
- Đếm file parse được.
- Đếm chunk.
- Đo latency.
- Đếm exception.
- Check output empty.

### Step 4: Add Judge

`eval/judges.py`:

- Dùng LLM judge với temperature `0`.
- Tách rubric QA và Organize.
- Output bắt buộc JSON.
- Không cho judge tự sửa answer, chỉ chấm.

### Step 5: Add Report Generator

`eval/report.py`:

- Đọc `task_metrics.jsonl`.
- Đọc `judge_scores.jsonl`.
- Tổng hợp thành `summary.md`.

## Lưu ý Quan Trọng

- LLM-as-judge không phải ground truth. Nó chỉ là bộ lọc chất lượng.
- Human audit vẫn cần thiết cho các task quan trọng.
- Không nên chỉ nhìn final answer. Phải kiểm tra evidence và thought log.
- Nên giữ nguyên prompt/agent workflow khi evaluate để kết quả phản ánh đúng production behavior.
- Với dataset nhỏ, nên chạy toàn bộ task thay vì sample.

## Command Đề Xuất

Sau khi implement eval runner:

```bash
uv run python eval/run_eval.py --dump data/dump.json --data-dir data --out eval/outputs/eval_runs
```

Chạy regression:

```bash
uv run python eval/run_eval.py --dump data/dump.json --data-dir data --baseline eval/baselines/latest.json
```

## Tiêu Chuẩn Chấp Nhận Tối Thiểu

Trước khi coi hệ thống ổn:

```text
Crash rate = 0%
Runnable task completion >= 95%
Auto judge pass + weak_pass >= 80%
Grounded average >= 4.0
Format average >= 4.0
Unstable tasks <= 10%
All fail/weak_pass tasks reviewed by human
```

