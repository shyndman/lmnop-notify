"""Light state management for LMNOP alerts."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.light import DOMAIN as LIGHT_DOMAIN
from homeassistant.components.light import ColorMode
from homeassistant.core import HomeAssistant

from .const import ALERT_BRIGHTNESS, ALERT_RGB_COLOR

_LOGGER = logging.getLogger(__name__)


class LightStateManager:
    """Manages light states for alert notifications."""

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize the light state manager."""
        self.hass = hass
        self._saved_states: dict[str, dict[str, Any]] = {}
        self._alert_active = False

    def _get_light_entities(self, light_group_id: str) -> list[str]:
        """Get individual light entities from a light group."""
        if not light_group_id:
            return []

        # Check if it's a group
        if light_group_id.startswith("light."):
            group_state = self.hass.states.get(light_group_id)
            if group_state is None:
                _LOGGER.warning("Light group %s not found", light_group_id)
                return []

            # If it's a group, get member entities
            entity_ids = group_state.attributes.get("entity_id")
            if entity_ids:
                # Group has member entities
                return entity_ids if isinstance(entity_ids, list) else [entity_ids]
            # It's a single light entity
            return [light_group_id]

        return []

    def _validate_rgb_support(self, entity_ids: list[str]) -> list[str]:
        """Filter entities to only include those that support RGB color."""
        rgb_lights = []

        for entity_id in entity_ids:
            state = self.hass.states.get(entity_id)
            if state is None:
                _LOGGER.warning("Light entity %s not found", entity_id)
                continue

            supported_color_modes = state.attributes.get("supported_color_modes", [])
            if ColorMode.RGB in supported_color_modes:
                rgb_lights.append(entity_id)
            else:
                _LOGGER.warning(
                    "Light %s does not support RGB color mode, skipping", entity_id
                )

        return rgb_lights

    def _save_light_state(self, entity_id: str) -> dict[str, Any] | None:
        """Save the current state of a light."""
        state = self.hass.states.get(entity_id)
        if state is None:
            return None

        saved_state = {
            "entity_id": entity_id,
            "state": state.state,
        }

        # Save relevant attributes
        attributes = state.attributes
        for attr in ["brightness", "rgb_color", "color_temp", "effect"]:
            if attr in attributes:
                saved_state[attr] = attributes[attr]

        return saved_state

    async def save_light_states_and_set_alert(self, light_group_id: str) -> bool:
        """Save current light states and set them to alert mode."""
        if self._alert_active:
            _LOGGER.debug("Alert already active, not saving states again")
            return False

        entity_ids = self._get_light_entities(light_group_id)
        if not entity_ids:
            _LOGGER.warning("No light entities found for group %s", light_group_id)
            return False

        rgb_lights = self._validate_rgb_support(entity_ids)
        if not rgb_lights:
            _LOGGER.warning("No RGB-capable lights found in group %s", light_group_id)
            return False

        # Save current states
        self._saved_states = {}
        for entity_id in rgb_lights:
            saved_state = self._save_light_state(entity_id)
            if saved_state:
                self._saved_states[entity_id] = saved_state

        if not self._saved_states:
            _LOGGER.warning("No light states could be saved")
            return False

        # Set lights to alert mode
        try:
            await self.hass.services.async_call(
                LIGHT_DOMAIN,
                "turn_on",
                {
                    "entity_id": rgb_lights,
                    "rgb_color": ALERT_RGB_COLOR,
                    "brightness": ALERT_BRIGHTNESS,
                },
                blocking=True,
            )
            self._alert_active = True
            _LOGGER.info("Set %d lights to alert mode", len(rgb_lights))
            return True

        except Exception as err:
            _LOGGER.error("Failed to set lights to alert mode: %s", err)
            self._saved_states = {}
            return False

    async def restore_light_states(self) -> bool:
        """Restore lights to their previous states."""
        if not self._alert_active or not self._saved_states:
            _LOGGER.debug("No alert active or no saved states to restore")
            return False

        try:
            # Restore each light individually
            for entity_id, saved_state in self._saved_states.items():
                service_data = {"entity_id": entity_id}

                if saved_state["state"] == "off":
                    # Turn light off
                    await self.hass.services.async_call(
                        LIGHT_DOMAIN,
                        "turn_off",
                        service_data,
                        blocking=True,
                    )
                else:
                    # Turn light on with previous settings
                    if "brightness" in saved_state:
                        service_data["brightness"] = saved_state["brightness"]

                    # Set color attributes - prioritize color_temp over rgb_color to avoid conflicts
                    # (color_temp is more commonly used for everyday lighting)
                    if "color_temp" in saved_state:
                        service_data["color_temp"] = saved_state["color_temp"]
                        _LOGGER.debug(
                            "Restoring %s with color_temp: %s",
                            entity_id,
                            saved_state["color_temp"],
                        )
                    elif "rgb_color" in saved_state:
                        service_data["rgb_color"] = saved_state["rgb_color"]
                        _LOGGER.debug(
                            "Restoring %s with rgb_color: %s",
                            entity_id,
                            saved_state["rgb_color"],
                        )

                    if "effect" in saved_state:
                        service_data["effect"] = saved_state["effect"]

                    await self.hass.services.async_call(
                        LIGHT_DOMAIN,
                        "turn_on",
                        service_data,
                        blocking=True,
                    )

            _LOGGER.info(
                "Restored %d lights to previous states", len(self._saved_states)
            )
            self._saved_states = {}
            self._alert_active = False
            return True

        except Exception as err:
            _LOGGER.error("Failed to restore light states: %s", err)
            return False

    @property
    def is_alert_active(self) -> bool:
        """Return whether alert mode is currently active."""
        return self._alert_active

    @property
    def alert_light_count(self) -> int:
        """Return the number of lights currently in alert mode."""
        return len(self._saved_states) if self._alert_active else 0

    def get_alert_light_entities(self) -> list[str]:
        """Return list of light entities currently in alert mode."""
        return list(self._saved_states.keys()) if self._alert_active else []

    def clear_alert_state(self) -> None:
        """Clear alert state without restoring lights (for cleanup)."""
        self._saved_states = {}
        self._alert_active = False
