"""LMNOP platform for notify component."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components import persistent_notification as pn
from homeassistant.components.notify import NotifyEntity, NotifyEntityFeature
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import dt as dt_util

from .api import LmnopApiClient
from .const import (
    ALERT_PRIORITIES,
    ATTR_PRIORITY,
    DEFAULT_NAME,
    DOMAIN,
    PRIORITY_CRITICAL,
    PRIORITY_DEBUG,
    PRIORITY_HIGH,
    PRIORITY_LOW,
    PRIORITY_MEDIUM,
)

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
    
    async_add_entities([LmnopNotifyEntity(
        hass=hass,
        api_client=api_client,
        alert_tracker=alert_tracker,
        name=name,
        unique_id=entry.entry_id,
    )])


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

    async def async_send_message(self, message: str, title: str | None = None, **kwargs) -> None:
        """Send a message."""
        # Extract priority from service call data (if provided)
        data = kwargs.get("data", {})
        priority = data.get(ATTR_PRIORITY, PRIORITY_MEDIUM)
        
        # Validate priority
        valid_priorities = [PRIORITY_CRITICAL, PRIORITY_HIGH, PRIORITY_MEDIUM, PRIORITY_LOW, PRIORITY_DEBUG]
        if priority not in valid_priorities:
            _LOGGER.warning("Invalid priority '%s', using MEDIUM", priority)
            priority = PRIORITY_MEDIUM

        # Create unique notification ID for persistent notification tracking
        notification_id = f"{DOMAIN}_{self._attr_unique_id}_{dt_util.utcnow().timestamp()}"
        
        # Log the notification (barebones implementation)
        _LOGGER.info(
            "Sending notification: priority=%s, title=%s, message=%s",
            priority,
            title,
            message[:50] + "..." if len(message) > 50 else message
        )

        try:
            # Send via API client
            await self._api_client.send_notification({
                "message": message,
                "title": title,
                "priority": priority,
                "notification_id": notification_id,
            })
            
            # Create persistent notification for acknowledgment tracking
            pn.async_create(
                self.hass,
                message=message,
                title=title or f"{self._attr_name} Notification",
                notification_id=notification_id,
            )
            
            # Handle light alerts for HIGH/CRITICAL priorities
            if priority in ALERT_PRIORITIES:
                await self._alert_tracker.add_alert(notification_id, priority)
                _LOGGER.info("Added light alert for %s priority notification", priority)
            
            _LOGGER.debug("Notification sent successfully with ID: %s", notification_id)
            
        except Exception as err:
            _LOGGER.error("Failed to send notification: %s", err)
            raise HomeAssistantError(f"Failed to send notification: {err}") from err

