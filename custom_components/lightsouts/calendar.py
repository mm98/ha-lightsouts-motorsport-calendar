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

from .const import CONF_TITLE_TEMPLATE, DEFAULT_TITLE_TEMPLATE, DOMAIN

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
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_calendar"
        self._attr_device_info = DeviceInfo(
            entry_type=DeviceEntryType.SERVICE,
            identifiers={(DOMAIN, entry.entry_id)},
            manufacturer="Lightsouts",
            name=entry.title or "Lightsouts",
            configuration_url="https://lightsouts.com/",
        )

    @property
    def _title_template(self) -> str:
        return self._entry.options.get(
            CONF_TITLE_TEMPLATE,
            self._entry.data.get(CONF_TITLE_TEMPLATE, DEFAULT_TITLE_TEMPLATE),
        )

    @property
    def event(self) -> CalendarEvent | None:
        """The next upcoming (or currently running) session."""
        now = dt_util.utcnow()
        for session in self.coordinator.data or []:
            if session.end >= now:
                return _to_calendar_event(session, self._title_template)
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
        tmpl = self._title_template
        return [
            _to_calendar_event(s, tmpl)
            for s in self.coordinator.data or []
            if s.end > start_utc and s.start < end_utc
        ]

    @callback
    def _handle_coordinator_update(self) -> None:
        """Push state on every refresh so the next-event sensor stays fresh."""
        super()._handle_coordinator_update()


class _SafeDict(dict):
    """Return an empty string for any unknown template variable."""

    def __missing__(self, key: str) -> str:
        return ""


def _format_title(template: str, session: Session) -> str:
    """Render the user's title template, substituting known variables.

    Unknown variables resolve to ""; malformed templates fall back to the default.
    """
    variables = _SafeDict({
        "series":       session.series_short  or "",
        "series_full":  session.series_name   or "",
        "event":        session.event_name    or "",
        "session":      session.session_name  or "",
        "circuit":      session.circuit       or "",
        "country":      session.country       or "",
        "category":     session.category      or "",
    })
    try:
        return template.format_map(variables).strip()
    except (ValueError, KeyError, IndexError):
        return DEFAULT_TITLE_TEMPLATE.format_map(variables).strip()


def _to_calendar_event(session: Session, title_template: str) -> CalendarEvent:
    summary = _format_title(title_template, session)
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
