# recordShelf

Find a record on your shelf by lighting the LED next to it.

recordShelf syncs your [Discogs](https://www.discogs.com) collection, knows which box on the
shelf every record lives in, and drives addressable LED strips through [WLED](https://kno.wled.ge)
so a tap on your phone makes the right spot blink. It also paints the whole shelf by decade,
genre, or rating, and exposes plain URLs so HomeKit (via Homebridge) or a Siri Shortcut can
trigger it.

Version 2 is a full rewrite of the 2017 Flask + Fadecandy tool, which now lives in
[`legacy/`](legacy/). It replaces the Raspberry Pi and Fadecandy with any WLED controller,
replaces the "records are evenly spread across the shelf" guess with real per-box placement
and calibration, and adds a web app that works from a phone.

## How it works

```
Discogs ──sync──▶ SQLite ──▶ shelf order + box boundaries ──▶ record → box → LED
                                                                      │
        browser ◀── websocket (live frame) ◀── renderer ──DDP/UDP──▶ WLED boards
```

- **Layout** (`config/shelf.yaml`): the physical shelf. Rows and columns of boxes, which LED
  strip runs past which boxes, which controller each strip is on. A 5x5 Kallax with five
  100-LED strips is the example; anything rectangular works, and you can mark boxes that hold
  something other than records.
- **Shelf order**: the sequence records sit in, flowing box by box. Generated from an ordering
  **scheme** (sections by genre or decade, alphabetical inside, with per-record overrides), then
  adjusted by hand as you move things.
- **Boundaries**: the first record in each box. Tell the app "this record is the first one in
  box r2c3" and it interpolates LED positions inside the box. Until you calibrate, it guesses
  by box capacity.
- **Renderer**: one background task owns the LED frame, runs the active effect, and streams it
  to the boards. Effects never block the web server. When an effect ends the boards go back to
  whatever WLED (and HomeKit) had them doing.

## Quick start

Requirements: Python 3.12+, [uv](https://docs.astral.sh/uv/), Node 20+ for the web app.

```bash
git clone https://github.com/whoismikesmith/recordShelf
cd recordShelf
uv sync                      # backend deps
uv run recordshelf init      # writes config/shelf.yaml and .env from the examples
$EDITOR .env                 # DISCOGS_USERNAME and DISCOGS_TOKEN
(cd web && npm install && npm run build)
uv run recordshelf serve     # http://localhost:8000
```

Then in the app: **Settings → Sync now** to pull the collection, **Layout** to describe your
shelf and controllers, **Organize** to pick an ordering scheme, generate a plan, apply it, and
calibrate boxes, **Browse** to find records.

A Discogs token is optional for public collections but raises the rate limit from 25 to 60
requests a minute, and it is the only way to see your collection folders and notes (Discogs
hides those from unauthenticated requests). Get one at
<https://www.discogs.com/settings/developers>. A 1700-item collection syncs in about a
minute either way.

### Development

```bash
uv run recordshelf serve --reload      # API with auto-reload on :8000
cd web && npm run dev                  # Vite dev server on :5173, proxies /api and /ws
uv run pytest                          # backend tests
uv run ruff check src tests            # lint
```

Set every controller to `type: none` in `config/shelf.yaml` and the virtual shelf in the
browser still shows exactly what the LEDs would do, so you can build and test with no
hardware attached.

## Hardware

Any WLED board works. The example config assumes two GLEDOPTO controllers, one driving four
100-LED strips (rows 0 to 3) and one driving the fifth. See [docs/wled.md](docs/wled.md) for
the WLED settings that matter, wiring notes, and how the LED indices map to boxes.

The original Fadecandy is still supported through the `opc` controller type if you want to
migrate gradually.

## Layout config

`config/shelf.yaml` is validated on load and editable in the app. The important parts:

```yaml
rows: 5
cols: 5
controllers:
  - {id: wled-a, type: wled, host: 192.168.1.50, led_count: 400}
strips:
  # LEDs 0-99 on wled-a run left to right past the five boxes in row 0
  - {id: row0, controller: wled-a, start: 0, count: 100, boxes: [[0,0],[0,1],[0,2],[0,3],[0,4]]}
  # a strip wired right to left just lists its boxes in that order
  - {id: row1, controller: wled-a, start: 100, count: 100, boxes: [[1,4],[1,3],[1,2],[1,1],[1,0]]}
boxes:
  - {at: [0,0], kind: other, label: Turntable}
  - {at: [2,2], capacity: 30}
```

Box ids are `r{row}c{col}`, counted from the top left. `record_order` controls how the shelf
order flows through the boxes (row by row by default).

## Ordering scheme

You said your shelf is half alphabetical and half by genre. The scheme handles that:

- `section_by: genre` groups records into sections. Discogs gives several genres and styles
  per release; the first genre wins unless a `style_map` or `genre_map` entry says otherwise
  (`Grunge: 90s Rock`, `Hip Hop: Hip-Hop & Soul`).
- `section_order` lists sections in shelf order. Unlisted sections follow alphabetically.
- `within` sorts inside a section: `[artist, year, title]` by default.
- `include_descriptions` decides what counts as a shelf record (`LP` and `12"` by default;
  7" singles are skipped rather than mixed in). Per-record overrides can pin a section,
  force a sort key, or exclude a record entirely.

**Generate plan** shows what would go in each box and which records move. **Apply** makes it
the shelf order. Then reshuffle the real shelf to match, and calibrate a few boxes.

## Hooks for Homebridge, Siri, and friends

Everything the app does is also a plain HTTP call, and the most useful ones accept GET:

| URL | Does |
| --- | --- |
| `/api/hooks/locate?q=kind+of+blue` | best text match, blink it |
| `/api/hooks/scene/decade` | paint the shelf by decade until told to stop |
| `/api/hooks/box/r2c3` | light a whole box |
| `/api/hooks/off` | stop, hand the strips back to WLED |
| `/api/hooks/state` | `{"on": true/false}` for switch status polling |

[docs/homebridge.md](docs/homebridge.md) has a homebridge-http-switch config and the Siri
Shortcut recipe. The full API is documented live at `/docs`.

## Running it somewhere permanent

```bash
docker compose up -d
```

builds the web app and runs the server on port 8000 with `./data` and `./config` mounted.
Use IP addresses rather than `.local` names for controllers inside Docker.

## License

MIT. See [LICENSE](LICENSE).
