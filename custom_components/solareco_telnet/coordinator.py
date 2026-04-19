"""DataUpdateCoordinator for SolarEco Telnet.

Replaces the custom SensorConnector class from v2.x. Benefits:
- Uses HA's standard update pattern — less custom code
- asyncio.open_connection() instead of blocking telnetlib
  (telnetlib is deprecated since Python 3.11 and removed in 3.13)
- Backoff + sun-below-horizon pause preserved from v2.2.0
"""
from __future__ import annotations

import asyncio
import logging
import time
from datetime import timedelta

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from . import parsers

_LOGGER = logging.getLogger(__name__)


# Map sensor name → parser function. Order doesn't matter; sensor.py uses
# the same keys as entity translation_keys.
PARSERS: dict[str, callable] = {
    "relay": parsers.parse_relay,
    "fan": parsers.parse_fan,
    "required_voltage": parsers.parse_required_voltage,
    "voltage": parsers.parse_voltage,
    "current": parsers.parse_current,
    "power": parsers.parse_power,
    "frequency": parsers.parse_frequency,
    "cooler_temperature": parsers.parse_cooler_temperature,
    "boiler_temperature": parsers.parse_boiler_temperature,
    "pulse_width": parsers.parse_pulse_width,
    "day_energy": parsers.parse_day_energy,
}


class SolarEcoTelnetCoordinator(DataUpdateCoordinator[dict]):
    """Polls the SolarEco telnet endpoint and exposes parsed values to sensors."""

    # Backoff schedule: after 3 initial failures, progressively wait longer
    # before retrying. Values in seconds.
    BACKOFF_SCHEDULE = [10, 30, 60, 120, 300]
    BACKOFF_LOG_INTERVAL = 300  # log at most once per 5 min while backing off
    # sun.sun may be unavailable for a few seconds at HA startup (integration
    # load order race). Only log the warning after this many consecutive misses.
    SUN_WARN_AFTER = 5

    def __init__(
        self,
        hass: HomeAssistant,
        host: str,
        port: int,
        timeout: int,
        poll_interval: int,
        pause_at_night: bool,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=f"solareco_telnet {host}:{port}",
            update_interval=timedelta(seconds=poll_interval),
        )
        self.host = host
        self.port = port
        self.timeout = timeout
        self.pause_at_night = pause_at_night

        self._consecutive_errors = 0
        self._backoff_until = 0.0
        self._last_error_log_time = 0.0
        self._sun_warning_logged = False
        self._sun_missing_count = 0      # how many consecutive polls had no sun.sun
        self._night_mode = False

    async def _async_update_data(self) -> dict:
        """Fetch one line via telnet, parse it, return dict of values."""
        now = time.monotonic()

        # Sun-below-horizon pause
        if self.pause_at_night and self._check_night_mode():
            # Keep returning last known data with unchanged timestamps; entities
            # mark unavailable via coordinator.last_update_success=False after
            # a failed update. Here we succeed with previous data — they stay
            # available but stale. If that's undesired, raise UpdateFailed.
            return self.data or {name: None for name in PARSERS}

        # Backoff window
        if now < self._backoff_until:
            remaining = self._backoff_until - now
            _LOGGER.debug("In backoff window, %d s remaining", int(remaining))
            raise UpdateFailed(f"Backoff active for {int(remaining)} s more")

        try:
            line = await self._read_line()
        except (asyncio.TimeoutError, OSError, ConnectionError) as err:
            self._handle_failure(err, now)
            raise UpdateFailed(str(err)) from err

        # Parse
        result: dict = {}
        for name, parser in PARSERS.items():
            try:
                result[name] = parser(line)
            except Exception as err:  # parser shouldn't raise but be safe
                _LOGGER.warning("Parser %s failed: %s", name, err)
                result[name] = None

        if self._consecutive_errors > 0:
            _LOGGER.info(
                "SolarEco connection restored after %d failed attempts",
                self._consecutive_errors,
            )
        self._consecutive_errors = 0
        self._backoff_until = 0.0
        self._last_error_log_time = 0.0

        _LOGGER.debug("Received: %s", line)
        return result

    # ─── Telnet I/O (pure asyncio, no telnetlib) ─────────────────────────────

    async def _read_line(self) -> str:
        """Open async TCP connection, read one line, close.

        SolarEco publishes one newline-terminated line as soon as a client
        connects, then keeps the session open. We only need the first line,
        so we close immediately.
        """
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(self.host, self.port),
            timeout=self.timeout,
        )
        try:
            raw = await asyncio.wait_for(reader.readline(), timeout=self.timeout)
        finally:
            writer.close()
            try:
                await asyncio.wait_for(writer.wait_closed(), timeout=2)
            except asyncio.TimeoutError:
                pass

        if not raw:
            raise ConnectionError("Empty response from SolarEco")
        line = raw.decode("ascii", errors="replace").strip()
        if not line:
            raise ConnectionError("Blank line from SolarEco")
        return line

    # ─── Helpers ─────────────────────────────────────────────────────────────

    def _check_night_mode(self) -> bool:
        """Return True if sun is below horizon (and pause_at_night is enabled)."""
        sun = self.hass.states.get("sun.sun")
        if sun is None:
            self._sun_missing_count += 1
            if (
                not self._sun_warning_logged
                and self._sun_missing_count >= self.SUN_WARN_AFTER
            ):
                _LOGGER.warning(
                    "sun.sun entity not available after %d polls; night pause disabled. "
                    "Set your location in Settings → System → General, "
                    "or disable 'Pause at night' in integration options.",
                    self._sun_missing_count,
                )
                self._sun_warning_logged = True
            else:
                _LOGGER.debug(
                    "sun.sun not yet available (%d/%d polls)",
                    self._sun_missing_count,
                    self.SUN_WARN_AFTER,
                )
            return False
        # Sun available — reset counter + re-arm warning so later disappearance triggers again
        if self._sun_missing_count > 0 or self._sun_warning_logged:
            self._sun_missing_count = 0
            self._sun_warning_logged = False
        if sun.state == "below_horizon":
            if not self._night_mode:
                _LOGGER.info("Entering night mode — updates paused until sunrise")
                self._night_mode = True
                self._consecutive_errors = 0
                self._backoff_until = 0.0
            return True
        if self._night_mode:
            _LOGGER.info("Exiting night mode — resuming updates")
            self._night_mode = False
        return False

    def _get_backoff_seconds(self) -> int:
        """Return backoff delay based on consecutive_errors (0 if <= 3)."""
        if self._consecutive_errors <= 3:
            return 0
        idx = min(self._consecutive_errors - 4, len(self.BACKOFF_SCHEDULE) - 1)
        return self.BACKOFF_SCHEDULE[idx]

    def _handle_failure(self, err: Exception, now: float) -> None:
        self._consecutive_errors += 1
        if self._consecutive_errors <= 3:
            _LOGGER.warning(
                "Failed to connect to SolarEco (attempt %d): %s",
                self._consecutive_errors,
                err,
            )
        else:
            backoff = self._get_backoff_seconds()
            self._backoff_until = now + backoff
            if (now - self._last_error_log_time) >= self.BACKOFF_LOG_INTERVAL:
                _LOGGER.warning(
                    "SolarEco unreachable (%d consecutive failures). "
                    "Next retry in %d s. Last error: %s",
                    self._consecutive_errors,
                    backoff,
                    err,
                )
                self._last_error_log_time = now
