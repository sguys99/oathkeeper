"""Workflow registry — select and instantiate analysis workflows."""

from enum import StrEnum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from backend.app.agent.workflows.base import Workflow


class WorkflowType(StrEnum):
    STATIC = "static"
    REACT = "react"


def get_workflow(workflow_type: WorkflowType | str) -> "Workflow":
    """Return the appropriate Workflow instance for the given type."""
    wf = WorkflowType(workflow_type)
    if wf == WorkflowType.STATIC:
        from backend.app.agent.workflows.static import StaticWorkflow

        return StaticWorkflow()
    from backend.app.agent.workflows.react import ReactWorkflow

    return ReactWorkflow()
