"""Config flow for SolarEco Telnet integration."""
from __future__ import annotations

import asyncio
import logging

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError

_LOGGER = logging.getLogger(__name__)

DOMAIN = "solareco_telnet"

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required("host"): str,
        vol.Required("port", default=23): int,
        vol.Optional("poll_interval", default=5): int,
        vol.Optional("timeout", default=10): int,
        vol.Optional("pause_at_night", default=True): bool,
    }
)


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


async def _test_connection(host: str, port: int, timeout: int) -> None:
    """Probe the device with an async TCP connection + readline."""
    try:
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(host, port),
            timeout=timeout,
        )
    except (asyncio.TimeoutError, OSError) as err:
        raise CannotConnect(f"Cannot open connection: {err}") from err

    try:
        raw = await asyncio.wait_for(reader.readline(), timeout=timeout)
    except asyncio.TimeoutError as err:
        writer.close()
        raise CannotConnect("Timeout waiting for first line") from err
    finally:
        writer.close()
        try:
            await asyncio.wait_for(writer.wait_closed(), timeout=2)
        except asyncio.TimeoutError:
            pass

    if not raw:
        raise CannotConnect("Empty response from device")


async def validate_connection(hass: HomeAssistant, data: dict) -> dict:
    """Validate that we can reach the SolarEco device."""
    await _test_connection(data["host"], data["port"], data.get("timeout", 10))
    return {"title": f"SolarEco Telnet ({data['host']})"}


class SolarEcoTelnetConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for SolarEco Telnet."""

    VERSION = 1

    async def async_step_user(self, user_input=None) -> FlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                info = await validate_connection(self.hass, user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except Exception:  # noqa: BLE001
                _LOGGER.exception("Unexpected exception during config validation")
                errors["base"] = "unknown"
            else:
                await self.async_set_unique_id(
                    f"{user_input['host']}:{user_input['port']}"
                )
                self._abort_if_unique_id_configured()
                return self.async_create_entry(title=info["title"], data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return OptionsFlowHandler(config_entry)


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Runtime-adjustable options: poll interval, timeout, night pause."""

    def __init__(self, config_entry):
        self._config_entry = config_entry

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            self.hass.config_entries.async_update_entry(
                self._config_entry,
                data={**self._config_entry.data, **user_input},
            )
            return self.async_create_entry(title="", data={})

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        "poll_interval",
                        default=self._config_entry.data.get("poll_interval", 5),
                    ): int,
                    vol.Optional(
                        "timeout",
                        default=self._config_entry.data.get("timeout", 10),
                    ): int,
                    vol.Optional(
                        "pause_at_night",
                        default=self._config_entry.data.get("pause_at_night", True),
                    ): bool,
                }
            ),
        )
