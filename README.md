# Lightsouts Motorsport Calendar — Home Assistant integration

Adds motorsport events from [lightsouts.com](https://lightsouts.com/) to Home Assistant as a calendar entity.

F1, MotoGP, WRC, IndyCar, NASCAR, WEC, Formula E, IMSA, Supercars, DTM, Superbike, Moto2/3, F1 Academy, F2, F3, Indy NXT, NASCAR Truck, NASCAR O'Reilly — 19 series, ~750 sessions per season.

## Features

- **One calendar entity** (`calendar.lightsouts`) merging every series you pick
- **Per-series filtering** — choose any subset of the 19 available series
- **Per-session-type filtering** — Practice, Qualifying, Sprint, Race, Other
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
3. Pick the series and session types you want, set the refresh interval, save

A calendar entity `calendar.lightsouts` will appear. Add it to a Calendar dashboard card to see upcoming races.

## Options

All settings can be changed later via **Settings → Devices & Services → Lightsouts → Configure**:

| Option | Description |
|---|---|
| **Series to include** | Multi-select of the 19 available series; defaults to all |
| **Session types to include** | Practice / Qualifying / Sprint / Race / Other |
| **Refresh interval (hours)** | How often the integration polls the API (1–168, default 3) |

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

## How it works

The integration polls an unadvertised JSON API at `https://api.lightsouts.com/v1` (discovered by inspecting the lightsouts.com web app). The endpoints used are:

- `GET /series` — list of available motorsport series
- `GET /series/{slug}` — full season schedule for a series

Sessions are merged, classified, optionally filtered, and exposed as Home Assistant `CalendarEvent` objects.

Since the API is undocumented, it could change without notice. If it does, please open an issue.

## Credits

All event data comes from [lightsouts.com](https://lightsouts.com/) — a calendar for motorsport events maintained by its author. If this integration is useful to you, consider supporting them through the donation link on their site.

## License

MIT — see [LICENSE](LICENSE).
