from homeassistant.components.number import NumberEntity, NumberEntityDescription
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
    """Set up number entities for Advanced PID Controller."""
    name = entry.data.get("name", "PID Controller")
    async_add_entities([
        PIDSetpointNumber(name)
    ])


class PIDSetpointNumber(NumberEntity):
    """A simple number entity for the PID setpoint."""

    def __init__(self, name: str) -> None:
        self._attr_name = f"{name} Setpoint"
        self._attr_unique_id = f"{name.lower().replace(' ', '_')}_setpoint"
        self._attr_min_value = 0.0
        self._attr_max_value = 100.0
        self._attr_step = 1.0
        self._value = 20.0  # default setpoint

    @property
    def value(self) -> float:
        return self._value

    async def async_set_value(self, value: float) -> None:
        self._value = value
        self.async_write_ha_state()
