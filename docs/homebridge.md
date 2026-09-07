# Homebridge and Siri

WLED itself is already HomeKit-friendly through Homebridge plugins such as
`homebridge-wled-simple` (on/off, brightness, presets). Use that for ambient light.

recordShelf adds *actions*: locate a record, paint the shelf, switch it all off. They are plain
GET URLs under `/api/hooks/`, so any HTTP switch plugin works.

## homebridge-http-switch

Install `homebridge-http-switch` and add accessories like these to `config.json`
(replace the host):

```json
{
  "accessory": "HTTP-SWITCH",
  "name": "Shelf by decade",
  "switchType": "stateful",
  "onUrl": "http://recordshelf.local:8000/api/hooks/scene/decade",
  "offUrl": "http://recordshelf.local:8000/api/hooks/off",
  "statusUrl": "http://recordshelf.local:8000/api/hooks/state",
  "statusPattern": "\"on\": ?true"
},
{
  "accessory": "HTTP-SWITCH",
  "name": "Shelf lights off",
  "switchType": "stateless",
  "onUrl": "http://recordshelf.local:8000/api/hooks/off"
}
```

`statusUrl` lets HomeKit show whether anything is running. Add one stateful switch per scene
(`genre`, `rating`, `recent`, `section`, `label`, `style`), and stateless ones for boxes:
`/api/hooks/box/r2c3`.

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
