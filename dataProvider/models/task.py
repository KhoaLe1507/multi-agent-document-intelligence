# dataProvider/models/task.py
from dataclasses import dataclass
from typing import List

@dataclass
class Resource:
    file_path: str
    file_type: str
    token: str

@dataclass
class Task:
    task_id: str
    prompt_template: str
    resources: List[Resource]