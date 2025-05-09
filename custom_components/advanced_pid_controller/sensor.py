from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType
from homeassistant.helpers.entity import Entity

from .pid_controller import PIDControllerWrapper
from .const import DOMAIN, CONF_SENSOR_ENTITY_ID

import logging

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the PID output sensor."""
    name = entry.data.get("name", "PID Controller")
 
    sensor_entity_id = entry.options.get(
        CONF_SENSOR_ENTITY_ID, entry.data.get(CONF_SENSOR_ENTITY_ID)
    )

    entity = PIDOutputSensor(
        name=name,
        entry_id=entry.entry_id,
        hass=hass,
        sensor_entity_id=sensor_entity_id,
    )

    async_add_entities([entity], update_before_add=True)


class PIDOutputSensor(SensorEntity):
    """Sensor that shows the output of the PID controller."""

    def __init__(self, name: str, entry_id: str, hass: HomeAssistant, sensor_entity_id: str) -> None:
        self._attr_name = f"{name} PID Output"
        self._attr_unique_id = f"{entry_id}_pid_output"
        self._attr_native_unit_of_measurement = "%"
        self._state: float = 0.0
        self._entry_id = entry_id
        self.hass = hass
        self._pid = PIDControllerWrapper()
        self._sensor_entity_id = sensor_entity_id

    @property
    def native_value(self) -> StateType:
        return round(self._state, 2)

    async def async_update(self) -> None:
        """Update the PID output based on the input sensor."""

        # Stap 1: lees de inputwaarde van de opgegeven sensor
        state = self.hass.states.get(self._sensor_entity_id)
        if state is None or state.state in ("unknown", "unavailable"):
            _LOGGER.warning("Input sensor %s is not available", self._sensor_entity_id)
            return

        try:
            current_input = float(state.state)
        except ValueError:
            _LOGGER.warning("Cannot convert input sensor value: %s", state.state)
            return

        # Stap 2: haal PID-instellingen op uit number-entiteiten
        values = {}
        for key in [
            "setpoint", "kp", "ki", "kd", "output_min", "output_max", "sample_time"
        ]:
            number_entity_id = f"number.{self._entry_id}_{key}"
            number_state = self.hass.states.get(number_entity_id)
            if number_state and number_state.state not in ("unknown", "unavailable"):
                try:
                    values[key] = float(number_state.state)
                except ValueError:
                    _LOGGER.warning("Invalid state for %s: %s", key, number_state.state)

        self._pid.update_parameters(values)

        # Stap 3: bereken PID-uitvoer
        self._state = self._pid.compute(current_input)
