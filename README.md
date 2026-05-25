# Lightsouts Motorsport Calendar — Home Assistant integration

Adds motorsport events from [lightsouts.com](https://lightsouts.com/) to Home Assistant as a calendar and a live-session sensor.

F1, MotoGP, WRC, IndyCar, NASCAR, WEC, Formula E, IMSA, Supercars, DTM, Superbike, Moto2/3, F1 Academy, F2, F3, Indy NXT, NASCAR Truck, NASCAR O'Reilly — 19 series, ~750 sessions per season.

## Features

- **Calendar** (`calendar.lightsouts`) — all sessions from every series you pick, in one place
- **Live-session sensor** (`binary_sensor.lightsouts_active_session`) — turns on while a session is live and always shows the current or next session's details
- **Per-series filtering** — choose any subset of the 19 available series
- **Per-session-type filtering** — Practice, Qualifying, Sprint, Race, Other
- **Customisable event title and description** — build the calendar event title and detail text from any combination of series, event, session, circuit, and more
- **Sensible rendering of multi-day rallies** — WRC events show as all-day banners spanning the rally weekend; continuous endurance races (Le Mans 24h, Petit Le Mans 10h) stay as timed events
- **Configurable refresh interval** (1–168 hours, default 3h)
- **Times in your local timezone** — Home Assistant converts UTC times to whatever your HA instance is set to
- **Available in English and Danish**

## Requirements

- Home Assistant 2024.1 or newer

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
3. Pick the series and session types you want, set the refresh interval, and optionally customise the event title; save

Two items will appear under the **Lightsouts** device:
- `calendar.lightsouts` — add to a Calendar dashboard card to see upcoming races
- `binary_sensor.lightsouts_active_session` — use in automations to react when a session goes live

## Options

All settings can be changed later via **Settings → Devices & Services → Lightsouts → Configure**:

| Option | Description |
|---|---|
| **Series to include** | Choose which of the 19 series to show; defaults to all |
| **Session types to include** | Practice / Qualifying / Sprint / Race / Other |
| **Refresh interval (hours)** | How often the calendar checks for updates (1–168, default 3) |
| **Event title template** | Customise the title of each calendar event using placeholders (see below) |
| **Event description template** | Customise the detail text shown when you open an event (see below) |

### Event title template

The title of each calendar event is built from a pattern you define. The default is:

```
{series}: {circuit} ({country})
```

Available placeholders:

| Placeholder | Example |
|---|---|
| `{series}` | `F1` |
| `{series_full}` | `Formula 1` |
| `{event}` | `Monaco Grand Prix` |
| `{session}` | `Race` |
| `{circuit}` | `Circuit de Monaco` |
| `{country}` | `Monaco` |
| `{category}` | `Race` |

Unrecognised placeholders are ignored, so you can experiment freely. More examples:

```
{series} | {circuit}: {session}
{series_full} — {event} ({session})
{session} @ {circuit}, {country}
```

### Event description template

The detail text shown when you open a calendar event is also configurable. The default is:

```
Series: {series_full}
Event: {event}
Session: {session}
Category: {category}
Location: {location}
Source: https://lightsouts.com/{series_slug}
```

The same placeholders are available as for the title, plus `{series_slug}` and `{event_slug}`. Lines where a placeholder has no value (e.g. `Location:` when no circuit is known) are hidden automatically.

### Session type classification

Each session falls into one of these categories:

| Category | Includes |
|---|---|
| **Practice** | Free Practice 1–4, Practice 1–8, Warm Up |
| **Qualifying** | Qualifying 1–3, Qualifications 1–2, Sprint Qualifying, Superpole, Hyperpole, Top 10 Shootout |
| **Sprint** | Sprint, Sprint Race, Superpole Race |
| **Race** | Race 1–3, Feature Race, Opening Race, Reverse Grid Race, Rally |
| **Other** | Anything that doesn't match the above |

If you want only Sunday races, pick **Race** and **Sprint** (or just **Race** if you skip sprint weekends).

## Live-session sensor

`binary_sensor.lightsouts_active_session` turns on for the exact duration of a live session and off at all other times. It reacts at the precise start and end time of each session, not just when the calendar refreshes.

The sensor always shows details — the current session when on, or the next upcoming session when off. The `start` and `end` values indicate which session is shown.

| Detail | Description |
|---|---|
| `series` | Short series name (e.g. `F1`) |
| `series_full` | Full series name (e.g. `Formula 1`) |
| `series_slug` | Internal series identifier (e.g. `formula-1`) |
| `event` | Event/round name |
| `event_slug` | Internal event identifier |
| `session` | Session name (e.g. `Race`) |
| `circuit` | Circuit name |
| `country` | Host country |
| `category` | `Practice`, `Qualifying`, `Sprint`, `Race`, or `Other` |
| `start` | Session start time (UTC) |
| `end` | Session end time (UTC) |
| `uid` | Unique identifier for the session |
| `is_main` | `true` if this is the headline session of the event |

### Example automations

**Notify when any race starts** (fires at the exact start time):

```yaml
trigger:
  - platform: state
    entity_id: binary_sensor.lightsouts_active_session
    to: "on"
condition:
  - condition: template
    value_template: "{{ state_attr('binary_sensor.lightsouts_active_session', 'category') == 'Race' }}"
action:
  - service: notify.mobile_app_your_phone
    data:
      title: "🏁 Race starting"
      message: >
        {{ state_attr('binary_sensor.lightsouts_active_session', 'series') }}:
        {{ state_attr('binary_sensor.lightsouts_active_session', 'session') }}
        at {{ state_attr('binary_sensor.lightsouts_active_session', 'circuit') }}
```

**Turn on a scene while an F1 race is live** (stays active for the full session duration):

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

**Notify when a session ends**:

```yaml
trigger:
  - platform: state
    entity_id: binary_sensor.lightsouts_active_session
    from: "on"
    to: "off"
action:
  - service: notify.mobile_app_your_phone
    data:
      message: "Session over."
```

## Network efficiency

The integration is designed to be a considerate user of the lightsouts.com infrastructure:

- **Concurrency limit** — at most 4 series are fetched in parallel per refresh, instead of bursting all 19 simultaneously
- **Fetch only selected series** — only the series you have chosen are downloaded; the full series index is never fetched after setup
- **ETag / conditional requests** — each response's ETag is cached and sent back as `If-None-Match` on the next refresh; when the API replies `304 Not Modified` the previous payload is reused, so most refreshes transfer almost nothing
- **Sensible default interval** — the 3 hour default is well above the API's `max-age=900` cache window, so requests are mostly served from Cloudflare's edge rather than the origin

Net result: roughly 800 KB/day of traffic (one full download on the first refresh, then mostly `304`s).

## Credits

All event data comes from [lightsouts.com](https://lightsouts.com/) — a calendar for motorsport events maintained by its author. If this integration is useful to you, consider supporting them through the donation link on their site.

## License

MIT — see [LICENSE](LICENSE).
