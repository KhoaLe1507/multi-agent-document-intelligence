import json
import os
from datetime import datetime
from pathlib import Path
from pydantic import BaseModel

TRACE_DIR = Path("logs/traces")
TRACE_DIR.mkdir(parents=True, exist_ok=True)

class TaskTracer:
    """Singleton ghi log Markdown siêu chi tiết cho từng Task."""
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(TaskTracer, cls).__new__(cls)
            cls._instance.current_task = None
            cls._instance.spans = []
        return cls._instance

    def start_task(self, task_id: str, prompt_template: str = "", resources: list = None):
        if resources is None:
            resources = []
        self.current_task = {
            "task_id": task_id,
            "start_time": datetime.now(),
            "prompt_template": prompt_template,
            "task_type": "Chưa xác định",
            "resources": resources
        }
        self.spans = []

    def set_task_type(self, task_type: str):
        if self.current_task:
            self.current_task["task_type"] = task_type
            
    def add_agent_span(self, agent_name: str, system_prompt: str, user_prompt: str | list, response: any):
        if not self.current_task:
            return  # Không có task nào đang chạy

        # Format user prompt
        user_text = ""
        if isinstance(user_prompt, str):
            user_text = user_prompt
        elif isinstance(user_prompt, list):
            for item in user_prompt:
                if item.get("type") == "text":
                    user_text += item.get("text", "") + "\n"
                elif item.get("type") == "image_url":
                    user_text += "\n*[Đã nén và gửi 1 hình ảnh Vision Base64]*\n"

        # Format response
        if isinstance(response, BaseModel):
            response_text = "```json\n" + response.model_dump_json(indent=2) + "\n```"
        else:
            response_text = str(response)

        span = {
            "agent_name": agent_name,
            "time": datetime.now(),
            "system_prompt": system_prompt,
            "user_prompt": user_text.strip(),
            "response": response_text
        }
        self.spans.append(span)

    def end_task(self):
        if not self.current_task:
            return
            
        task_id = self.current_task["task_id"]
        start_time = self.current_task["start_time"]
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        md_lines = []
        md_lines.append(f"# 🎯 NHẬT KÝ TASK: `{task_id}`")
        md_lines.append(f"> **Thời gian thực thi:** {duration:.2f} giây")
        md_lines.append(f"> **Phân loại Task (Type):** `{self.current_task['task_type']}`")
        md_lines.append(f"> **Ngày giờ:** {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        md_lines.append(f"\n## 📜 Đề bài gốc (Prompt Template)\n")
        md_lines.append(f"```text\n{self.current_task['prompt_template']}\n```")
        
        resources = self.current_task.get("resources", [])
        if resources:
            md_lines.append("\n## 📁 Danh sách tệp đính kèm (Resources)\n")
            for idx, res in enumerate(resources, 1):
                md_lines.append(f"{idx}. `[{res.file_type}]` **{res.file_path}**")
                
        md_lines.append(f"\n---\n")
        
        md_lines.append(f"## 🤖 LỊCH SỬ TƯ DUY CỦA CÁC AGENTS\n")
        
        for i, span in enumerate(self.spans, 1):
            md_lines.append(f"### Bước {i}: [{span['agent_name']}]")
            md_lines.append(f"*🕛 Thời gian gọi: {span['time'].strftime('%H:%M:%S')}*")
            
            md_lines.append(f"\n<details><summary><b>1. System Prompt (Quyền hạn)</b></summary>\n")
            md_lines.append(f"```text\n{span['system_prompt']}\n```\n</details>\n")
            
            md_lines.append(f"\n<details open><summary><b>2. User Prompt (Đầu vào)</b></summary>\n")
            md_lines.append(f"```text\n{span['user_prompt']}\n```\n</details>\n")
            
            md_lines.append(f"\n<details open><summary><b>3. Output (Kết quả phân tích)</b></summary>\n")
            md_lines.append(f"{span['response']}")
            md_lines.append(f"\n</details>\n")
            md_lines.append(f"\n---\n")
        
        # Save to file
        file_path = TRACE_DIR / f"task_{task_id}.md"
        with open(file_path, "w", encoding="utf-8") as f:
            f.write("\n".join(md_lines))
            
        print(f"\n✅ Đã xuất báo cáo Agent cho Task {task_id} tại file: {file_path}")
        
        self.current_task = None
        self.spans = []

# Global instance
tracer = TaskTracer()
