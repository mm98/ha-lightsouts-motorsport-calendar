"""Data fetching for Lightsouts motorsport calendar."""
from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

import aiohttp
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    ALL_SESSION_TYPES,
    API_SERIES_DETAIL,
    API_SERIES_INDEX,
    CONF_SERIES,
    CONF_SESSION_TYPES,
    CONF_UPDATE_INTERVAL_HOURS,
    DEFAULT_UPDATE_INTERVAL_HOURS,
    DOMAIN,
    REQUEST_TIMEOUT,
    SESSION_TYPE_OTHER,
    SESSION_TYPE_PRACTICE,
    SESSION_TYPE_QUALIFYING,
    SESSION_TYPE_RACE,
    SESSION_TYPE_SPRINT,
)

_LOGGER = logging.getLogger(__name__)


# Sessions longer than this are treated as all-day events. Picked so that
# 24h endurance races (Le Mans = 1440 min) stay as timed events while WRC
# rallies (~3960 min for a 4-day rally) become all-day banners.
ALL_DAY_THRESHOLD_MINUTES = 25 * 60


@dataclass(slots=True)
class Session:
    """A single motorsport session flattened from the lightsouts API."""

    uid: str
    series_slug: str
    series_name: str
    series_short: str
    event_name: str
    event_slug: str
    circuit: str | None
    country: str | None
    session_name: str
    start: datetime
    end: datetime
    is_main: bool
    category: str
    is_all_day: bool


class LightsoutsCoordinator(DataUpdateCoordinator[list[Session]]):
    """Fetches and refreshes motorsport sessions from lightsouts.com."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.entry = entry
        self._session = async_get_clientsession(hass)
        hours = entry.options.get(
            CONF_UPDATE_INTERVAL_HOURS,
            entry.data.get(CONF_UPDATE_INTERVAL_HOURS, DEFAULT_UPDATE_INTERVAL_HOURS),
        )
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(hours=hours),
        )

    @property
    def _selected_series(self) -> list[str] | None:
        """Series slugs the user wants, or None for 'all available'."""
        raw = self.entry.options.get(CONF_SERIES, self.entry.data.get(CONF_SERIES))
        if not raw:
            return None
        return list(raw)

    @property
    def _selected_session_types(self) -> set[str]:
        raw = self.entry.options.get(
            CONF_SESSION_TYPES,
            self.entry.data.get(CONF_SESSION_TYPES, list(ALL_SESSION_TYPES)),
        )
        return set(raw) if raw else set(ALL_SESSION_TYPES)

    async def _async_update_data(self) -> list[Session]:
        """Fetch series index, then each selected series' events in parallel."""
        try:
            available = await self._fetch_series_index()
        except (aiohttp.ClientError, asyncio.TimeoutError) as err:
            raise UpdateFailed(f"Failed to fetch series index: {err}") from err

        wanted = self._selected_series
        slugs = [s["slug"] for s in available if wanted is None or s["slug"] in wanted]
        if not slugs:
            return []

        results = await asyncio.gather(
            *(self._fetch_series(slug) for slug in slugs), return_exceptions=True
        )

        sessions: list[Session] = []
        for slug, result in zip(slugs, results, strict=True):
            if isinstance(result, BaseException):
                _LOGGER.warning("Failed to fetch series %s: %s", slug, result)
                continue
            sessions.extend(self._flatten_series(result))

        allowed = self._selected_session_types
        sessions = [s for s in sessions if s.category in allowed]
        sessions.sort(key=lambda s: s.start)
        return sessions

    async def _fetch_series_index(self) -> list[dict[str, Any]]:
        async with asyncio.timeout(REQUEST_TIMEOUT):
            async with self._session.get(API_SERIES_INDEX) as resp:
                resp.raise_for_status()
                return await resp.json()

    async def _fetch_series(self, slug: str) -> dict[str, Any]:
        url = API_SERIES_DETAIL.format(slug=slug)
        async with asyncio.timeout(REQUEST_TIMEOUT):
            async with self._session.get(url) as resp:
                resp.raise_for_status()
                return await resp.json()

    @staticmethod
    def _flatten_series(payload: dict[str, Any]) -> list[Session]:
        series_name = payload.get("name") or payload.get("slug") or "Unknown"
        series_short = payload.get("nameAlt") or series_name
        series_slug = payload.get("slug", "")
        out: list[Session] = []
        for event in payload.get("events") or []:
            if event.get("tba"):
                continue
            event_name = event.get("name") or ""
            event_slug = event.get("slug") or ""
            circuit = (event.get("circuit") or {}).get("name")
            country = (event.get("country") or {}).get("name") or (
                (event.get("circuit") or {}).get("country") or {}
            ).get("name")
            for s in event.get("sessions") or []:
                start = _parse_session_start(s.get("date"), s.get("time"))
                if start is None:
                    continue
                duration = int(s.get("duration") or 60)
                end = start + timedelta(minutes=duration)
                sid = s.get("id")
                session_name = s.get("name") or "Session"
                uid = (
                    f"{series_slug}:{event_slug}:{sid}"
                    if sid
                    else f"{series_slug}:{event_slug}:{session_name}:{start.isoformat()}"
                )
                out.append(
                    Session(
                        uid=uid,
                        series_slug=series_slug,
                        series_name=series_name,
                        series_short=series_short,
                        event_name=event_name,
                        event_slug=event_slug,
                        circuit=circuit,
                        country=country,
                        session_name=session_name,
                        start=start,
                        end=end,
                        is_main=bool(s.get("main")),
                        category=classify_session(session_name),
                        is_all_day=duration >= ALL_DAY_THRESHOLD_MINUTES,
                    )
                )
        return out


def classify_session(name: str) -> str:
    """Bucket a session into one of: practice, qualifying, sprint, race, other.

    Priority matters — checked top-to-bottom; first match wins.
    """
    n = (name or "").strip().lower()
    if n in {"sprint", "sprint race", "superpole race"}:
        return SESSION_TYPE_SPRINT
    if "practice" in n or "warm up" in n:
        return SESSION_TYPE_PRACTICE
    if any(
        k in n
        for k in ("qualifying", "qualifications", "superpole", "hyperpole", "shootout")
    ):
        return SESSION_TYPE_QUALIFYING
    if "sprint" in n:
        return SESSION_TYPE_SPRINT
    if "race" in n or "rally" in n:
        return SESSION_TYPE_RACE
    return SESSION_TYPE_OTHER


def _parse_session_start(date_str: str | None, time_str: str | None) -> datetime | None:
    """Return a tz-aware UTC datetime for a session.

    Two API shapes are seen in the wild:
      - F1, MotoGP, etc.: date="2026-05-24", time="20:00"
      - WRC (rally): date="2026-05-28T08:30:00Z", time=null
    """
    if not date_str:
        return None
    try:
        if "T" in date_str:
            return datetime.fromisoformat(date_str.replace("Z", "+00:00")).astimezone(
                timezone.utc
            )
        return datetime.fromisoformat(
            f"{date_str}T{time_str or '00:00'}:00+00:00"
        )
    except ValueError:
        return None
