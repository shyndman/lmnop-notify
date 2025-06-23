"""
LMNOP notification integration for Home Assistant.

For more details about this integration, please refer to
https://github.com/shyndman/lmnop-notifier
"""

from __future__ import annotations

import logging

from homeassistant.components import persistent_notification as pn
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_API_KEY, Platform
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.storage import Store
from homeassistant.helpers.typing import ConfigType

from .api import LmnopApiClient
from .const import ALERT_PRIORITIES, CONF_ALERT_LIGHT_GROUP, DOMAIN
from .lights import LightStateManager

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.NOTIFY, Platform.SENSOR, Platform.BINARY_SENSOR]

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)

STORAGE_VERSION = 1
STORAGE_KEY = f"{DOMAIN}_alerts"


class AlertTracker:
    """Tracks active HIGH/CRITICAL notifications and manages light alerts."""

    def __init__(
        self, hass: HomeAssistant, entry: ConfigEntry, light_manager: LightStateManager
    ) -> None:
        """Initialize the alert tracker."""
        self.hass = hass
        self.entry = entry
        self.light_manager = light_manager
        self._active_alerts: set[str] = set()
        self._store = Store(hass, STORAGE_VERSION, STORAGE_KEY)

    async def load_alert_data(self) -> dict:
        """Load alert data from storage."""
        return await self._store.async_load() or {"active_alerts": []}

    async def save_alert_data(self) -> None:
        """Save alert data to storage."""
        await self._store.async_save({"active_alerts": list(self._active_alerts)})

    async def check_existing_notifications(self) -> None:
        """Check for existing LMNOP notifications on startup."""
        try:
            # Load saved alert data
            data = await self.load_alert_data()
            saved_alerts = set(data.get("active_alerts", []))

            # Get current persistent notifications
            notifications = self.hass.data.get("persistent_notification", {})
            current_lmnop_alerts = {
                notification_id
                for notification_id in notifications
                if notification_id.startswith(f"{DOMAIN}_")
            }

            # Find alerts that still exist
            self._active_alerts = saved_alerts & current_lmnop_alerts

            # If we have active alerts, ensure lights are in alert mode
            if self._active_alerts:
                light_group = self.entry.data.get(CONF_ALERT_LIGHT_GROUP)
                if light_group and not self.light_manager.is_alert_active:
                    _LOGGER.info(
                        "Found %d existing alerts, activating light alert mode",
                        len(self._active_alerts),
                    )
                    # Don't save states again, just set to alert mode
                    await self._activate_light_alert(light_group, save_states=False)

            # Clean up any alerts that no longer exist
            if saved_alerts != self._active_alerts:
                await self.save_alert_data()

        except Exception as err:
            _LOGGER.error("Error checking existing notifications: %s", err)

    async def add_alert(self, notification_id: str, priority: str) -> bool:
        """Add a HIGH/CRITICAL alert and potentially activate lights."""
        if priority not in ALERT_PRIORITIES:
            return False

        was_empty = len(self._active_alerts) == 0
        self._active_alerts.add(notification_id)
        await self.save_alert_data()

        # Activate lights if this is the first alert
        if was_empty:
            light_group = self.entry.data.get(CONF_ALERT_LIGHT_GROUP)
            if light_group:
                return await self._activate_light_alert(light_group, save_states=True)

        return True

    async def remove_alert(self, notification_id: str) -> bool:
        """Remove an alert and potentially deactivate lights."""
        if notification_id not in self._active_alerts:
            return False

        self._active_alerts.discard(notification_id)
        await self.save_alert_data()

        # Deactivate lights if this was the last alert
        if len(self._active_alerts) == 0:
            return await self.light_manager.restore_light_states()

        return True

    async def _activate_light_alert(self, light_group: str, save_states: bool) -> bool:
        """Activate light alert mode."""
        try:
            if save_states:
                return await self.light_manager.save_light_states_and_set_alert(
                    light_group
                )
            # Just set to alert mode without saving states (for startup recovery)
            entity_ids = self.light_manager._get_light_entities(light_group)
            rgb_lights = self.light_manager._validate_rgb_support(entity_ids)
            if rgb_lights:
                await self.hass.services.async_call(
                    "light",
                    "turn_on",
                    {
                        "entity_id": rgb_lights,
                        "rgb_color": [255, 0, 0],
                        "brightness": 255,
                    },
                    blocking=True,
                )
                self.light_manager._alert_active = True
                return True
            return False
        except Exception as err:
            _LOGGER.error("Failed to activate light alert: %s", err)
            return False

    @callback
    def handle_notification_update(self, update_type: str, notifications: dict) -> None:
        """Handle persistent notification updates."""
        if update_type == "removed":
            for notification_id in notifications:
                if notification_id.startswith(f"{DOMAIN}_"):
                    # Schedule the async operation
                    self.hass.async_create_task(self.remove_alert(notification_id))

    @property
    def active_alert_count(self) -> int:
        """Return the number of active alerts."""
        return len(self._active_alerts)

    @property
    def is_alert_active(self) -> bool:
        """Return whether any alerts are active."""
        return len(self._active_alerts) > 0


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the LMNOP component."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up LMNOP from a config entry."""
    # Initialize the API client
    api_client = LmnopApiClient(
        api_key=entry.data[CONF_API_KEY],
        session=async_get_clientsession(hass),
    )

    # Initialize light state manager
    light_manager = LightStateManager(hass)

    # Initialize alert tracking
    alert_tracker = AlertTracker(hass, entry, light_manager)

    # Store components
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        "api_client": api_client,
        "light_manager": light_manager,
        "alert_tracker": alert_tracker,
    }

    # Set up persistent notification listener
    pn.async_register_callback(hass, alert_tracker.handle_notification_update)

    # Check for existing notifications on startup
    await alert_tracker.check_existing_notifications()

    # Forward the config entry setup to notify platform
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Handle removal of an entry."""
    # Unload platforms
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    # Clean up stored data
    if unload_ok and entry.entry_id in hass.data.get(DOMAIN, {}):
        entry_data = hass.data[DOMAIN].pop(entry.entry_id)

        # Clear light alert state if active
        if "light_manager" in entry_data:
            light_manager = entry_data["light_manager"]
            if light_manager.is_alert_active:
                await light_manager.restore_light_states()

    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry."""
    await hass.config_entries.async_reload(entry.entry_id)
