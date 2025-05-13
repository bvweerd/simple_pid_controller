"""Sensor platform for Simple PID Controller."""

from __future__ import annotations

import logging

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.entity import EntityCategory

from datetime import timedelta
from simple_pid import PID
from typing import Any

from . import PIDDeviceHandle
from .const import DOMAIN
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

    # Init PID with default values
    pid = PID(1.0, 0.1, 0.05, setpoint=50)
    pid.sample_time = 10.0
    pid.output_limits = (-10.0, 10.0)

    async def update_pid():
        """Update the PID output using current sensor and parameter values."""
        input_value = handle.get_input_sensor_value()
        if input_value is None:
            raise ValueError("Input sensor not available")

        # Lees parameters uit de UI
        kp = handle.get_number("kp")
        ki = handle.get_number("ki")
        kd = handle.get_number("kd")
        setpoint = handle.get_number("setpoint")
        sample_time = handle.get_number("sample_time")
        out_min = handle.get_number("output_min")
        out_max = handle.get_number("output_max")
        auto_mode = handle.get_switch("auto_mode")
        p_on_m = handle.get_switch("proportional_on_measurement")

        # Pas live de PID-instellingen aan
        pid.tunings = (kp, ki, kd)
        pid.setpoint = setpoint
        pid.sample_time = sample_time
        pid.output_limits = (out_min, out_max)
        pid.auto_mode = auto_mode
        pid.proportional_on_measurement = p_on_m

        output = pid(input_value)

        # Calculate contributions
        p_contrib = kp * (setpoint - input_value) if not p_on_m else -kp * input_value
        i_contrib = pid._integral * ki
        d_contrib = pid._last_output - output if pid._last_output is not None else 0.0

        handle.last_contributions = (p_contrib, i_contrib, d_contrib)

        _LOGGER.debug(
            "PID input=%.2f setpoint=%.2f kp=%.2f ki=%.2f kd=%.2f => output=%.2f [P=%.2f, I=%.2f, D=%.2f]",
            input_value,
            setpoint,
            kp,
            ki,
            kd,
            output,
            p_contrib,
            i_contrib,
            d_contrib,
        )

        if coordinator.update_interval.total_seconds() != pid.sample_time:
            _LOGGER.debug("Updating coordinator interval to %.2f seconds", pid.sample_time)
            coordinator.update_interval = timedelta(seconds=pid.sample_time)

        return output

    # Setup Coordinator 
    coordinator = PIDDataCoordinator(hass, name, update_pid, interval=10)
    # Wait for HA to finish starting
    async def start_refresh(_: Any) -> None:
        _LOGGER.debug("Home Assistant started, first PID-refresh started")
        await coordinator.async_request_refresh()

    hass.bus.async_listen_once("homeassistant_started", start_refresh)

    async_add_entities(
        [
            PIDOutputSensor(entry, name, coordinator),
            PIDContributionSensor(entry, name, "p", handle, coordinator),
            PIDContributionSensor(entry, name, "i", handle, coordinator),
            PIDContributionSensor(entry, name, "d", handle, coordinator),
        ]
    )

    # Put listeners on inputs
    def make_listener(entity_id: str):
        def _listener(event):
            if event.data.get("entity_id") == entity_id:
                _LOGGER.debug("Update detected on %s", entity_id)
                coordinator.async_request_refresh()

        return _listener

    for key in [
        "kp",
        "ki",
        "kd",
        "setpoint",
        "output_min",
        "output_max",
        "sample_time",
    ]:
        hass.bus.async_listen(
            "state_changed", make_listener(f"number.{entry.entry_id}_{key}")
        )

    for key in ["auto_mode", "proportional_on_measurement"]:
        hass.bus.async_listen(
            "state_changed", make_listener(f"switch.{entry.entry_id}_{key}")
        )


class PIDOutputSensor(CoordinatorEntity[PIDDataCoordinator], SensorEntity):
    """Sensor representing the PID output."""

    def __init__(self, entry: ConfigEntry, device_name: str, coordinator: PIDDataCoordinator):
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_pid_output"
        self._attr_name = f"PID Output"
        self._attr_has_entity_name = True
        self._attr_native_unit_of_measurement = "%"

        # Device-info
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": device_name,
        }

    @property
    def native_value(self) -> float | None:
        if self.coordinator.data is None:
            return None
        return round(self.coordinator.data, 2)


class PIDContributionSensor(CoordinatorEntity[PIDDataCoordinator], SensorEntity):
    """Sensor representing P, I or D contribution."""

    def __init__(
        self,
        entry: ConfigEntry,
        device_name: str,
        component: str,
        handle: PIDDeviceHandle,
        coordinator: PIDDataCoordinator,
    ):
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_pid_{component}_contrib"
        self._attr_name = f"PID {component.upper()} Contribution"
        self._attr_entity_category = EntityCategory.DIAGNOSTIC
        self._attr_entity_registry_enabled_default = False
        self._attr_has_entity_name = True
        self._handle = handle
        self._component = component
        self._entry_id = entry.entry_id

        # Device-info
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": device_name,
        }

    @property
    def native_value(self):
        contributions = self._handle.last_contributions
        value = {
            "p": contributions[0],
            "i": contributions[1],
            "d": contributions[2],
        }.get(self._component)
        return round(value, 2) if value is not None else None
