"""Step type constants for hierarchical agent logging."""

from enum import StrEnum


class StepType(StrEnum):
    ORCHESTRATOR_REASONING = "orchestrator_reasoning"
    ORCHESTRATOR_TOOL_CALL = "orchestrator_tool_call"
    WORKER_START = "worker_start"
    WORKER_RESULT = "worker_result"
    REASONING = "reasoning"
    TOOL_CALL = "tool_call"
    OBSERVATION = "observation"
