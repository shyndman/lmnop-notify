"""LMNOP platform for notify component."""

from __future__ import annotations

import logging
import re
from typing import TYPE_CHECKING, Any

from homeassistant.components import persistent_notification as pn
from homeassistant.components.notify import NotifyEntity, NotifyEntityFeature
from homeassistant.const import CONF_NAME
from homeassistant.exceptions import HomeAssistantError
from homeassistant.util import dt as dt_util

from .const import (
    ALERT_PRIORITIES,
    DEFAULT_NAME,
    DOMAIN,
    PRIORITY_CRITICAL,
    PRIORITY_DEBUG,
    PRIORITY_HIGH,
    PRIORITY_LOW,
    PRIORITY_REGULAR,
)

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from .api import LmnopApiClient

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up notify entity."""
    entry_data = hass.data[DOMAIN][entry.entry_id]
    api_client = entry_data["api_client"]
    alert_tracker = entry_data["alert_tracker"]
    name = entry.data.get(CONF_NAME, DEFAULT_NAME)

    async_add_entities(
        [
            LmnopNotifyEntity(
                hass=hass,
                api_client=api_client,
                alert_tracker=alert_tracker,
                name=name,
                unique_id=entry.entry_id,
            )
        ]
    )


class LmnopNotifyEntity(NotifyEntity):
    """Implement the notification entity for LMNOP notifier."""

    _attr_supported_features = NotifyEntityFeature.TITLE

    def __init__(
        self,
        hass: HomeAssistant,
        api_client: LmnopApiClient,
        alert_tracker: Any,
        name: str,
        unique_id: str,
    ) -> None:
        """Initialize the notification entity."""
        self._api_client = api_client
        self._alert_tracker = alert_tracker
        self._attr_name = name
        self._attr_unique_id = unique_id

    def _parse_priority_from_title(self, title: str | None) -> tuple[str, str | None]:
        """Parse priority from title prefix and return (priority, clean_title)."""
        if not title:
            return PRIORITY_REGULAR, title

        # Match [priority] at the start of title
        match = re.match(r"^\[(\w+)\]\s*(.*)$", title)
        if not match:
            return PRIORITY_REGULAR, title

        priority_str = match.group(1).lower()
        clean_title = match.group(2) or None

        # Validate priority
        valid_priorities = [
            PRIORITY_CRITICAL,
            PRIORITY_HIGH,
            PRIORITY_REGULAR,
            PRIORITY_LOW,
            PRIORITY_DEBUG,
        ]

        if priority_str in valid_priorities:
            return priority_str, clean_title
        _LOGGER.warning(
            "Invalid priority '[%s]' in title, using REGULAR priority", priority_str
        )
        return PRIORITY_REGULAR, clean_title

    async def async_send_message(
        self, message: str, title: str | None = None, **kwargs
    ) -> None:
        """Send a message."""
        # Parse priority from title prefix
        priority, display_title = self._parse_priority_from_title(title)

        # Create unique notification ID for persistent notification tracking
        notification_id = (
            f"{DOMAIN}_{self._attr_unique_id}_{dt_util.utcnow().timestamp()}"
        )

        # Log the notification (barebones implementation)
        _LOGGER.info(
            "Sending notification: priority=%s, title=%s, message=%s",
            priority,
            title,
            message[:50] + "..." if len(message) > 50 else message,
        )

        try:
            # Send via API client
            await self._api_client.send_notification(
                {
                    "message": message,
                    "title": display_title,
                    "priority": priority,
                    "notification_id": notification_id,
                }
            )

            # Create persistent notification for acknowledgment tracking
            pn.async_create(
                self.hass,
                message=message,
                title=display_title or f"{self._attr_name} Notification",
                notification_id=notification_id,
            )

            # Handle light alerts for HIGH/CRITICAL priorities
            if priority in ALERT_PRIORITIES:
                await self._alert_tracker.add_alert(notification_id, priority)
                _LOGGER.info("Added light alert for %s priority notification", priority)

            _LOGGER.debug("Notification sent successfully with ID: %s", notification_id)

        except Exception as err:
            _LOGGER.exception("Failed to send notification")
            msg = f"Failed to send notification: {err}"
            raise HomeAssistantError(msg) from err
