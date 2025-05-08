from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.entity import Entity

from .const import DOMAIN

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up sensor entities for Advanced PID Controller."""
    name = entry.data.get("name", "PID Controller")
    async_add_entities([
        PIDOutputSensor(name)
    ])


class PIDOutputSensor(SensorEntity):
    """A simple sensor representing PID output."""

    def __init__(self, name: str) -> None:
        self._attr_name = f"{name} Output"
        self._attr_unique_id = f"{name.lower().replace(' ', '_')}_output"
        self._attr_native_unit_of_measurement = "%"
        self._state = 0.0

    @property
    def native_value(self) -> float:
        return self._state

    # In een echte controller zou je deze updaten via een coordinator of in reactie op input
    def update_output(self, value: float) -> None:
        self._state = value
        self.async_write_ha_state()
