"""Sensor platform for Simple PID Controller."""

from __future__ import annotations

import logging

from collections.abc import Callable

from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import Event, HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.restore_state import RestoreEntity

from datetime import timedelta
from time import perf_counter
from simple_pid import PID
from typing import Any

from . import PIDDeviceHandle
from .entity import BasePIDEntity
from .coordinator import PIDDataCoordinator

# Coordinator is used to centralize the data updates
PARALLEL_UPDATES = 0

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up PID output and diagnostic sensors."""
    handle: PIDDeviceHandle = entry.runtime_data.handle

    # Init PID with default values
    handle.pid = PID(1.0, 0.1, 0.05, setpoint=50, sample_time=None, auto_mode=False)

    handle.pid.output_limits = (-10.0, 10.0)
    handle.last_contributions = (0, 0, 0, 0)
    handle.last_known_output = None

    async def update_pid() -> float | None:
        """Update the PID output using current sensor and parameter values."""
        input_value = handle.get_input_sensor_value()
        if input_value is None:
            raise ValueError("Input sensor not available")

        handle.input_history.append(input_value)

        # Read parameters from UI
        kp = handle.get_number("kp")
        ki = handle.get_number("ki")
        kd = handle.get_number("kd")
        setpoint = handle.get_number("setpoint")
        starting_output = handle.get_number("starting_output")
        start_mode = handle.get_select("start_mode")
        sample_time = handle.get_number("sample_time")
        out_min = handle.get_number("output_min")
        out_max = handle.get_number("output_max")
        auto_mode = handle.get_switch("auto_mode")
        p_on_m = handle.get_switch("proportional_on_measurement")
        windup_protection = handle.get_switch("windup_protection")

        # A missing number entity, or one whose state is not a float, yields
        # None here. Feeding that
        # into the controller fails much deeper, with an error that no longer
        # points at the entity that is actually missing.
        if kp is None or ki is None or kd is None or setpoint is None:
            raise ValueError("PID parameters not available")

        # adapt PID settings
        handle.pid.tunings = (kp, ki, kd)
        handle.pid.setpoint = setpoint

        handle.pid_parameter_history.append(
            {
                "kp": kp,
                "ki": ki,
                "kd": kd,
                "setpoint": setpoint,
            }
        )

        if windup_protection:
            handle.pid.output_limits = (out_min, out_max)
        else:
            handle.pid.output_limits = (None, None)

        _LOGGER.debug("Start mode = %s (type: %s)", start_mode, type(start_mode))
        if not handle.pid.auto_mode and auto_mode:
            if start_mode == "Zero start":
                handle.pid.set_auto_mode(True, 0)
            elif start_mode == "Last known value":
                handle.pid.set_auto_mode(True, handle.last_known_output)
            elif start_mode == "Startup value":
                handle.pid.set_auto_mode(True, starting_output)
            else:
                handle.pid.set_auto_mode(True)
        else:
            handle.pid.auto_mode = auto_mode

        handle.pid.proportional_on_measurement = p_on_m

        now = perf_counter()
        if handle.last_update_timestamp is None:
            handle.last_measured_sample_time = None
        else:
            handle.last_measured_sample_time = now - handle.last_update_timestamp
        handle.last_update_timestamp = now

        handle.sample_time_history.append(handle.last_measured_sample_time)

        output = handle.pid(input_value)

        # save last know output
        handle.last_known_output = output
        handle.output_history.append(output)

        # save last I contribution
        last_i = handle.last_contributions[1] or 0.0

        # save all latest contributions
        handle.last_contributions = (
            handle.pid.components[0],
            handle.pid.components[1],
            handle.pid.components[2],
            handle.pid.components[1] - last_i,
        )

        handle.pid_contribution_history.append(
            {
                "p": handle.last_contributions[0],
                "i": handle.last_contributions[1],
                "d": handle.last_contributions[2],
                "i_delta": handle.last_contributions[3],
            }
        )

        _LOGGER.debug(
            "PID input=%s setpoint=%s kp=%s ki=%s kd=%s => output=%s [P=%s, I=%s, D=%s, dI=%s]",
            input_value,
            handle.pid.setpoint,
            handle.pid.Kp,
            handle.pid.Ki,
            handle.pid.Kd,
            output,
            handle.last_contributions[0],
            handle.last_contributions[1],
            handle.last_contributions[2],
            handle.last_contributions[3],
        )

        # sample_time is None when the number entity is missing or holds a
        # non-numeric state; feeding that to timedelta() raises inside the
        # coordinator instead of simply leaving the interval alone.
        if sample_time is not None and (
            coordinator.update_interval is None
            or coordinator.update_interval.total_seconds() != sample_time
        ):
            _LOGGER.debug("Updating coordinator interval to %.2f seconds", sample_time)
            # homeassistant-stubs declares update_interval read-only: a stray
            # `_update_interval` attribute between the property and its setter
            # stops mypy from pairing them. Home Assistant itself defines the
            # setter (helpers/update_coordinator.py).
            coordinator.update_interval = timedelta(  # type: ignore[misc]
                seconds=sample_time
            )

        return output

    # Setup Coordinator
    if entry.runtime_data.coordinator is None:
        entry.runtime_data.coordinator = PIDDataCoordinator(
            hass, handle.name, update_pid, interval=10
        )
    coordinator: PIDDataCoordinator = entry.runtime_data.coordinator

    # Wait for HA to finish starting
    async def start_refresh(_: Any) -> None:
        _LOGGER.debug("Home Assistant started, first PID-refresh started")
        await coordinator.async_request_refresh()

    entry.async_on_unload(
        hass.bus.async_listen_once("homeassistant_started", start_refresh)
    )

    async_add_entities(
        [
            PIDOutputSensor(hass, entry, coordinator),
            PIDContributionSensor(
                hass, entry, "pid_p_contrib", "P contribution", coordinator
            ),
            PIDContributionSensor(
                hass, entry, "pid_i_contrib", "I contribution", coordinator
            ),
            PIDContributionSensor(
                hass, entry, "pid_d_contrib", "D contribution", coordinator
            ),
            PIDContributionSensor(hass, entry, "error", "Error", coordinator),
            PIDContributionSensor(hass, entry, "pid_i_delta", "I delta", coordinator),
            PIDSampleTimeSensor(
                hass, entry, "actual_sample_time", "Actual Sample Time", coordinator
            ),
        ]
    )

    # Put listeners on inputs
    def make_listener(entity_id: str) -> Callable[[Event[Any]], None]:
        def _listener(event: Event[Any]) -> None:
            if event.data.get("entity_id") == entity_id:
                _LOGGER.debug("Update detected on %s", entity_id)
                # async_request_refresh is a coroutine: calling it from this
                # synchronous listener without scheduling it left the refresh
                # unawaited, so a change to one of the inputs below never
                # actually reached the controller.
                hass.async_create_task(coordinator.async_request_refresh())

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
        unsub = hass.bus.async_listen(
            "state_changed", make_listener(f"number.{entry.entry_id}_{key}")
        )
        entry.async_on_unload(unsub)

    for key in ["auto_mode", "proportional_on_measurement", "windup_protection"]:
        unsub = hass.bus.async_listen(
            "state_changed", make_listener(f"switch.{entry.entry_id}_{key}")
        )
        entry.async_on_unload(unsub)

    for key in ["start_mode"]:
        unsub = hass.bus.async_listen(
            "state_changed", make_listener(f"select.{entry.entry_id}_{key}")
        )
        entry.async_on_unload(unsub)


class PIDOutputSensor(
    BasePIDEntity, CoordinatorEntity[PIDDataCoordinator], RestoreEntity, SensorEntity
):
    """Sensor representing the PID output."""

    # homeassistant-stubs types BaseCoordinatorEntity.coordinator as Incomplete,
    # which erases the generic parameter and makes coordinator.data untyped.
    coordinator: PIDDataCoordinator

    def __init__(
        self, hass: HomeAssistant, entry: ConfigEntry, coordinator: PIDDataCoordinator
    ) -> None:
        # Both bases are initialised explicitly: super() would resolve to
        # BasePIDEntity, which takes a different signature.
        CoordinatorEntity.__init__(self, coordinator)

        name = "PID Output"
        key = "pid_output"

        BasePIDEntity.__init__(self, hass, entry, key, name)

        self._attr_native_unit_of_measurement = None
        self._attr_state_class = SensorStateClass.MEASUREMENT

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        if (state := await self.async_get_last_state()) is not None:
            try:
                value = float(state.state)
                self._handle.last_known_output = value
            except (ValueError, TypeError):
                self._handle.last_known_output = 0.0

    @property
    def native_value(self) -> float | None:
        if self.coordinator.data is None:
            return None
        return round(self.coordinator.data, 2)


class PIDContributionSensor(
    BasePIDEntity, CoordinatorEntity[PIDDataCoordinator], SensorEntity
):
    """Sensor representing P, I or D contribution."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        key: str,
        name: str,
        coordinator: PIDDataCoordinator,
    ) -> None:
        CoordinatorEntity.__init__(self, coordinator)

        BasePIDEntity.__init__(self, hass, entry, key, name)

        self._attr_entity_category = EntityCategory.DIAGNOSTIC
        self._attr_entity_registry_enabled_default = False
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._key = key

    @property
    def native_value(self) -> float | None:
        contributions = self._handle.last_contributions
        input_value = self._handle.get_input_sensor_value()
        setpoint = self._handle.get_number("setpoint")

        error: float
        if input_value is None or setpoint is None:
            error = 0
        else:
            error = input_value - setpoint

        value = {
            "pid_p_contrib": contributions[0],
            "pid_i_contrib": contributions[1],
            "pid_d_contrib": contributions[2],
            "error": error,
            "pid_i_delta": contributions[3],
        }.get(self._key)
        return round(value, 3) if value is not None else None


class PIDSampleTimeSensor(
    BasePIDEntity, CoordinatorEntity[PIDDataCoordinator], SensorEntity
):
    """Sensor exposing the measured sample time between PID updates."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        key: str,
        name: str,
        coordinator: PIDDataCoordinator,
    ) -> None:
        CoordinatorEntity.__init__(self, coordinator)

        BasePIDEntity.__init__(self, hass, entry, key, name)

        self._attr_entity_category = EntityCategory.DIAGNOSTIC
        self._attr_entity_registry_enabled_default = False
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_native_unit_of_measurement = "s"

    @property
    def native_value(self) -> float | None:
        sample_time = self._handle.last_measured_sample_time
        if sample_time is None:
            return None
        return round(sample_time, 3)
