"""Calendar platform for the Lightsouts motorsport integration."""
from __future__ import annotations

from datetime import datetime, time, timedelta
from typing import TYPE_CHECKING

from homeassistant.components.calendar import CalendarEntity, CalendarEvent
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
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
    """Register the Lightsouts calendar entity."""
    coordinator: LightsoutsCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([LightsoutsCalendar(coordinator, entry)])


class LightsoutsCalendar(CoordinatorEntity["LightsoutsCoordinator"], CalendarEntity):
    """A calendar entity backed by motorsport sessions from lightsouts.com."""

    _attr_has_entity_name = True
    _attr_name = None
    _attr_icon = "mdi:flag-checkered"

    def __init__(self, coordinator: LightsoutsCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_calendar"
        self._attr_device_info = DeviceInfo(
            entry_type=DeviceEntryType.SERVICE,
            identifiers={(DOMAIN, entry.entry_id)},
            manufacturer="Lightsouts",
            name=entry.title or "Lightsouts",
            configuration_url="https://lightsouts.com/",
        )

    @property
    def event(self) -> CalendarEvent | None:
        """The next upcoming (or currently running) session."""
        now = dt_util.utcnow()
        for session in self.coordinator.data or []:
            if session.end >= now:
                return _to_calendar_event(session)
        return None

    async def async_get_events(
        self,
        hass: HomeAssistant,
        start_date: datetime,
        end_date: datetime,
    ) -> list[CalendarEvent]:
        """Return sessions overlapping the given window."""
        start_utc = dt_util.as_utc(start_date)
        end_utc = dt_util.as_utc(end_date)
        return [
            _to_calendar_event(s)
            for s in self.coordinator.data or []
            if s.end > start_utc and s.start < end_utc
        ]

    @callback
    def _handle_coordinator_update(self) -> None:
        """Push state on every refresh so the next-event sensor stays fresh."""
        super()._handle_coordinator_update()


def _to_calendar_event(session: Session) -> CalendarEvent:
    summary = f"{session.series_short} — {session.event_name}: {session.session_name}"
    location_parts = [p for p in (session.circuit, session.country) if p]
    location = ", ".join(location_parts) or None
    description_lines = [
        f"Series: {session.series_name}",
        f"Event: {session.event_name}",
        f"Session: {session.session_name}",
    ]
    if location:
        description_lines.append(f"Location: {location}")
    description_lines.append(f"Source: https://lightsouts.com/{session.series_slug}")

    if session.is_all_day:
        start = session.start.date()
        # iCal-style: end date is exclusive. If the session ends partway through
        # a day, include that whole day by rounding up.
        end_date = session.end.date()
        if session.end.timetz().replace(tzinfo=None) != time(0, 0):
            end_date = end_date + timedelta(days=1)
        return CalendarEvent(
            start=start,
            end=end_date,
            summary=summary,
            location=location,
            description="\n".join(description_lines),
            uid=session.uid,
        )

    return CalendarEvent(
        start=session.start,
        end=session.end,
        summary=summary,
        location=location,
        description="\n".join(description_lines),
        uid=session.uid,
    )
