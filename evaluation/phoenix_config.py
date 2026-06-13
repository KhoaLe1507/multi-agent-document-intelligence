from __future__ import annotations

import contextlib
import json
import os
from typing import Any, Iterator


def create_phoenix_client(base_url: str | None = None):
    from phoenix.client import Client

    return Client(base_url=base_url) if base_url else Client()


def configure_phoenix_tracing(
    *,
    project_name: str = "ocr-multi-agent-evaluation",
    endpoint: str | None = None,
):
    try:
        from phoenix.otel import register
    except Exception:
        return None

    resolved_endpoint = endpoint or os.getenv("PHOENIX_COLLECTOR_ENDPOINT")
    kwargs = {
        "project_name": project_name,
        "batch": False,
        "auto_instrument": False,
    }
    if resolved_endpoint:
        kwargs["endpoint"] = resolved_endpoint
    return register(**kwargs)


@contextlib.contextmanager
def phoenix_span(name: str, attributes: dict[str, Any] | None = None) -> Iterator[Any]:
    try:
        from opentelemetry import trace
    except Exception:
        yield None
        return

    tracer = trace.get_tracer("ocr_multi_agents.evaluation")
    with tracer.start_as_current_span(name) as span:
        for key, value in (attributes or {}).items():
            try:
                span.set_attribute(key, _attribute_value(value))
            except Exception:
                span.set_attribute(key, str(value))
        yield span


def _attribute_value(value: Any) -> Any:
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return json.dumps(value, ensure_ascii=False, default=str)[:8000]
