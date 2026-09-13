# Homebridge and Siri

WLED itself is already HomeKit-friendly through Homebridge plugins such as
`homebridge-wled-simple` (on/off, brightness, presets). Use that for ambient light.

recordShelf adds *actions*: locate a record, paint the shelf, switch it all off. They are plain
GET URLs under `/api/hooks/`, so any HTTP switch plugin works.

## homebridge-http-switch

Install `homebridge-http-switch` and add accessories like these to `config.json`. Replace
`recordshelf.local` with the address of the machine running recordShelf; on a NAS use its IP
address (see [synology.md](synology.md)), since Homebridge containers often cannot resolve
`.local` names:

```json
{
  "accessory": "HTTP-SWITCH",
  "name": "Shelf by decade",
  "switchType": "stateful",
  "onUrl": "http://recordshelf.local:8000/api/hooks/scene/decade",
  "offUrl": "http://recordshelf.local:8000/api/hooks/off",
  "statusUrl": "http://recordshelf.local:8000/api/hooks/state",
  "statusPattern": "\"scene\":\\{\"name\":\"decade\"",
  "pullInterval": 10000
},
{
  "accessory": "HTTP-SWITCH",
  "name": "Shelf lights off",
  "switchType": "stateless",
  "onUrl": "http://recordshelf.local:8000/api/hooks/off"
}
```

`statusUrl` lets HomeKit show whether that scene is the one running: the pattern matches only
while `/api/hooks/state` reports that scene by name, so starting another scene flips this switch
off. (A pattern of `"on": ?true` would show every scene switch as on whenever any effect runs.)
Add one stateful switch per scene, and stateless ones for boxes with a duration so the box does
not stay lit forever: `/api/hooks/box/r2c3?duration=10`. Scene names:

- from the synced collection: `artist` (top 10 artists), `label` (top 10 labels), `genre`
  (top 5 genres), `year` (top 10 years), `style` (top 10 styles), `vinyl` (vinyl color),
  `pressing` (special pressings), `decade`, `section`, `rating`, `recent`
- after **Fetch details** / `recordshelf enrich`: `producers`, `mastering`, `musicians`,
  `plants` (pressing plants), `value` (market value), `wanted` (want/have)

The Scenes page shows which color means what for each one.

## Siri Shortcut: "find a record"

1. Shortcuts app → new shortcut → **Ask for Input** (Text), prompt "Which record?".
2. **Get Contents of URL** with `http://recordshelf.local:8000/api/hooks/locate`, method GET,
   query parameter `q` = Provided Input.
3. Optionally **Get Dictionary Value** `box_id` from the result and **Show Result** / speak it:
   "It's in box r2c3".
4. Name the shortcut "Find record". "Hey Siri, find record" then asks which one.

Matching is fuzzy: title, artist, label, year, genre, and style are searched, and the best
scoring record wins.

## Automations

Because scenes stay on until `/api/hooks/off`, a HomeKit automation can paint the shelf by
decade at sunset and turn it off at midnight, or light "recently added" when you get home.
