# dataProvider/services/provider_service.py
from __future__ import annotations

import json
import shutil
from dataclasses import asdict, is_dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from ..models.session import Session
from ..models.task import Resource, Task


class ProviderService:
    """Local dataset provider compatible with the old API-backed interface.

    The workflows still call create_session(), get_next_task(), download_file(),
    and submit_task(). This implementation serves those calls from local files.
    """

    def __init__(
        self,
        dump_path: str | Path = "data/dump.json",
        data_dir: str | Path = "data",
        submissions_path: str | Path = "logs/local_submissions.jsonl",
        *,
        skip_missing_tasks: bool = True,
    ):
        self.dump_path = Path(dump_path)
        self.data_dir = Path(data_dir)
        self.submissions_path = Path(submissions_path)
        self.skip_missing_tasks = skip_missing_tasks

        self.session: Session | None = None
        self._cursor = 0
        self._token_to_resource: dict[str, Resource] = {}
        self._tasks = self._load_tasks()

    @staticmethod
    def to_local_resource_name(file_path: str) -> str:
        return file_path.strip("/\\").replace("/", "_").replace("\\", "_")

    def resolve_resource_path(self, file_path: str) -> Path:
        return self.data_dir / self.to_local_resource_name(file_path)

    def _load_tasks(self) -> list[Task]:
        if not self.dump_path.exists():
            raise FileNotFoundError(f"Local dump file not found: {self.dump_path}")
        if not self.data_dir.exists():
            raise FileNotFoundError(f"Local data directory not found: {self.data_dir}")

        with self.dump_path.open("r", encoding="utf-8-sig") as f:
            payload = json.load(f)

        raw_tasks = payload.get("tasks", [])
        tasks: list[Task] = []
        missing_task_count = 0

        for raw_task in raw_tasks:
            resources: list[Resource] = []
            missing_files: list[str] = []

            for raw_res in raw_task.get("resources", []):
                file_path = raw_res["file_path"]
                local_path = self.resolve_resource_path(file_path)
                resource = Resource(
                    file_path=file_path,
                    file_type=raw_res.get("file_type", ""),
                    token=raw_res.get("token", ""),
                    local_path=str(local_path),
                )
                resources.append(resource)

                if not local_path.exists():
                    missing_files.append(str(local_path))

            if missing_files and self.skip_missing_tasks:
                missing_task_count += 1
                continue

            tasks.append(
                Task(
                    task_id=raw_task["task_id"],
                    prompt_template=raw_task["prompt_template"],
                    resources=resources,
                )
            )
            for resource in resources:
                if resource.token:
                    self._token_to_resource[resource.token] = resource

        if not tasks:
            raise ValueError(
                f"No runnable tasks loaded from {self.dump_path}. "
                "Check data files or disable skip_missing_tasks."
            )

        if missing_task_count:
            print(
                f"[LocalProvider] Skipped {missing_task_count} task(s) because "
                "at least one resource file is missing."
            )

        return tasks

    def create_session(self) -> Session:
        self.session = Session(
            session_id=f"local-{uuid4()}",
            access_token="local",
            expires_in=0,
        )
        return self.session

    def get_next_task(self) -> Task:
        if self._cursor >= len(self._tasks):
            raise StopIteration("No more local tasks in dataset.")

        task = self._tasks[self._cursor]
        self._cursor += 1
        return task

    def download_file(self, download_token: str, save_path: str) -> str:
        resource = self._token_to_resource.get(download_token)
        if resource is None:
            raise FileNotFoundError(f"Unknown local resource token: {download_token}")

        source_path = Path(resource.local_path or self.resolve_resource_path(resource.file_path))
        if not source_path.exists():
            raise FileNotFoundError(
                f"Missing resource file for {resource.file_path}: {source_path}"
            )

        destination = Path(save_path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        if source_path.resolve() != destination.resolve():
            shutil.copy2(source_path, destination)
        return str(destination)

    def submit_task(
        self,
        task_id: str,
        answers: list[Any],
        thought_log: str,
        used_tools: list[str] | None = None,
    ) -> dict[str, Any]:
        if used_tools is None:
            used_tools = []
        if self.session is None:
            self.create_session()

        payload = {
            "submitted_at": datetime.now(timezone.utc).isoformat(),
            "session_id": self.session.session_id,
            "task_id": task_id,
            "answers": self._jsonable(answers),
            "thought_log": thought_log,
            "used_tools": used_tools,
        }

        self.submissions_path.parent.mkdir(parents=True, exist_ok=True)
        with self.submissions_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(payload, ensure_ascii=False) + "\n")

        return {
            "status": "saved",
            "mode": "local",
            "task_id": task_id,
            "path": str(self.submissions_path),
        }

    def _jsonable(self, value: Any) -> Any:
        if is_dataclass(value):
            return asdict(value)
        if isinstance(value, list):
            return [self._jsonable(item) for item in value]
        if isinstance(value, tuple):
            return [self._jsonable(item) for item in value]
        if isinstance(value, dict):
            return {key: self._jsonable(item) for key, item in value.items()}
        return value
