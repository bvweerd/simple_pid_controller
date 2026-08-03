"""Coordinator for Simple PID Controller."""

from collections.abc import Awaitable, Callable
from datetime import timedelta
import logging

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


# simple_pid returns None while the controller is in manual mode, and the
# output sensor already renders that as an unknown state, so None is part of
# the coordinator's data type rather than an error.
class PIDDataCoordinator(DataUpdateCoordinator[float | None]):
    """Coordinator responsible for scheduling PID controller updates."""

    # homeassistant-stubs types this as Incomplete, which erases the return
    # type; Home Assistant itself declares it Callable[[], Awaitable[_DataT]].
    update_method: Callable[[], Awaitable[float | None]]

    def __init__(
        self,
        hass: HomeAssistant,
        name: str,
        update_method: Callable[[], Awaitable[float | None]],
        interval: float = 10,
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{name}_coordinator",
            update_interval=timedelta(seconds=interval),
        )
        self.update_method = update_method

    async def _async_update_data(self) -> float | None:
        """Perform the PID calculation and return the new output value."""
        try:
            return await self.update_method()
        except Exception as err:
            raise UpdateFailed(f"PID update failed: {err}") from err
