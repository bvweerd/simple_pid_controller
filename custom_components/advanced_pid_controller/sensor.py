# custom_components/advanced_pid_controller/sensor.py

from __future__ import annotations

import logging

from homeassistant.components.sensor import SensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from simple_pid import PID

from .const import DOMAIN, CONF_SENSOR_ENTITY_ID
from .coordinator import PIDDataCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the PID output sensor."""

    name = entry.data.get("name", "PID Controller")
    sensor_entity_id = entry.options.get(CONF_SENSOR_ENTITY_ID, entry.data.get(CONF_SENSOR_ENTITY_ID))

    """
    # Entity IDs van bijbehorende number sliders
    kp_id = f"number.{entry.entry_id}_kp"
    ki_id = f"number.{entry.entry_id}_ki"
    kd_id = f"number.{entry.entry_id}_kd"
    setpoint_id = f"number.{entry.entry_id}_setpoint"
    """
    
    # Placeholder PID-configuratie (kan later dynamisch worden)
    pid = PID(1.0, 0.1, 0.05, setpoint=50)
    pid.output_limits = (-100, 100)

    async def update_pid():
        state = hass.states.get(sensor_entity_id)
        if state is None or state.state in ("unknown", "unavailable"):
            raise ValueError(f"Sensor {sensor_entity_id} state is not available")
        input_value = float(state.state)

        """
        # Waarden uit number sliders
        kp = float(hass.states.get(kp_id).state or 1)
        ki = float(hass.states.get(ki_id).state or 0)
        kd = float(hass.states.get(kd_id).state or 0)
        setpoint = float(hass.states.get(setpoint_id).state or 50)
        
        pid.tunings = (kp, ki, kd)
        pid.setpoint = setpoint
        """
        
        output = pid(input_value)
        """
        _LOGGER.debug(
            "PID: input=%.2f setpoint=%.2f kp=%.2f ki=%.2f kd=%.2f -> output=%.2f",
            input_value, setpoint, kp, ki, kd, output
        )
        """
        return output
        
    coordinator = PIDDataCoordinator(hass, name, update_pid, interval=10)
    await coordinator.async_config_entry_first_refresh()

    async_add_entities([PIDOutputSensor(entry, name, coordinator)])


class PIDOutputSensor(CoordinatorEntity[PIDDataCoordinator], SensorEntity):
    """Sensor that represents the PID output."""

    def __init__(self, entry_id: str, name: str, coordinator: PIDDataCoordinator):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._config_entry = entry_id
        self._attr_unique_id = f"{entry_id}_pid_output"
        self._attr_name = f"{name} PID Output"
        self._attr_native_unit_of_measurement = "%"
        self._attr_device_class = None

    @property
    def native_value(self) -> float:
        """Return the current PID output."""
        return round(self.coordinator.data, 2)

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self._config_entry.entry_id)},
            "name": "Advanced PID Controller",
            "manufacturer": "bvweerd",
            "model": "PID Controller",
            "entry_type": "service",  # Optional
        }