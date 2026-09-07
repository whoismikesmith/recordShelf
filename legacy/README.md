# Legacy (2017) recordShelf

Kept for reference only. Nothing here runs against the v2 server.

- `app.py`, `config.py`, `opc.py`: the original Python 2 Flask app that fetched a Discogs
  collection into `collection.json` and blinked a Fadecandy over Open Pixel Control.
- `static/`: its Jinja templates and vendored jQuery + DataTables.
- `old_JS_version/`: the even earlier PHP + browser JavaScript version that talked to a
  Fadecandy websocket directly, with "superlatives" (top labels, top artists) and colour
  effects.

If you still have a working Fadecandy, v2 can drive it with a controller of `type: opc`
in `config/shelf.yaml`. See `../docs/wled.md`.
