"""Switch platform for PID Controller."""

from homeassistant.components.switch import SwitchEntity
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.entity import EntityCategory

from .entity import BasePIDEntity

SWITCH_ENTITIES = [
    {"key": "auto_mode", "name": "Auto Mode", "default_state": True},
    {
        "key": "proportional_on_measurement",
        "name": "Proportional on Measurement",
        "default_state": False,
    },
    {
        "key": "windup_protection",
        "name": "Windup Protection",
        "default_state": True,
    },
]


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    async_add_entities([PIDOptionSwitch(hass, entry, desc) for desc in SWITCH_ENTITIES])


class PIDOptionSwitch(SwitchEntity, RestoreEntity):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, desc: dict) -> None:
        BasePIDEntity.__init__(self, hass, entry, desc["key"], desc["name"])

        self._attr_entity_category = EntityCategory.CONFIG
        self._state = desc["default_state"]

    async def async_added_to_hass(self) -> None:
        """Restore previous state if available."""
        await super().async_added_to_hass()
        if (last_state := await self.async_get_last_state()) is not None:
            self._state = last_state.state == "on"

    @property
    def is_on(self) -> bool:
        return self._state

    async def async_turn_on(self, **kwargs) -> None:
        self._state = True
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs) -> None:
        self._state = False
        self.async_write_ha_state()
