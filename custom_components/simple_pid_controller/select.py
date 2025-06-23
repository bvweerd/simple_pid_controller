from homeassistant.components.select import SelectEntity
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.helpers.entity import EntityCategory

from .entity import BasePIDEntity

START_MODE_OPTIONS = [
    "Zero start",  # Simple and safe, but may cause jumps
    "Last known value",  # Continuous, smooth resumption
    "Startup value",  # User-defined default at startup
]


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up the PID start mode select entity."""
    coordinator = entry.runtime_data.coordinator
    async_add_entities(
        [PIDStartModeSelect(hass, entry, "start_mode", "PID Start Mode", coordinator)]
    )


class PIDStartModeSelect(BasePIDEntity, SelectEntity, RestoreEntity):
    """Representation of the PID start mode selection."""

    def __init__(self, hass, entry, key, name, coordinator):
        super().__init__(hass, entry, key, name)
        self._attr_options = START_MODE_OPTIONS
        self._attr_current_option = START_MODE_OPTIONS[0]
        self._attr_entity_category = EntityCategory.CONFIG
        self.coordinator = coordinator  # if needed later

    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        if option in self._attr_options:
            self._attr_current_option = option
            self.async_write_ha_state()

    async def async_added_to_hass(self):
        """Restore previous state."""
        await super().async_added_to_hass()
        if (
            last_state := await self.async_get_last_state()
        ) and last_state.state in self._attr_options:
            self._attr_current_option = last_state.state
