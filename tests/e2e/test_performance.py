"""E2E: Performance tests — response time and failure rate.

Requires: DATABASE_URL, OPENAI_API_KEY or ANTHROPIC_API_KEY, PINECONE_API_KEY
Run with: uv run pytest -m e2e -v --timeout=200

Note: test_failure_rate_below_5_percent is marked @slow and takes ~60 min
with real LLM calls. Run separately: uv run pytest -m "e2e and slow"
"""

import logging
import time

import pytest

from tests.e2e.conftest import poll_until_complete
from tests.fixtures.sample_deals import CLEAR_GO_DEAL

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.e2e, pytest.mark.asyncio]


class TestPerformance:
    """MVP performance criteria validation."""

    @pytest.mark.timeout(180)
    async def test_analysis_completes_within_3_minutes(
        self,
        e2e_client,
        ensure_seed_data,
    ):
        """A standard deal analysis must complete in under 3 minutes."""
        start = time.monotonic()

        resp = await e2e_client.post("/api/deals/", json=CLEAR_GO_DEAL)
        deal_id = resp.json()["id"]

        resp = await e2e_client.post(f"/api/deals/{deal_id}/analyze")
        assert resp.status_code == 202

        deal = await poll_until_complete(e2e_client, deal_id)
        elapsed = time.monotonic() - start

        assert deal["status"] == "completed"
        logger.info("Analysis completed in %.1f seconds", elapsed)
        assert elapsed < 180, f"Analysis took {elapsed:.1f}s (limit: 180s)"

    @pytest.mark.slow
    @pytest.mark.timeout(600)
    async def test_failure_rate_below_5_percent(
        self,
        e2e_client,
        ensure_seed_data,
    ):
        """Run 20 analyses sequentially; failure rate must be ≤ 5%.

        This test is slow (~60 min) and expensive ($2-4 in LLM costs).
        Only run in nightly CI: ``uv run pytest -m "e2e and slow"``
        """
        total = 20
        failures = 0

        for i in range(total):
            resp = await e2e_client.post(
                "/api/deals/",
                json={
                    "title": f"성능테스트 딜 #{i + 1}",
                    "raw_input": CLEAR_GO_DEAL["raw_input"],
                },
            )
            deal_id = resp.json()["id"]

            resp = await e2e_client.post(f"/api/deals/{deal_id}/analyze")
            assert resp.status_code == 202

            deal = await poll_until_complete(e2e_client, deal_id, timeout=180)
            if deal["status"] != "completed":
                failures += 1
                logger.warning("Run %d/%d FAILED", i + 1, total)
            else:
                logger.info("Run %d/%d OK", i + 1, total)

        failure_rate = failures / total
        logger.info(
            "Failure rate: %d/%d = %.1f%%",
            failures,
            total,
            failure_rate * 100,
        )
        assert (
            failure_rate <= 0.05
        ), f"Failure rate {failure_rate:.0%} exceeds 5% threshold ({failures}/{total} failed)"
