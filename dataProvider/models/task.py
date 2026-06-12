# dataProvider/models/task.py
from dataclasses import dataclass
from typing import List

@dataclass
class Resource:
    file_path: str
    file_type: str
    token: str = ""
    local_path: str | None = None

@dataclass
class Task:
    task_id: str
    prompt_template: str
    resources: List[Resource]
