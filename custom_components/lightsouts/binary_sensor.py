"""Binary sensor for the currently active motorsport session."""
from __future__ import annotations

from collections.abc import Callable
from datetime import datetime
from typing import TYPE_CHECKING, Any

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_point_in_time
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from .const import DOMAIN

if TYPE_CHECKING:
    from .coordinator import LightsoutsCoordinator, Session


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Register the active-session binary sensor."""
    coordinator: LightsoutsCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([LightsoutsActiveSensor(coordinator, entry)])


class LightsoutsActiveSensor(
    CoordinatorEntity["LightsoutsCoordinator"], BinarySensorEntity
):
    """On while a session is live; attributes carry the full session detail."""

    _attr_has_entity_name = True
    _attr_name = "Active session"
    _attr_icon = "mdi:flag-checkered"

    def __init__(self, coordinator: LightsoutsCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_active_session"
        self._attr_device_info = DeviceInfo(
            entry_type=DeviceEntryType.SERVICE,
            identifiers={(DOMAIN, entry.entry_id)},
            manufacturer="Lightsouts",
            name=entry.title or "Lightsouts",
            configuration_url="https://lightsouts.com/",
        )
        self._unsub_next: Callable[[], None] | None = None

    def _active_session(self) -> Session | None:
        now = dt_util.utcnow()
        for session in self.coordinator.data or []:
            if session.start <= now < session.end:
                return session
        return None

    def _next_change(self) -> datetime | None:
        """Nearest future session start or end, to know when to flip state."""
        now = dt_util.utcnow()
        candidates: list[datetime] = []
        for session in self.coordinator.data or []:
            if session.start > now:
                candidates.append(session.start)
            if session.end > now:
                candidates.append(session.end)
        return min(candidates) if candidates else None

    @property
    def is_on(self) -> bool:
        return self._active_session() is not None

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        session = self._active_session()
        if session is None:
            return None
        return {
            "series": session.series_short,
            "series_full": session.series_name,
            "series_slug": session.series_slug,
            "event": session.event_name,
            "event_slug": session.event_slug,
            "session": session.session_name,
            "circuit": session.circuit,
            "country": session.country,
            "category": session.category,
            "start": session.start.isoformat(),
            "end": session.end.isoformat(),
            "uid": session.uid,
            "is_main": session.is_main,
        }

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        self._reschedule()

    async def async_will_remove_from_hass(self) -> None:
        self._cancel_next()

    @callback
    def _handle_coordinator_update(self) -> None:
        self._reschedule()
        super()._handle_coordinator_update()

    @callback
    def _reschedule(self) -> None:
        self._cancel_next()
        if (next_at := self._next_change()) is not None:
            self._unsub_next = async_track_point_in_time(
                self.hass, self._on_time_reached, next_at
            )

    @callback
    def _cancel_next(self) -> None:
        if self._unsub_next:
            self._unsub_next()
            self._unsub_next = None

    @callback
    def _on_time_reached(self, _now: datetime) -> None:
        self._reschedule()
        self.async_write_ha_state()
