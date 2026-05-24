# Lightsouts Motorsport Calendar — Home Assistant integration

Adds motorsport events from [lightsouts.com](https://lightsouts.com/) to Home Assistant as a calendar entity and an active-session binary sensor.

F1, MotoGP, WRC, IndyCar, NASCAR, WEC, Formula E, IMSA, Supercars, DTM, Superbike, Moto2/3, F1 Academy, F2, F3, Indy NXT, NASCAR Truck, NASCAR O'Reilly — 19 series, ~750 sessions per season.

## Features

- **One calendar entity** (`calendar.lightsouts`) merging every series you pick
- **Active-session binary sensor** (`binary_sensor.lightsouts_active_session`) — `on` while a session is live, with full session detail as attributes
- **Per-series filtering** — choose any subset of the 19 available series
- **Per-session-type filtering** — Practice, Qualifying, Sprint, Race, Other
- **Customisable event summary template** — build the calendar event title from any combination of series, event, session, circuit, and more
- **Sensible rendering of multi-day rallies** — WRC events show as all-day banners spanning the rally weekend; continuous endurance races (Le Mans 24h, Petit Le Mans 10h) stay as timed events
- **Configurable refresh interval** (1–168 hours, default 3h)
- **Times in your local timezone** — Home Assistant converts the API's UTC times to whatever your HA instance is set to
- **Available in English and Danish**

## Requirements

- Home Assistant 2024.1 or newer (uses modern `ConfigFlowResult`, `OptionsFlow`, selectors)

## Installation

### HACS (recommended)

1. HACS → Integrations → ⋮ → *Custom repositories*
2. Add `https://github.com/mm98/ha-lightsouts-motorsport-calendar` as category **Integration**
3. Install **Lightsouts Motorsport Calendar**
4. Restart Home Assistant

### Manual

1. Copy the `custom_components/lightsouts/` folder from this repository into your Home Assistant `config/custom_components/` directory
2. Restart Home Assistant

## Setup

1. **Settings → Devices & Services → Add Integration**
2. Search for **Lightsouts**
3. Pick the series and session types you want, set the refresh interval, and optionally customise the event summary template; save

Two entities will appear under the **Lightsouts** device:
- `calendar.lightsouts` — add to a Calendar dashboard card to see upcoming races
- `binary_sensor.lightsouts_active_session` — use in automations to react when a session goes live

## Options

All settings can be changed later via **Settings → Devices & Services → Lightsouts → Configure**:

| Option | Description |
|---|---|
| **Series to include** | Multi-select of the 19 available series; defaults to all |
| **Session types to include** | Practice / Qualifying / Sprint / Race / Other |
| **Refresh interval (hours)** | How often the integration polls the API (1–168, default 3) |
| **Event summary template** | Python `str.format_map` template for the calendar event title (see below) |

### Event summary template

The title of each calendar event is built from a configurable template. The default is:

```
{series}: {circuit} ({country})
```

Available variables:

| Variable | Example |
|---|---|
| `{series}` | `F1` |
| `{series_full}` | `Formula 1` |
| `{event}` | `Monaco Grand Prix` |
| `{session}` | `Race` |
| `{circuit}` | `Circuit de Monaco` |
| `{country}` | `Monaco` |
| `{category}` | `Race` |

Unknown variables are silently replaced with an empty string, so you can safely experiment. Example templates:

```
{series} | {circuit}: {session}
{series_full} — {event} ({session})
{session} @ {circuit}, {country}
```

### Session type classification

Each session is classified into exactly one bucket:

| Bucket | Includes |
|---|---|
| **Practice** | Free Practice 1–4, Practice 1–8, Warm Up |
| **Qualifying** | Qualifying 1–3, Qualifications 1–2, Sprint Qualifying, Superpole, Hyperpole, Top 10 Shootout |
| **Sprint** | Sprint, Sprint Race, Superpole Race |
| **Race** | Race 1–3, Feature Race, Opening Race, Reverse Grid Race, Rally |
| **Other** | Fallback for any future name; currently empty |

If you want only Sunday races, pick **Race** and **Sprint** (or just **Race** if you skip sprint weekends).

## Active-session binary sensor

`binary_sensor.lightsouts_active_session` is `on` for the exact duration of a live session and `off` at all other times. State transitions are scheduled at the precise start and end time of each session — they do not depend on the coordinator refresh cycle.

When `on`, the following attributes are available:

| Attribute | Description |
|---|---|
| `series` | Short series name (e.g. `F1`) |
| `series_full` | Full series name (e.g. `Formula 1`) |
| `series_slug` | API slug (e.g. `formula-1`) |
| `event` | Event/round name |
| `event_slug` | API slug for the event |
| `session` | Session name (e.g. `Race`) |
| `circuit` | Circuit name |
| `country` | Host country |
| `category` | `Practice`, `Qualifying`, `Sprint`, `Race`, or `Other` |
| `start` | Session start time (ISO-8601 UTC) |
| `end` | Session end time (ISO-8601 UTC) |
| `uid` | Stable unique identifier for the session |
| `is_main` | `true` if this is the headline session of the event |

### Example automations

Turn on a "race mode" scene when an F1 race starts:

```yaml
trigger:
  - platform: state
    entity_id: binary_sensor.lightsouts_active_session
    to: "on"
condition:
  - condition: template
    value_template: >
      {{ state_attr('binary_sensor.lightsouts_active_session', 'series') == 'F1'
         and state_attr('binary_sensor.lightsouts_active_session', 'category') == 'Race' }}
action:
  - scene: scene.race_mode
```

Send a notification when any live session ends:

```yaml
trigger:
  - platform: state
    entity_id: binary_sensor.lightsouts_active_session
    from: "on"
    to: "off"
action:
  - service: notify.mobile_app
    data:
      message: "Session over."
```

## How it works

The integration polls an unadvertised JSON API at `https://api.lightsouts.com/v1` (discovered by inspecting the lightsouts.com web app). The endpoints used are:

- `GET /series` — list of available motorsport series
- `GET /series/{slug}` — full season schedule for a series

Sessions are merged, classified, optionally filtered, and exposed as Home Assistant `CalendarEvent` objects (calendar entity) and live state with attributes (binary sensor).

Since the API is undocumented, it could change without notice. If it does, please open an issue.

### Being a polite API citizen

The integration takes care to minimise load on the lightsouts.com infrastructure:

- **Limited concurrency** — at most 4 series are fetched in parallel per refresh, instead of bursting all 19 simultaneously
- **Conditional requests** — `ETag` is cached per URL and sent back as `If-None-Match` on the next refresh; when the API replies `304 Not Modified` we keep the previous payload, so almost every refresh after the first is zero-body
- **Cloudflare-friendly defaults** — the 3 hour default refresh interval is far above the API's `max-age=900` cache window, so we don't trigger cache misses unnecessarily

Net result: roughly 800 KB/day of traffic (a single full payload, then mostly `304`s), almost all of it served from Cloudflare's edge cache rather than the origin.

## Credits

All event data comes from [lightsouts.com](https://lightsouts.com/) — a calendar for motorsport events maintained by its author. If this integration is useful to you, consider supporting them through the donation link on their site.

## License

MIT — see [LICENSE](LICENSE).
