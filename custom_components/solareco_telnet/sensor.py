"""SolarEco Telnet sensor platform."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfEnergy,
    UnitOfFrequency,
    UnitOfPower,
    UnitOfTemperature,
    UnitOfTime,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import DOMAIN
from .coordinator import SolarEcoTelnetCoordinator

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True, kw_only=True)
class SolarEcoSensorDescription(SensorEntityDescription):
    """Per-sensor metadata. `key` must match a parser name in coordinator.PARSERS."""
    icon: str | None = None


SENSORS: tuple[SolarEcoSensorDescription, ...] = (
    SolarEcoSensorDescription(
        key="relay",
        translation_key="relay",
        icon="mdi:electric-switch",
    ),
    SolarEcoSensorDescription(
        key="fan",
        translation_key="fan",
        icon="mdi:fan",
    ),
    SolarEcoSensorDescription(
        key="required_voltage",
        translation_key="required_voltage",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:alpha-v-circle-outline",
    ),
    SolarEcoSensorDescription(
        key="voltage",
        translation_key="voltage",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:alpha-v-circle-outline",
    ),
    SolarEcoSensorDescription(
        key="current",
        translation_key="current",
        native_unit_of_measurement=UnitOfElectricCurrent.MILLIAMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:current-dc",
    ),
    SolarEcoSensorDescription(
        key="power",
        translation_key="power",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:alpha-w-circle-outline",
    ),
    SolarEcoSensorDescription(
        key="frequency",
        translation_key="frequency",
        native_unit_of_measurement=UnitOfFrequency.HERTZ,
        device_class=SensorDeviceClass.FREQUENCY,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:sine-wave",
    ),
    SolarEcoSensorDescription(
        key="cooler_temperature",
        translation_key="cooler_temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:thermometer",
    ),
    SolarEcoSensorDescription(
        key="boiler_temperature",
        translation_key="boiler_temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:water-boiler",
    ),
    SolarEcoSensorDescription(
        key="pulse_width",
        translation_key="pulse_width",
        native_unit_of_measurement=UnitOfTime.MICROSECONDS,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:pulse",
    ),
    SolarEcoSensorDescription(
        key="day_energy",
        translation_key="day_energy",
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:solar-power",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: SolarEcoTelnetCoordinator = hass.data[DOMAIN][entry.entry_id]
    entities = [SolarEcoSensor(coordinator, desc, entry) for desc in SENSORS]
    async_add_entities(entities)


class SolarEcoSensor(CoordinatorEntity[SolarEcoTelnetCoordinator], SensorEntity):
    """Single SolarEco data point from the parsed telnet line."""

    _attr_has_entity_name = True
    entity_description: SolarEcoSensorDescription

    def __init__(
        self,
        coordinator: SolarEcoTelnetCoordinator,
        description: SolarEcoSensorDescription,
        entry: ConfigEntry,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        # Unique_id preserved from v2.x for state history continuity.
        # Format: "<entry_id>_<sensor_name>".
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_icon = description.icon
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": f"SolarEco Telnet ({entry.data['host']})",
            "manufacturer": "SolarEco",
            "model": "MPPT Regulator (Telnet)",
        }

    @property
    def native_value(self) -> Any:
        if self.coordinator.data is None:
            return None
        return self.coordinator.data.get(self.entity_description.key)
