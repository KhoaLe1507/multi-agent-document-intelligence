from __future__ import annotations

from typing import Any

from core.config.settings import settings
from dataProvider import ProviderService


def load_local_eval_samples(
    dump_path: str | None = None,
    data_dir: str | None = None,
    limit: int | None = None,
) -> list[dict[str, Any]]:
    provider = ProviderService(
        dump_path=dump_path or settings.DATA_DUMP_PATH,
        data_dir=data_dir or settings.DATA_DIR,
        submissions_path=settings.LOCAL_SUBMISSIONS_PATH,
        skip_missing_tasks=settings.LOCAL_SKIP_MISSING_TASKS,
    )
    samples = []
    for task in provider._tasks:
        samples.append(
            {
                "sample_id": task.task_id,
                "task_prompt": task.prompt_template,
                "prompt_template": task.prompt_template,
                "expected_task_type": None,
                "metadata": {
                    "resources": [
                        {
                            "file_path": res.file_path,
                            "file_type": res.file_type,
                            "token": res.token,
                            "local_path": res.local_path,
                        }
                        for res in task.resources
                    ],
                    "num_resources": len(task.resources),
                },
            }
        )
        if limit is not None and len(samples) >= limit:
            break
    return samples


def create_or_update_phoenix_dataset(
    client,
    samples: list[dict[str, Any]],
    dataset_name: str,
    dataset_description: str,
):
    inputs = samples
    outputs = [{"ground_truth": None} for _ in samples]
    metadata = [sample.get("metadata", {}) for sample in samples]
    return client.datasets.create_dataset(
        name=dataset_name,
        dataset_description=dataset_description,
        inputs=inputs,
        outputs=outputs,
        metadata=metadata,
    )
