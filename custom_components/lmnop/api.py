"""Barebones Notification API Client."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    import aiohttp

_LOGGER = logging.getLogger(__name__)

# Maximum message length for log truncation
MAX_MESSAGE_LENGTH = 100


class LmnopApiClientError(Exception):
    """Exception to indicate a general API error."""


class LmnopApiClient:
    """Barebones notification API client - just logs notifications."""

    def __init__(
        self,
        api_key: str,
        session: aiohttp.ClientSession,  # type: ignore[name-defined]
    ) -> None:
        """Initialize the API client."""
        self._api_key = api_key
        self._session = session

    async def validate_credentials(self) -> bool:
        """Validate API credentials - always succeeds for barebones implementation."""
        _LOGGER.debug("Validating credentials (barebones - always succeeds)")
        return True

    async def send_notification(self, notification_data: dict[str, Any]) -> Any:
        """Send a notification - barebones implementation just logs."""
        _LOGGER.info(
            "BAREBONES: Would send notification - %s",
            {
                "priority": notification_data.get("priority"),
                "title": notification_data.get("title"),
                "message": (
                    notification_data.get("message", "")[:MAX_MESSAGE_LENGTH] + "..."
                    if len(notification_data.get("message", "")) > MAX_MESSAGE_LENGTH
                    else notification_data.get("message", "")
                ),
                "notification_id": notification_data.get("notification_id"),
            },
        )

        # Return a mock successful response
        return {
            "success": True,
            "notification_id": notification_data.get("notification_id"),
        }
