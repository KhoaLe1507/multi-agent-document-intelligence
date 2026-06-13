import os
from unittest.mock import MagicMock

os.environ.setdefault("GEMINI_API_KEY", "dummy")

from core.workflows.organize_workflow import OrganizeWorkflow
from core.workflows.qa_workflow import QAWorkflow


def test_workflows_compile_to_langgraph_state_graphs():
    provider = MagicMock()

    qa_workflow = QAWorkflow(provider)
    organize_workflow = OrganizeWorkflow(provider)

    assert type(qa_workflow.graph.graph).__name__ == "CompiledStateGraph"
    assert type(organize_workflow.graph.graph).__name__ == "CompiledStateGraph"
