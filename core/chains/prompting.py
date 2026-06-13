from __future__ import annotations

from typing import Any


def render_prompt_template(template: str, **values: Any) -> str:
    """Render a prompt through LangChain PromptTemplate when available."""
    try:
        from langchain_core.prompts import PromptTemplate
    except ImportError:
        return template.format(**values)

    return PromptTemplate.from_template(template).format(**values)
