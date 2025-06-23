"""Barebones Notification API Client."""

from __future__ import annotations

import logging
from typing import Any

import aiohttp

_LOGGER = logging.getLogger(__name__)


class LmnopApiClientError(Exception):
    """Exception to indicate a general API error."""


class LmnopApiClient:
    """Barebones notification API client - just logs notifications."""

    def __init__(
        self,
        api_key: str,
        session: aiohttp.ClientSession,
    ) -> None:
        """Initialize the API client."""
        self._api_key = api_key
        self._session = session

    async def validate_credentials(self) -> bool:
        """Validate the API credentials - always succeeds for barebones implementation."""
        _LOGGER.debug("Validating credentials (barebones - always succeeds)")
        return True

    async def send_notification(self, notification_data: dict[str, Any]) -> Any:
        """Send a notification - barebones implementation just logs."""
        _LOGGER.info(
            "BAREBONES: Would send notification - %s",
            {
                "priority": notification_data.get("priority"),
                "title": notification_data.get("title"),
                "message": notification_data.get("message", "")[:100] + "..."
                if len(notification_data.get("message", "")) > 100
                else notification_data.get("message", ""),
                "notification_id": notification_data.get("notification_id"),
            }
        )

        # Return a mock successful response
        return {"success": True, "notification_id": notification_data.get("notification_id")}

