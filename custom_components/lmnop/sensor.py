"""LMNOP sensor platform for alert status."""

from __future__ import annotations

import logging

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DEFAULT_NAME, DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up LMNOP sensor entities."""
    entry_data = hass.data[DOMAIN][entry.entry_id]
    alert_tracker = entry_data["alert_tracker"]
    light_manager = entry_data["light_manager"]
    name = entry.data.get(CONF_NAME, DEFAULT_NAME)

    entities = [
        LmnopAlertStatusSensor(alert_tracker, light_manager, name, entry.entry_id),
    ]

    async_add_entities(entities)


class LmnopAlertStatusSensor(SensorEntity):
    """Sensor showing LMNOP alert status."""

    def __init__(self, alert_tracker, light_manager, name: str, unique_id: str) -> None:
        """Initialize the alert status sensor."""
        self._alert_tracker = alert_tracker
        self._light_manager = light_manager
        self._attr_name = f"{name} Alert Status"
        self._attr_unique_id = f"{unique_id}_alert_status"
        self._attr_icon = "mdi:alert-circle"

    @property
    def native_value(self) -> str:
        """Return the state of the sensor."""
        return "Active" if self._alert_tracker.is_alert_active else "Clear"

    @property
    def extra_state_attributes(self) -> dict[str, any]:
        """Return additional state attributes."""
        return {
            "active_alert_count": self._alert_tracker.active_alert_count,
            "lights_in_alert_mode": self._light_manager.get_alert_light_entities(),
            "alert_light_count": self._light_manager.alert_light_count,
        }

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return True


