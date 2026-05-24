"""Config and options flow for the Lightsouts motorsport calendar."""
from __future__ import annotations

import asyncio
import logging
from typing import Any

import aiohttp
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.config_entries import ConfigEntry, ConfigFlowResult, OptionsFlow
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import (
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    SelectOptionDict,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
)

from .const import (
    ALL_SESSION_TYPES,
    API_SERIES_INDEX,
    CONF_SERIES,
    CONF_SESSION_TYPES,
    CONF_UPDATE_INTERVAL_HOURS,
    DEFAULT_SESSION_TYPES,
    DEFAULT_UPDATE_INTERVAL_HOURS,
    DOMAIN,
    MAX_UPDATE_INTERVAL_HOURS,
    MIN_UPDATE_INTERVAL_HOURS,
    REQUEST_TIMEOUT,
)

_LOGGER = logging.getLogger(__name__)


async def _fetch_series_options(hass) -> list[SelectOptionDict]:
    """Fetch the available motorsport series so the user can choose."""
    session = async_get_clientsession(hass)
    async with asyncio.timeout(REQUEST_TIMEOUT):
        async with session.get(API_SERIES_INDEX) as resp:
            resp.raise_for_status()
            data = await resp.json()
    options = [
        SelectOptionDict(value=s["slug"], label=s.get("name") or s["slug"])
        for s in data
        if s.get("slug")
    ]
    options.sort(key=lambda o: o["label"].lower())
    return options


def _interval_selector() -> NumberSelector:
    return NumberSelector(
        NumberSelectorConfig(
            min=MIN_UPDATE_INTERVAL_HOURS,
            max=MAX_UPDATE_INTERVAL_HOURS,
            step=1,
            mode=NumberSelectorMode.BOX,
            unit_of_measurement="h",
        )
    )


def _series_selector(options: list[SelectOptionDict]) -> SelectSelector:
    return SelectSelector(
        SelectSelectorConfig(
            options=options,
            multiple=True,
            mode=SelectSelectorMode.DROPDOWN,
        )
    )


def _session_type_selector() -> SelectSelector:
    return SelectSelector(
        SelectSelectorConfig(
            options=list(ALL_SESSION_TYPES),
            multiple=True,
            mode=SelectSelectorMode.LIST,
            translation_key=CONF_SESSION_TYPES,
        )
    )


class LightsoutsConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Initial setup flow."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")

        try:
            options = await _fetch_series_options(self.hass)
        except (aiohttp.ClientError, asyncio.TimeoutError) as err:
            _LOGGER.warning("Could not fetch series list: %s", err)
            return self.async_abort(reason="cannot_connect")

        if user_input is not None:
            return self.async_create_entry(
                title="Lightsouts",
                data={},
                options={
                    CONF_SERIES: user_input[CONF_SERIES],
                    CONF_SESSION_TYPES: user_input[CONF_SESSION_TYPES],
                    CONF_UPDATE_INTERVAL_HOURS: int(
                        user_input[CONF_UPDATE_INTERVAL_HOURS]
                    ),
                },
            )

        default_series = [o["value"] for o in options]
        schema = vol.Schema(
            {
                vol.Required(CONF_SERIES, default=default_series): _series_selector(
                    options
                ),
                vol.Required(
                    CONF_SESSION_TYPES, default=DEFAULT_SESSION_TYPES
                ): _session_type_selector(),
                vol.Required(
                    CONF_UPDATE_INTERVAL_HOURS,
                    default=DEFAULT_UPDATE_INTERVAL_HOURS,
                ): _interval_selector(),
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema)

    @staticmethod
    @callback
    def async_get_options_flow(entry: ConfigEntry) -> OptionsFlow:
        return LightsoutsOptionsFlow(entry)


class LightsoutsOptionsFlow(OptionsFlow):
    """Lets the user change series / session types / interval after setup."""

    def __init__(self, entry: ConfigEntry) -> None:
        self.entry = entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        try:
            options = await _fetch_series_options(self.hass)
        except (aiohttp.ClientError, asyncio.TimeoutError) as err:
            _LOGGER.warning("Could not fetch series list: %s", err)
            return self.async_abort(reason="cannot_connect")

        current = self.entry.options
        if user_input is not None:
            return self.async_create_entry(
                title="",
                data={
                    CONF_SERIES: user_input[CONF_SERIES],
                    CONF_SESSION_TYPES: user_input[CONF_SESSION_TYPES],
                    CONF_UPDATE_INTERVAL_HOURS: int(
                        user_input[CONF_UPDATE_INTERVAL_HOURS]
                    ),
                },
            )

        schema = vol.Schema(
            {
                vol.Required(
                    CONF_SERIES,
                    default=current.get(
                        CONF_SERIES, [o["value"] for o in options]
                    ),
                ): _series_selector(options),
                vol.Required(
                    CONF_SESSION_TYPES,
                    default=current.get(CONF_SESSION_TYPES, DEFAULT_SESSION_TYPES),
                ): _session_type_selector(),
                vol.Required(
                    CONF_UPDATE_INTERVAL_HOURS,
                    default=current.get(
                        CONF_UPDATE_INTERVAL_HOURS, DEFAULT_UPDATE_INTERVAL_HOURS
                    ),
                ): _interval_selector(),
            }
        )
        return self.async_show_form(step_id="init", data_schema=schema)
