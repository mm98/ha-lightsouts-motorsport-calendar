"""Constants for the Lightsouts motorsport calendar integration."""
from __future__ import annotations

DOMAIN = "lightsouts"
INTEGRATION_VERSION = "0.1.0"  # keep in sync with manifest.json

API_BASE = "https://api.lightsouts.com/v1"
API_SERIES_INDEX = f"{API_BASE}/series"
API_SERIES_DETAIL = f"{API_BASE}/series/{{slug}}"

REQUEST_TIMEOUT = 30

# Limit how many series we fetch in parallel so we don't fire 19 simultaneous
# requests at the origin on every refresh.
MAX_CONCURRENT_REQUESTS = 4

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36"
)

CONF_SERIES = "series"
CONF_SESSION_TYPES = "session_types"
CONF_UPDATE_INTERVAL_HOURS = "update_interval_hours"
CONF_TITLE_TEMPLATE = "title_template"

# Variables available to the title template: {series}, {series_full}, {event},
# {session}, {circuit}, {country}, {category}
DEFAULT_TITLE_TEMPLATE = "{series} - {event}: {session}"

SESSION_TYPE_PRACTICE = "practice"
SESSION_TYPE_QUALIFYING = "qualifying"
SESSION_TYPE_SPRINT = "sprint"
SESSION_TYPE_RACE = "race"
SESSION_TYPE_OTHER = "other"

ALL_SESSION_TYPES: list[str] = [
    SESSION_TYPE_PRACTICE,
    SESSION_TYPE_QUALIFYING,
    SESSION_TYPE_SPRINT,
    SESSION_TYPE_RACE,
    SESSION_TYPE_OTHER,
]
DEFAULT_SESSION_TYPES = list(ALL_SESSION_TYPES)

DEFAULT_UPDATE_INTERVAL_HOURS = 3
MIN_UPDATE_INTERVAL_HOURS = 1
MAX_UPDATE_INTERVAL_HOURS = 168  # one week
