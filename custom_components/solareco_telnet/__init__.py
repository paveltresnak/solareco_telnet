"""SolarEco Telnet integration for Home Assistant."""
from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .coordinator import SolarEcoTelnetCoordinator

_LOGGER = logging.getLogger(__name__)

DOMAIN = "solareco_telnet"
PLATFORMS: list[str] = ["sensor"]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up SolarEco Telnet from a config entry."""
    coordinator = SolarEcoTelnetCoordinator(
        hass,
        host=entry.data["host"],
        port=entry.data["port"],
        timeout=int(entry.data.get("timeout", 10)),
        poll_interval=int(entry.data.get("poll_interval", 5)),
        pause_at_night=bool(entry.data.get("pause_at_night", True)),
    )

    # First refresh — fails if device is unreachable. Swallowed so entities
    # are still created (marked unavailable), coordinator retries per interval.
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    entry.async_on_unload(entry.add_update_listener(_async_reload_entry))
    return True


async def _async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry when options change."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok
