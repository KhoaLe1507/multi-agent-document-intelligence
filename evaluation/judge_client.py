from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any

from google import genai
from google.genai import types

from core.config.settings import settings

from .evaluator_schemas import BinaryJudgeResult, fail_result


@dataclass
class JudgeClient:
    api_key: str | None = None
    model: str | None = None
    max_retries: int = 2

    def __post_init__(self):
        self.api_key = self.api_key or settings.GEMINI_API_KEY
        self.model = self.model or settings.GEMINI_MODEL_NAME
        self.client = genai.Client(api_key=self.api_key) if self.api_key else None

    def run_llm_judge(
        self,
        *,
        judge_name: str,
        system_prompt: str,
        input_payload: dict[str, Any],
        criterion_name: str,
    ) -> dict:
        if self.client is None:
            return fail_result(
                criterion_name,
                "Evaluation failed because GEMINI_API_KEY is not configured.",
                judge_name,
            )

        payload = {"criterion_name": criterion_name, **input_payload}
        prompt = json.dumps(payload, ensure_ascii=False, default=str)

        last_error = None
        for _ in range(self.max_retries + 1):
            try:
                response = self.client.models.generate_content(
                    model=self.model,
                    contents=[types.Part.from_text(text=prompt)],
                    config=types.GenerateContentConfig(
                        system_instruction=system_prompt,
                        temperature=0.0,
                        response_mime_type="application/json",
                    ),
                )
                parsed = self._parse_json(response.text or "")
                result = BinaryJudgeResult(
                    score=1 if parsed.get("score") == 1 else 0,
                    label="PASS" if parsed.get("score") == 1 else "FAIL",
                    explanation=str(parsed.get("explanation") or "No explanation returned."),
                    judge_name=judge_name,
                    criterion_name=criterion_name,
                )
                return result.model_dump()
            except Exception as exc:
                last_error = exc

        return fail_result(
            criterion_name,
            f"Evaluation failed because judge output was invalid: {last_error}",
            judge_name,
        )

    def _parse_json(self, text: str) -> dict[str, Any]:
        cleaned = text.strip()
        cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", cleaned, flags=re.IGNORECASE)
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            start = cleaned.find("{")
            end = cleaned.rfind("}")
            if start != -1 and end != -1 and end > start:
                return json.loads(cleaned[start : end + 1])
            raise


_DEFAULT_CLIENT: JudgeClient | None = None


def get_judge_client() -> JudgeClient:
    global _DEFAULT_CLIENT
    if _DEFAULT_CLIENT is None:
        _DEFAULT_CLIENT = JudgeClient()
    return _DEFAULT_CLIENT


def run_llm_judge(
    *,
    judge_name: str,
    system_prompt: str,
    input_payload: dict[str, Any],
    criterion_name: str,
) -> dict:
    return get_judge_client().run_llm_judge(
        judge_name=judge_name,
        system_prompt=system_prompt,
        input_payload=input_payload,
        criterion_name=criterion_name,
    )

