# recordShelf web app

Vite + React + TypeScript single-page app for the recordShelf API.

## Develop

Run the API on port 8000 (`uv run recordshelf serve --reload` from the repo root), then:

```
cd web
npm install
npm run dev
```

Vite serves the app on http://localhost:5173 and proxies `/api` and `/ws` to the API.

## Build

```
npm run build
```

Output lands in `web/dist`, which the FastAPI server serves at `/` when present. `npm run typecheck` runs the compiler only.

## Layout

- `src/api.ts` typed client and response types
- `src/ws.ts` websocket store: live LED frames, active effect, sync progress
- `src/components/VirtualShelf.tsx` the on-screen shelf with live LEDs
- `src/pages/*` one file per screen, larger editors split into sub-files
- `src/styles.css` all styling; dark by default, light when the OS asks for it
