from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.const import CONF_NAME, CONF_UNIQUE_ID
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_platform
from homeassistant.helpers.entity_component import EntityComponent

from pid import PID, AutoMode

_LOGGER = logging.getLogger(__name__)

CONF_INPUT_SENSOR = "input_sensor"
CONF_SETPOINT = "setpoint"
CONF_SETPOINT_SENSOR = "setpoint_sensor"
CONF_KP = "kp"
CONF_KI = "ki"
CONF_KD = "kd"
CONF_WINDOW_SIZE = "window_size"
CONF_PRECISION = "precision"
CONF_MIN_OUTPUT = "min_output"
CONF_MAX_OUTPUT = "max_output"
CONF_REVERSE = "reverse"

DEFAULT_NAME = "Simple PID Controller"
DEFAULT_KP = 1.0
DEFAULT_KI = 0.1
DEFAULT_KD = 0.0
DEFAULT_WINDOW_SIZE = 10
DEFAULT_PRECISION = 2
DEFAULT_MIN_OUTPUT = 0
DEFAULT_MAX_OUTPUT = 100
DEFAULT_REVERSE = False

SCAN_INTERVAL = timedelta(seconds=10)

async def async_setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    async_add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    name = config.get(CONF_NAME, DEFAULT_NAME)
    input_sensor = config[CONF_INPUT_SENSOR]
    setpoint = config.get(CONF_SETPOINT)
    setpoint_sensor = config.get(CONF_SETPOINT_SENSOR)
    kp = config.get(CONF_KP, DEFAULT_KP)
    ki = config.get(CONF_KI, DEFAULT_KI)
    kd = config.get(CONF_KD, DEFAULT_KD)
    window_size = config.get(CONF_WINDOW_SIZE, DEFAULT_WINDOW_SIZE)
    precision = config.get(CONF_PRECISION, DEFAULT_PRECISION)
    min_output = config.get(CONF_MIN_OUTPUT, DEFAULT_MIN_OUTPUT)
    max_output = config.get(CONF_MAX_OUTPUT, DEFAULT_MAX_OUTPUT)
    reverse = config.get(CONF_REVERSE, DEFAULT_REVERSE)

    pid = PID(kp, ki, kd, setpoint=setpoint)
    pid.sample_time = window_size
    pid.output_limits = (min_output, max_output)
    pid.auto_mode = AutoMode.AUTO

    if reverse:
        pid.direction = PID.REVERSE
    else:
        pid.direction = PID.DIRECT

    async_add_entities(
        [
            SimplePIDController(
                name,
                input_sensor,
                setpoint,
                setpoint_sensor,
                pid,
                precision,
            )
        ]
    )

class SimplePIDController(SensorEntity):
    def __init__(
        self,
        name: str,
        input_sensor: str,
        setpoint: float | None,
        setpoint_sensor: str | None,
        pid: PID,
        precision: int,
    ) -> None:
        self._attr_name = name
        self._input_sensor = input_sensor
        self._setpoint = setpoint
        self._setpoint_sensor = setpoint_sensor
        self._pid = pid
        self._precision = precision
        self._attr_native_unit_of_measurement = "%"
        self._attr_icon = "mdi:math-integral"

    @property
    def should_poll(self) -> bool:
        return True

    def update(self) -> None:
        input_state = self.hass.states.get(self._input_sensor)
        if input_state is None:
            _LOGGER.warning("Input sensor state is None")
            return

        try:
            input_value = float(input_state.state)
        except ValueError:
            _LOGGER.warning("Invalid input sensor state")
            return

        if self._setpoint_sensor:
            setpoint_state = self.hass.states.get(self._setpoint_sensor)
            if setpoint_state is None:
                _LOGGER.warning("Setpoint sensor state is None")
                return

            try:
                self._pid.setpoint = float(setpoint_state.state)
            except ValueError:
                _LOGGER.warning("Invalid setpoint sensor state")
                return

        self._attr_native_value = round(self._pid(input_value), self._precision)
