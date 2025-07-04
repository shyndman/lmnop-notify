"""Adds config flow for LMNOP Notifier."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_NAME
from homeassistant.helpers import selector

if TYPE_CHECKING:
    from homeassistant.data_entry_flow import FlowResult

from .const import CONF_ALERT_LIGHT_GROUP, DEFAULT_NAME, DOMAIN


class LmnopFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for LMNOP Notifier."""

    VERSION = 1

    async def async_step_user(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> FlowResult:
        """Handle a flow initialized by the user."""
        if user_input is not None:
            # Check if already configured with same name
            self._async_abort_entries_match({CONF_NAME: user_input[CONF_NAME]})

            return self.async_create_entry(
                title=user_input[CONF_NAME],
                data=user_input,
            )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_NAME,
                        default=DEFAULT_NAME,
                    ): selector.TextSelector(
                        selector.TextSelectorConfig(
                            type=selector.TextSelectorType.TEXT,
                        ),
                    ),
                    vol.Optional(
                        CONF_ALERT_LIGHT_GROUP,
                    ): selector.EntitySelector(
                        selector.EntitySelectorConfig(
                            domain="light",
                        ),
                    ),
                },
            ),
        )
