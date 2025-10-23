"""SolarEco Telnet sensor platform."""
import logging
import telnetlib
from datetime import timedelta
import re

from homeassistant.components.sensor import SensorEntity, SensorStateClass, SensorDeviceClass
from homeassistant.const import UnitOfTemperature, UnitOfPower, UnitOfElectricPotential, UnitOfElectricCurrent, \
    UnitOfEnergy, UnitOfFrequency, UnitOfTime
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.dispatcher import async_dispatcher_connect, dispatcher_send
from homeassistant.helpers.event import async_track_time_interval

DOMAIN = "solareco_telnet"
SIGNAL = "solareco_telnet_update"

_LOGGER = logging.getLogger(__name__)


class SolarecoSensorConfig:
    """Sensor configuration class."""

    def __init__(self, name, unit_of_measurement, device_class, data_transformation, 
                 icon, state_class=SensorStateClass.MEASUREMENT):
        self.name = name
        self.unit_of_measurement = unit_of_measurement
        self.device_class = device_class
        self.data_transformation = data_transformation
        self.icon = icon
        self.state_class = state_class


SENSORS = [
    SolarecoSensorConfig('relay', None, None, 
        lambda data: re.findall(r'AC+\d', data)[0][2:] if re.search(r'AC+\d', data) else (re.findall(r'R:+\d', data)[0][2:] if re.search(r'R:+\d', data) else None),
        "mdi:electric-switch"),
    SolarecoSensorConfig('fan', None, None, 
        lambda data: re.findall(r'F:+\d', data)[0][2:] if re.search(r'F:+\d', data) else None,
        "mdi:fan"),
    SolarecoSensorConfig('required_voltage', UnitOfElectricPotential.VOLT, None, 
        lambda data: int(re.findall(r'U:(\d+)\s', data)[0]) if re.search(r'U:(\d+)\s', data) else None,
        "mdi:alpha-v-circle-outline"),
    SolarecoSensorConfig('voltage', UnitOfElectricPotential.VOLT, SensorDeviceClass.VOLTAGE, 
        lambda data: int(re.findall(r'(\d+)V', data)[0]) if re.search(r'(\d+)V', data) else None,
        "mdi:alpha-v-circle-outline"),
    SolarecoSensorConfig('current', UnitOfElectricCurrent.MILLIAMPERE, SensorDeviceClass.CURRENT, 
        lambda data: int(re.findall(r'(\d+)mA', data)[0]) if re.search(r'(\d+)mA', data) else None,
        "mdi:current-dc"),
    SolarecoSensorConfig('power', UnitOfPower.WATT, SensorDeviceClass.POWER, 
        lambda data: int(re.findall(r'(\d+)W', data)[0]) if re.search(r'(\d+)W', data) else None,
        "mdi:alpha-w-circle-outline"),
    SolarecoSensorConfig('frequency', UnitOfFrequency.HERTZ, SensorDeviceClass.FREQUENCY, 
        lambda data: int(re.findall(r'(\d+)Hz', data)[0]) if re.search(r'(\d+)Hz', data) else None,
        "mdi:sine-wave"),
    SolarecoSensorConfig('cooler_temperature', UnitOfTemperature.CELSIUS, SensorDeviceClass.TEMPERATURE, 
        lambda data: int(re.findall(r'(\d+)C', data)[0]) if re.search(r'(\d+)C', data) else None,
        "mdi:thermometer"),
    SolarecoSensorConfig('boiler_temperature', UnitOfTemperature.CELSIUS, SensorDeviceClass.TEMPERATURE, 
        lambda data: int(re.findall(r'(\d+):\d+C', data)[0]) if re.search(r'(\d+):\d+C', data) else None,
        "mdi:water-boiler"),
    SolarecoSensorConfig('pulse_width', UnitOfTime.MICROSECONDS, None, 
        lambda data: int(re.findall(r'(\d+)us', data)[0]) if re.search(r'(\d+)us', data) else None,
        "mdi:pulse"),
    SolarecoSensorConfig('day_energy', UnitOfEnergy.WATT_HOUR, SensorDeviceClass.ENERGY, 
        lambda data: int(re.findall(r'(\d+)Wh', data)[-1]) if re.search(r'(\d+)Wh', data) else None,
        "mdi:solar-power",
        SensorStateClass.TOTAL_INCREASING),
]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up SolarEco Telnet sensors from a config entry."""
    config = entry.data
    
    _LOGGER.info(f"Setting up SolarEco Telnet sensor platform: {config}")
    
    sensor_connector = SensorConnector(
        hass,
        entry.entry_id,
        config['host'],
        config['port'],
        config.get('timeout', 10),
        config.get('pause_at_night', True)
    )
    
    # Do first update
    await hass.async_add_executor_job(sensor_connector.update)
    
    # Poll for updates in the background
    poll_interval = int(config.get('poll_interval', 5))
    
    async def async_update(now):
        """Update sensor data only when sun is above horizon."""
        # Check if pause at night is enabled
        if not config.get('pause_at_night', True):
            # Night pause disabled, always update
            await hass.async_add_executor_job(sensor_connector.update)
            return
            
        # Check if sun entity exists
        sun_state = hass.states.get('sun.sun')
        if sun_state is None:
            # Sun entity not available, log warning once and continue updating
            if not hasattr(async_update, '_sun_warning_logged'):
                _LOGGER.warning(
                    "Sun entity (sun.sun) not available. Night mode disabled. "
                    "Configure your location in Settings -> System -> General to enable night mode, "
                    "or disable 'Pause at night' option when reconfiguring this integration."
                )
                async_update._sun_warning_logged = True
            await hass.async_add_executor_job(sensor_connector.update)
            return
        
        if sun_state.state == 'below_horizon':
            _LOGGER.debug("Sun is below horizon, skipping update")
            sensor_connector.set_night_mode(True)
            return
        
        sensor_connector.set_night_mode(False)
        await hass.async_add_executor_job(sensor_connector.update)
    
    entry.async_on_unload(
        async_track_time_interval(hass, async_update, timedelta(seconds=poll_interval))
    )

    entities = [
        SolarecoSensor(sensor_connector, sensor_config, entry)
        for sensor_config in SENSORS
    ]
    async_add_entities(entities, True)


class SolarecoSensor(SensorEntity):
    """Representation of a SolarEco sensor."""

    def __init__(self, sensor_connector, sensor_config: SolarecoSensorConfig, entry: ConfigEntry):
        """Initialize the sensor."""
        super().__init__()
        self.sensor_connector = sensor_connector
        self.sensor_config = sensor_config
        self._entry = entry

        self._attr_has_entity_name = True
        self._attr_translation_key = self.sensor_config.name
        self._state = None
        self._attr_icon = self.sensor_config.icon
        
        # Set device info
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": f"SolarEco Telnet ({entry.data['host']})",
            "manufacturer": "SolarEco",
            "model": "MPPT Regulator (Telnet)",
        }

    async def async_added_to_hass(self) -> None:
        """Run when entity about to be added to hass."""
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass,
                f"{SIGNAL}_{self._entry.entry_id}",
                self._async_update_callback
            )
        )

    @callback
    def _async_update_callback(self):
        """Update the state."""
        self._async_update_data()
        self.async_write_ha_state()

    @property
    def unique_id(self):
        """Return a unique ID."""
        return f"{self._entry.entry_id}_{self.sensor_config.name}"

    @property
    def native_value(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def state_class(self):
        """Return the state class."""
        return self.sensor_config.state_class

    @property
    def device_class(self):
        """Return the device class."""
        return self.sensor_config.device_class

    @property
    def native_unit_of_measurement(self):
        """Return the unit of measurement."""
        return self.sensor_config.unit_of_measurement

    @property
    def available(self):
        """Return True if entity is available."""
        return self.sensor_connector.available

    @callback
    def _async_update_data(self):
        """Fetch new state data for the sensor."""
        self._state = self.sensor_connector.data.get(self.sensor_config.name)


class SensorConnector:
    """Class to manage connection to SolarEco device."""

    def __init__(self, hass, entry_id, solareco_host, solareco_port, timeout=10, pause_at_night=True):
        """Initialize the connector."""
        self.hass = hass
        self.entry_id = entry_id
        self.solareco_host = solareco_host
        self.solareco_port = solareco_port
        self.timeout = timeout
        self.pause_at_night = pause_at_night
        self.data = {sensor.name: None for sensor in SENSORS}
        self.available = False
        self._consecutive_errors = 0
        self._night_mode = False

    def set_night_mode(self, night_mode: bool):
        """Set night mode (don't try to connect when sun is down)."""
        if night_mode != self._night_mode:
            self._night_mode = night_mode
            if night_mode:
                _LOGGER.info("Entering night mode - updates paused until sunrise")
                self.available = False
                # Keep last known values but mark as unavailable
                dispatcher_send(self.hass, f"{SIGNAL}_{self.entry_id}")
            else:
                _LOGGER.info("Exiting night mode - resuming updates")

    def update(self):
        """Fetch new state data."""
        if self._night_mode:
            _LOGGER.debug("In night mode, skipping update")
            return
            
        try:
            _LOGGER.debug(f"Connecting to SolarEco at {self.solareco_host}:{self.solareco_port}")
            
            with telnetlib.Telnet(self.solareco_host, self.solareco_port, timeout=self.timeout) as tn:
                # Read data with timeout
                line = tn.read_until(b'\n', timeout=self.timeout).decode('ascii').strip()
                
                if not line:
                    raise Exception("Empty response from SolarEco")
                
                _LOGGER.debug(f"Received data: {line}")
                
                # Parse data
                for sensor in SENSORS:
                    try:
                        value = sensor.data_transformation(line)
                        self.data[sensor.name] = value
                        _LOGGER.debug(f"Parsed {sensor.name}: {value}")
                    except Exception as e:
                        _LOGGER.warning(f"Failed to parse {sensor.name}: {e}")
                        self.data[sensor.name] = None
                
                # Reset error counter on successful update
                self._consecutive_errors = 0
                self.available = True
                
                # Notify sensors
                dispatcher_send(self.hass, f"{SIGNAL}_{self.entry_id}")
                
        except Exception as e:
            self._consecutive_errors += 1
            
            if self._consecutive_errors <= 3:
                _LOGGER.warning(f"Failed to connect to SolarEco (attempt {self._consecutive_errors}): {e}")
            else:
                _LOGGER.error(f"Repeated connection failures to SolarEco ({self._consecutive_errors} times): {e}")
            
            # Mark as unavailable after 3 consecutive errors
            if self._consecutive_errors >= 3:
                self.available = False
                
            # Keep last known values but mark as stale
            dispatcher_send(self.hass, f"{SIGNAL}_{self.entry_id}")
