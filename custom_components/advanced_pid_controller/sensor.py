"""Sensor platform for Advanced PID Controller."""

from __future__ import annotations

import logging

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from simple_pid import PID

from . import PIDDeviceHandle
from .const import DOMAIN
from .coordinator import PIDDataCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the PID output sensor."""
    handle: PIDDeviceHandle = hass.data[DOMAIN][entry.entry_id]
    name = handle.name

    pid = PID(1.0, 0.1, 0.05, setpoint=50)
    pid.output_limits = (0, 100)

    async def update_pid():
        input_value = handle.get_input_sensor_value()
        if input_value is None:
            raise ValueError("Input sensor not available")

        kp = handle.get_number("kp") or 1.0
        ki = handle.get_number("ki") or 0.1
        kd = handle.get_number("kd") or 0.05
        setpoint = handle.get_number("setpoint") or 50.0

        pid.tunings = (kp, ki, kd)
        pid.setpoint = setpoint

        output = pid(input_value)
        _LOGGER.debug(
            "PID: input=%.2f setpoint=%.2f kp=%.2f ki=%.2f kd=%.2f -> output=%.2f",
            input_value, setpoint, kp, ki, kd, output
        )
        return output

    coordinator = PIDDataCoordinator(hass, name, update_pid, interval=10)
    await coordinator.async_config_entry_first_refresh()

    async_add_entities([PIDOutputSensor(entry.entry_id, name, coordinator)])


class PIDOutputSensor(CoordinatorEntity[PIDDataCoordinator], SensorEntity):
    """Sensor representing the PID output."""

    def __init__(self, entry_id: str, name: str, coordinator: PIDDataCoordinator):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry_id}_pid_output"
        self._attr_name = f"{name} PID Output"
        self._attr_native_unit_of_measurement = "%"
        self._attr_device_class = None
        self._entry_id = entry_id
        self._device_name = name

    @property
    def native_value(self) -> float:
        """Return the current PID output."""
        return round(self.coordinator.data, 2)

    @property
    def device_info(self):
        """Return device information for grouping entities."""
        return {
            "identifiers": {(DOMAIN, self._entry_id)},
            "name": self._device_name,
            "manufacturer": "Custom",
            "model": "Advanced PID Controller",
        }
