"""Slack webhook client — fire-and-forget notifications."""

from __future__ import annotations

import logging

import httpx

from backend.app.utils.settings import get_settings

logger = logging.getLogger(__name__)

_VERDICT_EMOJI: dict[str, str] = {
    "go": ":large_green_circle:",
    "conditional_go": ":large_yellow_circle:",
    "no_go": ":red_circle:",
    "hold": ":white_circle:",
}


async def send_analysis_notification(
    deal_name: str,
    verdict: str,
    total_score: float,
    notion_page_url: str | None = None,
) -> bool:
    """Post an analysis completion summary to the configured Slack webhook.

    Returns True on success, False on failure (non-critical, logged only).
    """
    settings = get_settings()
    if not settings.slack_webhook_url:
        logger.warning("Slack webhook URL not configured — skipping notification")
        return False

    key = verdict.lower().replace(" ", "_").replace("-", "_")
    emoji = _VERDICT_EMOJI.get(key, ":question:")

    lines = [
        f"{emoji} *OathKeeper 분석 완료*",
        f"*Deal:* {deal_name}",
        f"*판정:* {verdict}",
        f"*점수:* {total_score:.1f} / 100",
    ]
    if notion_page_url:
        lines.append(f"<{notion_page_url}|Notion에서 보기>")

    payload = {"text": "\n".join(lines)}

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(settings.slack_webhook_url, json=payload)
            resp.raise_for_status()
            return True
    except httpx.HTTPError:
        logger.exception("Failed to send Slack notification")
        return False
