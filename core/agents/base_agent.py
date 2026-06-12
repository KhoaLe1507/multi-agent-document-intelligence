# core/agents/base_agent.py
from __future__ import annotations

import base64
import json
import re
from typing import Any, Optional, Type, TypeVar, get_args, get_origin

from google import genai
from google.genai import types
from pydantic import BaseModel

from ..config.settings import settings
from ..exceptions.agent_errors import LLMCommunicationError, SystemConfigError
from ..utils.logger import agent_logger
from ..utils.retry import llm_retry
from ..utils.trace_logger import tracer

T = TypeVar("T", bound=BaseModel)


class BaseAgent:
    """Base class that provides Gemini reasoning for all child agents."""

    def __init__(self, agent_name: str, temperature: float):
        if not settings.GEMINI_API_KEY:
            raise SystemConfigError("Missing GEMINI_API_KEY in .env")

        self.agent_name = agent_name
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
        self.model = settings.GEMINI_MODEL_NAME
        self.temperature = temperature

    @llm_retry()
    def call_llm(
        self,
        system_prompt: str,
        user_prompt: str | list,
        response_model: Optional[Type[T]] = None,
        image_base64: Optional[str] = None,
    ) -> T | str:
        agent_logger.debug(f"[{self.agent_name}] Dang phan tich bang Gemini...")

        contents = self._build_contents(user_prompt, image_base64)
        if response_model:
            system_instruction = self._structured_system_prompt(system_prompt, response_model)
            config = types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=self.temperature,
                response_mime_type="application/json",
                response_schema=response_model,
            )
        else:
            config = types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=self.temperature,
            )

        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=contents,
                config=config,
            )

            if response_model:
                parsed_res = self._parse_structured_response(response, response_model)

                agent_logger.success(
                    f"[{self.agent_name}] Da xuat du lieu chuan bang Gemini."
                )
                tracer.add_agent_span(
                    agent_name=self.agent_name,
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    response=parsed_res,
                )
                return parsed_res

            text_res = response.text or ""
            agent_logger.success(f"[{self.agent_name}] Da sinh xong phan hoi text.")
            tracer.add_agent_span(
                agent_name=self.agent_name,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                response=text_res,
            )
            return text_res

        except Exception as e:
            agent_logger.error(f"[{self.agent_name}] That bai khi goi Gemini: {str(e)}")
            raise LLMCommunicationError(
                f"Loi giao tiep Gemini tai {self.agent_name}: {str(e)}"
            )

    def _structured_system_prompt(self, system_prompt: str, response_model: Type[T]) -> str:
        field_names = ", ".join(response_model.model_fields.keys())
        return (
            f"{system_prompt}\n\n"
            "CRITICAL OUTPUT RULES:\n"
            "- Return exactly one valid JSON object and nothing else.\n"
            "- Do not use markdown fences, headings, YAML, or prose outside JSON.\n"
            "- Quote every JSON property name and every string value.\n"
            f"- The JSON object must match this Pydantic model: {response_model.__name__}.\n"
            f"- Required/allowed top-level keys: {field_names}."
        )

    def _parse_structured_response(self, response: Any, response_model: Type[T]) -> T:
        parsed = getattr(response, "parsed", None)
        if parsed is not None:
            if isinstance(parsed, response_model):
                return parsed
            return response_model.model_validate(parsed)

        raw_text = response.text or ""
        for candidate in self._structured_candidates(raw_text, response_model):
            try:
                return response_model.model_validate_json(candidate)
            except Exception:
                try:
                    return response_model.model_validate(json.loads(candidate))
                except Exception:
                    continue

        repaired = self._repair_field_header_response(raw_text, response_model)
        if repaired is not None:
            return response_model.model_validate(repaired)

        return response_model.model_validate_json(raw_text)

    def _structured_candidates(self, raw_text: str, response_model: Type[T]) -> list[str]:
        text = raw_text.strip()
        candidates = [text]

        fenced = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.IGNORECASE)
        candidates.append(fenced.strip())

        json_start = text.find("{")
        json_end = text.rfind("}")
        if json_start != -1 and json_end != -1 and json_end > json_start:
            candidates.append(text[json_start : json_end + 1].strip())

        fixed_candidates = []
        valid_fields = "|".join(re.escape(name) for name in response_model.model_fields)
        for candidate in candidates:
            fixed = re.sub(
                rf'([{{,]\s*)({valid_fields})(\s*:)',
                r'\1"\2"\3',
                candidate,
            )
            fixed_candidates.append(fixed)

        return list(dict.fromkeys(candidates + fixed_candidates))

    def _repair_field_header_response(
        self,
        raw_text: str,
        response_model: Type[T],
    ) -> dict[str, Any] | None:
        fields = list(response_model.model_fields.keys())
        if not fields:
            return None

        field_pattern = "|".join(re.escape(name) for name in fields)
        matches = list(
            re.finditer(
                rf'(?ms)(?:^|[{{,\n])\s*"?(?P<name>{field_pattern})"?\s*:?\s*',
                raw_text,
            )
        )
        if not matches:
            return None

        repaired: dict[str, Any] = {}
        for idx, match in enumerate(matches):
            name = match.group("name")
            start = match.end()
            end = matches[idx + 1].start() if idx + 1 < len(matches) else len(raw_text)
            value_text = raw_text[start:end].strip().strip(",").strip()
            value_text = value_text.removesuffix("}").strip().strip(",").strip()
            repaired[name] = self._coerce_repaired_value(
                value_text,
                response_model.model_fields[name].annotation,
            )

        return repaired

    def _coerce_repaired_value(self, value_text: str, annotation: Any) -> Any:
        if value_text == "":
            return None

        cleaned = value_text.strip()
        try:
            return json.loads(cleaned)
        except Exception:
            pass

        target = self._normalize_annotation(annotation)
        unquoted = cleaned.strip().strip('"').strip("'")

        if target is bool:
            return unquoted.lower() in {"true", "yes", "1"}
        if target is int:
            match = re.search(r"-?\d+", unquoted)
            return int(match.group(0)) if match else 0
        if target is float:
            match = re.search(r"-?\d+(?:\.\d+)?", unquoted)
            return float(match.group(0)) if match else 0.0
        if target is list:
            return [item.strip() for item in re.split(r"[,\n]+", unquoted) if item.strip()]
        if unquoted.lower() in {"null", "none"}:
            return None
        return unquoted

    def _normalize_annotation(self, annotation: Any) -> Any:
        origin = get_origin(annotation)
        if origin is list:
            return list
        if origin is None:
            return annotation
        args = [arg for arg in get_args(annotation) if arg is not type(None)]
        if len(args) == 1:
            return self._normalize_annotation(args[0])
        return annotation

    def _build_contents(
        self,
        user_prompt: str | list,
        image_base64: Optional[str] = None,
    ) -> list[Any]:
        if isinstance(user_prompt, str):
            contents: list[Any] = [types.Part.from_text(text=user_prompt)]
            if image_base64:
                contents.append(self._image_part_from_base64(image_base64))
            return contents

        contents = []
        for block in user_prompt:
            if block.get("type") == "text":
                contents.append(types.Part.from_text(text=block.get("text", "")))
            elif block.get("type") == "image_url":
                url = block.get("image_url", {}).get("url", "")
                image_part = self._image_part_from_data_url(url)
                if image_part is not None:
                    contents.append(image_part)
        return contents

    def _image_part_from_data_url(self, data_url: str) -> types.Part | None:
        match = re.match(r"^data:(?P<mime>[^;]+);base64,(?P<data>.+)$", data_url)
        if not match:
            return None

        return self._image_part_from_base64(
            match.group("data"),
            mime_type=match.group("mime"),
        )

    def _image_part_from_base64(
        self,
        image_base64: str,
        mime_type: str = "image/jpeg",
    ) -> types.Part:
        return types.Part.from_bytes(
            data=base64.b64decode(image_base64),
            mime_type=mime_type,
        )
