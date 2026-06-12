# tests/test_data_pipeline.py
import json
from pathlib import Path

import pytest

from core.parsers.file_router import parse_file
from dataProvider import ProviderService


SAMPLE_DATA_DIR = Path(__file__).parent / "sample_data"


class TestDataPipeline:
    def test_excel_to_markdown_chunking(self):
        excel_file = SAMPLE_DATA_DIR / "bang_tien_do.xlsx"

        if not excel_file.exists():
            pytest.skip(f"Missing sample file: {excel_file.name}")

        chunks = parse_file(str(excel_file))
        assert len(chunks) > 0
        assert chunks[0].chunk_type == "table"

    def test_pdf_to_vision_chunking(self):
        pdf_file = SAMPLE_DATA_DIR / "tai_lieu_dac_ta.pdf"

        if not pdf_file.exists():
            pytest.skip(f"Missing sample file: {pdf_file.name}")

        chunks = parse_file(str(pdf_file))
        assert len(chunks) > 0
        assert chunks[0].chunk_type == "image"

    def test_provider_loads_local_task_and_resource(self, tmp_path):
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        dump_path = data_dir / "dump.json"
        submissions_path = tmp_path / "submissions.jsonl"

        flattened_resource = data_dir / "Public_folder_muc_luc.pdf"
        flattened_resource.write_bytes(b"%PDF-1.4\n% local test")
        dump_path.write_text(
            json.dumps(
                {
                    "tasks": [
                        {
                            "task_id": "task_local_001",
                            "prompt_template": "Find the table of contents file.",
                            "resources": [
                                {
                                    "file_path": "Public/folder/muc_luc.pdf",
                                    "file_type": "pdf",
                                    "token": "local_token_1",
                                }
                            ],
                        }
                    ]
                }
            ),
            encoding="utf-8",
        )

        provider = ProviderService(
            dump_path=dump_path,
            data_dir=data_dir,
            submissions_path=submissions_path,
            skip_missing_tasks=False,
        )

        session = provider.create_session()
        task = provider.get_next_task()
        saved_path = provider.download_file(
            task.resources[0].token,
            tmp_path / "downloads" / task.resources[0].file_path,
        )
        result = provider.submit_task(
            task_id=task.task_id,
            answers=["answer"],
            thought_log="local thought log",
            used_tools=["LocalProvider"],
        )

        assert session.session_id.startswith("local-")
        assert task.task_id == "task_local_001"
        assert Path(saved_path).read_bytes() == flattened_resource.read_bytes()
        assert result["status"] == "saved"
        assert submissions_path.exists()
