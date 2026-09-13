# Extending recordShelf

The server is a small set of pieces that only meet in `services.py`. Most additions touch
one file.

## Add a controller type (driver)

`src/recordshelf/drivers/base.py` defines `Driver`. Subclass it, implement `send(pixels)`
(a full frame for that controller, as `(r, g, b)` tuples), and optionally `start`, `stop`,
`release` (called when an effect ends, to hand the strip back) and `probe` (for the Layout
page's test button). Register it in `drivers/__init__.py::make_driver` and add the type name
to `ControllerType` in `models.py`. `WledDriver` (UDP) and `OpcDriver` (TCP) are the
references; both are under 100 lines.

Ideas: sACN/E1.31, a Philips Hue gradient strip, an MQTT topic, a serial Arduino.

## Add an effect

Effects live in `src/recordshelf/render/effects.py`. An effect is any object with
`render(frame, t) -> bool`: paint into `frame` (a list of RGB tuples indexed by global pixel)
for time `t` seconds since start, return `False` when finished. The renderer calls it at the
configured frame rate and never from a request handler. Expose it with a method on
`Services` and a route in `api/lights.py`. `Locate` is the one users see most; keep its
behaviour (blink the target, sweep inside the box) if you replace it.

Useful helpers: `Box.pixels` (a `range`), `Box.pixel_for(index, count)` (which LED the n-th
of m records in a box gets), `Placement.locate(instance_id)`.

## Add a scene

Scenes are functions in `src/recordshelf/render/scenes.py` that receive a `SceneContext`
(releases, placement, scheme, overrides, Discogs `basic` info per instance, fetched `details`
per release id) and return `SceneResult(colors, legend, note)` where `colors` maps global
pixel to RGB. Register in the `SCENES` dict with a title and one-line description and it
appears in the app, with its legend previewed, and at `/api/hooks/scene/<name>`.

`_ranked` builds a scene from any `Release -> list[str]` function: it counts values over every
shelf record (placed or eligible), colors the top N from `PALETTE` (ten hues named and chosen
to stay apart on WS2812B LEDs), folds the rest into `Grey · everything else (N)`, and writes
legend entries like `Red · Thou (19)`. Return `None` instead of a list when the record's
details have not been fetched yet; those stay off with their own legend line.

## Release details

`details.py` fetches `GET /releases/{id}` (credits, companies, country, community have/want,
lowest price) and `GET /marketplace/price_suggestions/{id}` per release into
`data/discogs-details.sqlite`, one raw JSON row per release and kind. `parse_details` turns a
row into `ReleaseDetails`; add fields there when a scene needs more of the release.

## Add a section rule or sort key

`ordering.py`: `section_for` decides which section a record belongs to, `sort_key` orders
records inside a section. Add a literal to `SectionBy` / `SortKey` in `models.py`, handle it
in those two functions, and the Organize page picks it up from the schema.

## Where state lives

| What | Where | Why |
| --- | --- | --- |
| Hardware and shelf geometry | `config/shelf.yaml` | hand-editable, portable, versionable |
| Collection, shelf order, boundaries, overrides, scheme | `data/recordshelf.sqlite` | changes often, from the app |
| Full Discogs release details and prices | `data/discogs-details.sqlite` | a cache; delete it and refetch |
| Secrets and process settings | `.env` / environment | never committed |

## API

Every route is under `/api` and documented at `/docs` (OpenAPI). The websocket at `/ws`
sends `{"type": "hello", ...}` on connect, then `frame` (hex RGB for every pixel), `effect`,
`scene`, `sync`, `enrich`, and `layout` messages. Anything that can render 500 colored dots
can be a front end.
