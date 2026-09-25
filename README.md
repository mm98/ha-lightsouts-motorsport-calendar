# Lightsouts Motorsport Calendar for Home Assistant

See upcoming motorsport sessions from [lightsouts.com](https://lightsouts.com/) in Home Assistant: a calendar with every session of the series you follow, and a sensor that turns on while a session is live, for automations like "turn on the race scene when the F1 race starts".

It covers 19 series, about 750 sessions per season: F1, F2, F3, F1 Academy, MotoGP, Moto2, Moto3, WRC, WEC, IMSA, IndyCar, Indy NXT, NASCAR, NASCAR O'Reilly, NASCAR Truck, Formula E, Supercars, DTM and Superbike.

Available in English and Danish.

## Install

Requires Home Assistant 2024.1 or newer.

### With HACS

Select this button to open the integration in HACS, then select **Download**:

[![Open this repository in HACS](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=mm98&repository=ha-lightsouts-motorsport-calendar&category=integration)

Or add it yourself:

1. Open **HACS**, select the three dots at the top right and pick **Custom repositories**.
2. Enter `https://github.com/mm98/ha-lightsouts-motorsport-calendar`, choose the type **Integration** and select **Add**.
3. Search HACS for **Lightsouts Motorsport Calendar**, open it and select **Download**.
4. Restart Home Assistant.

### Without HACS

1. Copy the `custom_components/lightsouts` folder from this repository into the `custom_components` folder of your Home Assistant configuration.
2. Restart Home Assistant.

## Set up

Go to **Settings > Devices & services**, select **Add integration** and pick **Lightsouts**. Or select this button:

[![Add the Lightsouts integration](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=lightsouts)

Then choose what to show:

| Setting | What it does |
|---|---|
| Series to include | Which of the 19 series to show. All of them by default. |
| Session types to include | Practice, Qualifying, Sprint, Race and Other. See **Session types** below. |
| Refresh interval (hours) | How often the calendar checks lightsouts.com for changes: 1 to 168 hours, 3 by default. |
| Event title template | How each event in the calendar is named. See below. |
| Event description template | The text you see when you open an event. See below. |

You can change these settings later with **Configure** on the integration.

### Event title and description

The default title is `{series}: {circuit} ({country})`, for example `F1: Circuit de Monaco (Monaco)`. The default description is:

```
Series: {series_full},
Event: {event},
Session: {session},
Location: {location}
```

You can use these placeholders in both:

| Placeholder | Example |
|---|---|
| `{series}` | F1 |
| `{series_full}` | Formula 1 |
| `{event}` | Monaco Grand Prix |
| `{session}` | Race |
| `{circuit}` | Circuit de Monaco |
| `{country}` | Monaco |
| `{location}` | Circuit de Monaco, Monaco |
| `{category}` | Race |
| `{series_slug}` and `{event_slug}` | The series and the event as they appear in lightsouts.com links, for example `https://lightsouts.com/{series_slug}` |

Placeholders the integration doesn't know stay empty, so you can try things out freely. In the description, a line is left out when it ends with a placeholder that has no value, for example **Location:** when no circuit is known.

Some other titles to try:

```
{series} | {circuit}: {session}
{series_full} - {event} ({session})
{session} @ {circuit}, {country}
```

### Session types

Every session belongs to one of these types:

| Type | Includes |
|---|---|
| Practice | Free Practice 1 to 4, Practice 1 to 8, Warm Up |
| Qualifying | Qualifying 1 to 3, Qualifications 1 and 2, Sprint Qualifying, Superpole, Hyperpole, Top 10 Shootout |
| Sprint | Sprint, Sprint Race, Superpole Race |
| Race | Race 1 to 3, Feature Race, Opening Race, Reverse Grid Race, Rally |
| Other | Everything else |

For only the races, pick **Race**, and **Sprint** too if you want the sprint races.

## What you get

### A calendar

`calendar.lightsouts` shows every session of the series and session types you picked, in your own time zone. Add it to a **Calendar** card to see what's coming up.

Rallies such as WRC show as all-day events across the rally weekend. Long endurance races, such as the Le Mans 24 Hours, keep their real start and end times.

### A live session sensor

`binary_sensor.lightsouts_active_session` is on while a session is live and off the rest of the time. It switches at the exact start and end of each session, not only when the calendar checks for changes.

Open it to see the session that is live, or the next one when nothing is:

| Detail | Shows |
|---|---|
| series | The short series name, for example F1 |
| series_full | The full series name, for example Formula 1 |
| event | The event, for example Monaco Grand Prix |
| session | The session, for example Race |
| circuit | The circuit |
| country | The country |
| category | Practice, Qualifying, Sprint, Race or Other |
| start and end | When the session starts and ends, in UTC |
| is_main | true for the main session of the event |

## Examples

Create a new automation, open the three dots at the top right, pick **Edit in YAML** and paste one of these.

A notification when a race starts:

```yaml
triggers:
  - trigger: state
    entity_id: binary_sensor.lightsouts_active_session
    to: "on"
conditions:
  - condition: state
    entity_id: binary_sensor.lightsouts_active_session
    attribute: category
    state: Race
actions:
  - action: notify.notify
    data:
      title: Race starting
      message: >
        {{ trigger.to_state.attributes.series }}:
        {{ trigger.to_state.attributes.session }}
        at {{ trigger.to_state.attributes.circuit }}
```

A scene while an F1 race is live:

```yaml
triggers:
  - trigger: state
    entity_id: binary_sensor.lightsouts_active_session
    to: "on"
conditions:
  - condition: state
    entity_id: binary_sensor.lightsouts_active_session
    attribute: series
    state: F1
  - condition: state
    entity_id: binary_sensor.lightsouts_active_session
    attribute: category
    state: Race
actions:
  - action: scene.turn_on
    target:
      entity_id: scene.race_mode
```

A notification when a session ends:

```yaml
triggers:
  - trigger: state
    entity_id: binary_sensor.lightsouts_active_session
    from: "on"
    to: "off"
actions:
  - action: notify.notify
    data:
      message: The session is over.
```

## Problems and ideas

Tell us on [GitHub](https://github.com/mm98/ha-lightsouts-motorsport-calendar/issues).

## Credits

All event data comes from [lightsouts.com](https://lightsouts.com/), a motorsport calendar made by its author. If this integration is useful to you, consider supporting them through the donation link on their site. This integration is not made by lightsouts.com or connected to it.

## License

MIT, see [LICENSE](LICENSE).
