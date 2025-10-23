"""Config flow for SolarEco Telnet integration."""
import logging
import telnetlib
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError

_LOGGER = logging.getLogger(__name__)

DOMAIN = "solareco_telnet"

STEP_USER_DATA_SCHEMA = vol.Schema({
    vol.Required("host"): str,
    vol.Required("port", default=23): int,
    vol.Optional("poll_interval", default=5): int,
    vol.Optional("timeout", default=10): int,
    vol.Optional("pause_at_night", default=True): bool,
})


async def validate_connection(hass: HomeAssistant, data: dict) -> dict:
    """Validate the connection to SolarEco device."""
    host = data["host"]
    port = data["port"]
    timeout = data.get("timeout", 10)

    try:
        await hass.async_add_executor_job(
            _test_connection, host, port, timeout
        )
    except ConnectionError as err:
        _LOGGER.error("Connection test failed: %s", err)
        raise CannotConnect from err
    except Exception as err:
        _LOGGER.error("Unexpected error: %s", err)
        raise CannotConnect from err

    return {"title": f"SolarEco Telnet ({host})"}


def _test_connection(host: str, port: int, timeout: int) -> None:
    """Test connection to SolarEco device (blocking)."""
    try:
        with telnetlib.Telnet(host, port, timeout=timeout) as tn:
            data = tn.read_until(b'\n', timeout=timeout)
            if not data:
                raise ConnectionError("No data received from device")
    except Exception as err:
        raise ConnectionError(f"Failed to connect: {err}") from err


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class SolarEcoTelnetConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for SolarEco Telnet."""

    VERSION = 1

    async def async_step_user(self, user_input=None) -> FlowResult:
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            try:
                info = await validate_connection(self.hass, user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                # Create unique ID based on host:port
                await self.async_set_unique_id(f"{user_input['host']}:{user_input['port']}")
                self._abort_if_unique_id_configured()

                return self.async_create_entry(title=info["title"], data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )
