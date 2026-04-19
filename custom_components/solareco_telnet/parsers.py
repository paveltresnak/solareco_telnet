"""SolarEco data parsers — regex patterns + named parser functions.

Device sends one line per telnet read, e.g.:

    AC1 F:0 U:229 231V 123mA 28W 50Hz 45C 55:48C 1234us 10kWh 234Wh

Each parser function extracts one field from the raw line.
"""
from __future__ import annotations

import re


# Regex patterns compiled once at module load.
_RE_AC = re.compile(r"AC+(\d)")
_RE_RELAY_R = re.compile(r"R:+(\d)")
_RE_FAN = re.compile(r"F:+(\d)")
_RE_REQ_VOLT = re.compile(r"U:(\d+)\s")
_RE_VOLT = re.compile(r"(\d+)V")
_RE_CURRENT = re.compile(r"(\d+)mA")
_RE_POWER = re.compile(r"(\d+)W")
_RE_FREQ = re.compile(r"(\d+)Hz")
_RE_COOLER = re.compile(r"(\d+)C")
_RE_BOILER = re.compile(r"(\d+):\d+C")
_RE_PULSE = re.compile(r"(\d+)us")
_RE_TOTAL_ENERGY = re.compile(r"\d+kWh\s(\d+)Wh")
_RE_DAY_ENERGY = re.compile(r"(\d+)Wh")


def parse_relay(data: str) -> str | None:
    """Relay state — either 'ACn' or 'R:n'."""
    m = _RE_AC.search(data)
    if m:
        return m.group(1)
    m = _RE_RELAY_R.search(data)
    return m.group(1) if m else None


def parse_fan(data: str) -> str | None:
    m = _RE_FAN.search(data)
    return m.group(1) if m else None


def parse_required_voltage(data: str) -> int | None:
    m = _RE_REQ_VOLT.search(data)
    return int(m.group(1)) if m else None


def parse_voltage(data: str) -> int | None:
    m = _RE_VOLT.search(data)
    return int(m.group(1)) if m else None


def parse_current(data: str) -> int | None:
    m = _RE_CURRENT.search(data)
    return int(m.group(1)) if m else None


def parse_power(data: str) -> int | None:
    m = _RE_POWER.search(data)
    return int(m.group(1)) if m else None


def parse_frequency(data: str) -> int | None:
    m = _RE_FREQ.search(data)
    return int(m.group(1)) if m else None


def parse_cooler_temperature(data: str) -> int | None:
    """First 'NNC' match — cooler temp."""
    m = _RE_COOLER.search(data)
    return int(m.group(1)) if m else None


def parse_boiler_temperature(data: str) -> int | None:
    """Boiler temp in format 'HH:MMC'."""
    m = _RE_BOILER.search(data)
    return int(m.group(1)) if m else None


def parse_pulse_width(data: str) -> int | None:
    m = _RE_PULSE.search(data)
    return int(m.group(1)) if m else None


def parse_total_energy(data: str) -> int | None:
    """Total energy — 'NNkWh MMWh' → MM (Wh part only)."""
    m = _RE_TOTAL_ENERGY.search(data)
    return int(m.group(1)) if m else None


def parse_day_energy(data: str) -> int | None:
    """Daily energy — last 'NNWh' in the line."""
    matches = _RE_DAY_ENERGY.findall(data)
    return int(matches[-1]) if matches else None
