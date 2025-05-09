"""Sensor platform for Simple PID Controller."""

from __future__ import annotations

import logging

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.entity import EntityCategory

from simple_pid import PID

from .const import DOMAIN
from . import PIDDeviceHandle
from .coordinator import PIDDataCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up PID output and diagnostic sensors."""
    handle: PIDDeviceHandle = hass.data[DOMAIN][entry.entry_id]
    name = handle.name

    pid = PID(1.0, 0.1, 0.05, setpoint=50)
    pid.output_limits = (-10.0, 10.0)

    sample_time = handle.get_number("sample_time") or 10.0

    async def update_pid():
        input_value = handle.get_input_sensor_value()
        if input_value is None:
            raise ValueError("Input sensor not available")

        kp = handle.get_number("kp") or 1.0
        ki = handle.get_number("ki") or 0.1
        kd = handle.get_number("kd") or 0.05
        setpoint = handle.get_number("setpoint") or 50.0
        out_min = handle.get_number("output_min") or -10.0
        out_max = handle.get_number("output_max") or 10.0
        auto_mode = handle.get_switch("auto_mode")
        p_on_m = handle.get_switch("proportional_on_measurement")

        pid.tunings = (kp, ki, kd)
        pid.setpoint = setpoint
        pid.sample_time = sample_time
        pid.output_limits = (out_min, out_max)
        pid.auto_mode = auto_mode
        pid.proportional_on_measurement = p_on_m

        output = pid(input_value)

        p_contrib = kp * (pid.setpoint - input_value) if not p_on_m else -kp * input_value
        i_contrib = pid._integral * ki
        d_contrib = pid._last_output - output if pid._last_output is not None else 0.0

        handle.last_contributions = (p_contrib, i_contrib, d_contrib)
        return output

    coordinator = PIDDataCoordinator(hass, name, update_pid, interval=sample_time)
    await coordinator.async_config_entry_first_refresh()

    async_add_entities([
        PIDOutputSensor(entry.entry_id, name, coordinator),
        PIDContributionSensor(entry.entry_id, name, "p", handle, coordinator),
        PIDContributionSensor(entry.entry_id, name, "i", handle, coordinator),
        PIDContributionSensor(entry.entry_id, name, "d", handle, coordinator),
    ])

    def make_listener(target_id: str):
        def _listener(event):
            if event.data.get("entity_id") == target_id:
                coordinator.async_request_refresh()
        return _listener

    # Monitor numeric and switch parameter changes
    for key in ["kp","ki","kd","setpoint","output_min","output_max","sample_time"]:
        hass.bus.async_listen("state_changed", make_listener(f"number.{entry.entry_id}_{key}"))
    for key in ["auto_mode","proportional_on_measurement"]:
        hass.bus.async_listen("state_changed", make_listener(f"switch.{entry.entry_id}_{key}"))


class PIDOutputSensor(CoordinatorEntity[PIDDataCoordinator], SensorEntity):
    """Sensor representing the PID output."""

    def __init__(self, entry_id: str, name: str, coordinator: PIDDataCoordinator):
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry_id}_pid_output"
        self._attr_name = f"{name} PID Output"
        self._attr_native_unit_of_measurement = "%"
        self._entry_id = entry_id
        self._device_name = name

    @property
    def native_value(self) -> float:
        return round(self.coordinator.data, 2)

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self._entry_id)},
            "name": self._device_name,
            "manufacturer": "Custom",
            "model": "Simple PID Controller",
        }


class PIDContributionSensor(CoordinatorEntity[PIDDataCoordinator], SensorEntity):
    """Sensor representing the P, I, or D contribution of the PID controller."""

    def __init__(self, entry_id: str, name: str, component: str, handle: PIDDeviceHandle, coordinator: PIDDataCoordinator):
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry_id}_pid_{component}_contrib"
        self._attr_name = f"{name} PID {component.upper()} Contribution"
        self._attr_entity_category = EntityCategory.DIAGNOSTIC
        self._handle = handle
        self._component = component
        self._device_name = name
        self._entry_id = entry_id

    @property
    def native_value(self):
        p, i, d = self._handle.last_contributions
        val = {"p": p, "i": i, "d": d}[self._component]
        return round(val, 2) if val is not None else None

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self._entry_id)},
            "name": self._device_name,
            "manufacturer": "Custom",
            "model": "Simple PID Controller",
        }
