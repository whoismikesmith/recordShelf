# WLED setup

recordShelf talks to WLED over DDP, a small UDP protocol on port 4048 that WLED accepts out
of the box. While frames arrive WLED shows them; a couple of seconds after they stop it
returns to its own preset. That is what lets HomeKit run ambient lighting on the same strips.

## Board settings

In the WLED web UI, **Config → LED Preferences**:

- Set up each output (GPIO pin, LED count, color order). WLED chains the outputs into one
  index space: with four outputs of 100 LEDs, output 1 is 0-99, output 2 is 100-199, and so
  on. That whole range is one `controller` in `config/shelf.yaml` with `led_count: 400`.
- Set a sane **maximum current** / brightness limiter. recordShelf sends full-brightness
  values; WLED's global brightness slider scales them.

**Config → Sync Interfaces**:

- **Receive UDP realtime** enabled, DDP port 4048 (default).
- **Realtime timeout** (default 2500 ms): how long after the last packet WLED keeps showing
  our frame before resuming its own effect. recordShelf also sends `{"live": false}` when an
  effect ends so the hand-back is immediate; the timeout is the safety net.
- **Realtime override** off (`lor` = 0). If it is on, WLED ignores our packets.

**Config → WiFi**: give the board a static IP or a DHCP reservation. `.local` names work from
a Mac but not from inside Docker.

## Mapping LEDs to boxes

Each `strips` entry in the layout describes one physical strip:

```yaml
- id: row1
  controller: wled-a
  start: 100        # first LED index on the controller
  count: 100        # LEDs on this strip
  boxes: [[1,4],[1,3],[1,2],[1,1],[1,0]]   # boxes in the order the LEDs pass them
```

`count` is split evenly across the boxes listed (a 100-LED strip past five boxes gives each
box 20 LEDs; a remainder goes to the first boxes). Listing the boxes right-to-left tells
recordShelf the LEDs run right-to-left, so record positions are mirrored correctly. If a box
comes out backwards anyway, add `reversed: true` for that box under `boxes:`.

Use **Layout → Identify** in the app to check wiring: it lights the first LED of every box in
its own color. **Light pixel** lights one LED by controller and index.

## Two boards, or one

A GLEDOPTO with four outputs covers four rows. For a fifth strip either add a second board
(a second `controller` entry) or run two rows on one output as a single longer strip. Both are
just config; the app does not care where a strip physically ends.

## Fadecandy

The old setup still works: `type: opc`, `host: <pi-address>`, `port: 7890`. OPC has no
"hand back" concept, so recordShelf clears the strip when an effect ends.
