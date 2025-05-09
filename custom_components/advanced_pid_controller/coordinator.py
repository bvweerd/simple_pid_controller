from datetime import timedelta
import logging

from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)
from homeassistant.core import HomeAssistant

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class PIDDataCoordinator(DataUpdateCoordinator[float]):
    """Class to manage updating the PID controller output."""

    def __init__(self, hass: HomeAssistant, name: str, update_interval: float, update_method):
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{name}_coordinator",
            update_interval=timedelta(seconds=update_interval),
        )
        self.update_method = update_method

    async def _async_update_data(self) -> float:
        """Fetch the latest PID output."""
        try:
            return await self.update_method()
        except Exception as err:
            raise UpdateFailed(f"PID update failed: {err}") from err
