"""Workflow protocol — common interface for analysis execution strategies."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable


class Workflow(Protocol):
    """Common interface for static and react analysis workflows.

    The service handles deal lookup, previous result deletion, error handling,
    and result persistence. The workflow only handles graph building, execution,
    and result extraction.
    """

    async def execute(
        self,
        deal_id: uuid.UUID,
        deal_input: str,
        on_progress: Callable[[str], Awaitable[None]],
    ) -> dict:
        """Run the analysis and return a result dict.

        Expected return keys: total_score, verdict, scores, resource_estimate,
        risks, risk_interdependencies, similar_projects, final_report,
        structured_deal.
        """
        ...
