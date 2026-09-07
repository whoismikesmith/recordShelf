import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "../api";
import { QueryError } from "../components/ErrorBoundary";
import { useToast } from "../components/Toast";
import { useShelfSocket } from "../ws";
import { copyText } from "../hooks";
import { Icons } from "../icons";

function fmtDate(s: string | null): string {
  if (!s) return "never";
  const d = new Date(s);
  return isNaN(d.getTime()) ? s : d.toLocaleString();
}

function UrlRow({ path, note }: { path: string; note: string }) {
  const toast = useToast();
  const url = `${window.location.origin}${path}`;
  return (
    <div className="stack" style={{ gap: 2 }}>
      <div className="url">
        <code>{url}</code>
        <button className="btn sm" onClick={async () => toast.show((await copyText(url)) ? "Copied" : "Copy failed", "ok")} aria-label="Copy"><Icons.copy /></button>
      </div>
      <span className="small muted">{note}</span>
    </div>
  );
}

export function SettingsPage() {
  const toast = useToast();
  const qc = useQueryClient();
  const ws = useShelfSocket();
  const status = useQuery({ queryKey: ["status"], queryFn: api.status, refetchInterval: 15000 });
  const sync = useMutation({
    mutationFn: api.startSync,
    onSuccess: () => { toast.show("Sync started", "ok"); void qc.invalidateQueries({ queryKey: ["status"] }); },
    onError: toast.error,
  });
  const s = status.data;
  const live = ws.sync ?? s?.sync;
  const running = live?.state === "running";
  const pct = live && live.pages ? Math.round((live.page / live.pages) * 100) : 0;

  if (status.error) return <QueryError error={status.error} what="status" />;
  return (
    <div className="stack">
      <h1>Settings</h1>
      <div className="two-col">
        <div className="card stack">
          <h2>Discogs</h2>
          {s && (
            <dl className="kv">
              <dt>Username</dt><dd>{s.username || <span className="badge danger">not set (DISCOGS_USERNAME)</span>}</dd>
              <dt>Token</dt><dd>{s.has_token ? <span className="badge ok">present</span> : <span className="badge warn">none · slower rate limit</span>}</dd>
              <dt>Last sync</dt><dd>{fmtDate(s.last_sync)}</dd>
              <dt>Records</dt><dd className="mono">{s.release_count} total · {s.on_shelf} on shelf · {s.inbox} inbox · {s.skipped} skipped · {s.excluded} excluded</dd>
            </dl>
          )}
          <div className="row">
            <button className="btn primary" onClick={() => sync.mutate()} disabled={running || sync.isPending || !s?.username}>
              {running ? "Syncing…" : "Sync now"}
            </button>
            {live?.state === "done" && <span className="small muted">Last run: +{live.added} / ~{live.updated} / −{live.removed}</span>}
            {live?.state === "error" && <span className="badge danger" title={live.error ?? ""}>{live.error}</span>}
          </div>
          {running && (
            <div className="stack" style={{ gap: 4 }}>
              <div className="progress"><div style={{ width: `${pct}%` }} /></div>
              <span className="small muted">Page {live?.page}/{live?.pages} · {live?.fetched} records</span>
            </div>
          )}
          <p className="small muted" style={{ margin: 0 }}>Username and token live in <code>.env</code> on the server. A personal token from discogs.com/settings/developers raises the rate limit from 25 to 60 requests per minute.</p>
        </div>
        <div className="card stack">
          <h2>Controllers</h2>
          {s?.controllers.length === 0 && <span className="muted">No controllers in the layout.</span>}
          {s?.controllers.map((c) => (
            <div key={c.id} className="row between">
              <div>
                <strong className="mono">{c.id}</strong> <span className="badge">{c.type}</span>
                <div className="small muted mono">{c.host || "—"} · {c.led_count} LEDs · {c.frames_sent} frames</div>
              </div>
              {c.error ? <span className="badge danger" title={c.error}>error</span> : c.connected ? <span className="badge ok">ok</span> : <span className="badge">idle</span>}
            </div>
          ))}
          <div className="small muted">
            Live view: <span className={`badge ${ws.connected ? "ok" : "danger"}`}>{ws.connected ? "connected" : "reconnecting"}</span> · {s?.websocket_clients ?? 0} client{s?.websocket_clients === 1 ? "" : "s"}
          </div>
        </div>
      </div>
      <div className="card stack">
        <h2>Homebridge &amp; Shortcuts</h2>
        <p className="small muted">
          Every light action has a plain GET URL, so anything that can fetch a URL can drive the shelf. In Homebridge, install <code>homebridge-http-switch</code> and
          make a switch whose <em>on</em> URL is a scene hook, whose <em>off</em> URL is the off hook, and whose status URL is the state hook (it returns <code>{`{"on": true}`}</code>).
          On iPhone, an Apple Shortcut with a single <em>Get Contents of URL</em> action pointing at the locate hook gives you &ldquo;Hey Siri, find a record&rdquo; with the title spoken into the Shortcut&rsquo;s text input.
        </p>
        <UrlRow path="/api/hooks/locate?q=kind%20of%20blue" note="Best text match, then lights it. Replace the q value." />
        <UrlRow path="/api/hooks/scene/decade" note="Play a scene: decade, genre, style, section, label, rating, recent. Add ?duration=600 for ten minutes." />
        <UrlRow path="/api/hooks/box/r0c0" note="Light one box. Box ids are r{row}c{col}, zero-based from the top left." />
        <UrlRow path="/api/hooks/off" note="Lights off, WLED resumes its own state." />
        <UrlRow path="/api/hooks/state" note="Status for HomeKit switches: returns on/off and the active effect." />
      </div>
    </div>
  );
}
