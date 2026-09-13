import { useState } from "react";
import { Link } from "react-router-dom";
import { useMutation, useQuery } from "@tanstack/react-query";
import { api, rgbCss, type LegendEntry } from "../api";
import { QueryError } from "../components/ErrorBoundary";
import { useToast } from "../components/Toast";
import { useShelfSocket } from "../ws";
import { Icons } from "../icons";

const DURATIONS: { label: string; value: number | null }[] = [
  { label: "Until stopped", value: null },
  { label: "1 minute", value: 60 },
  { label: "10 minutes", value: 600 },
  { label: "1 hour", value: 3600 },
];

/** `column` lists one entry per line, for legends that name specific artists, labels, people. */
export function Legend({ legend, column = false }: { legend: LegendEntry[]; column?: boolean }) {
  return (
    <div className={`legend ${column ? "col" : ""}`}>
      {legend.map((l) => (
        <span key={l.label} className="small">
          <span className="sw" style={{ background: rgbCss(l.color) }} />
          {l.label}
          {!l.color_name && l.count ? <span className="muted mono"> {l.count}</span> : null}
        </span>
      ))}
    </div>
  );
}

export function ScenesPage() {
  const toast = useToast();
  const ws = useShelfSocket();
  const scenes = useQuery({ queryKey: ["scenes"], queryFn: api.scenes });
  const [duration, setDuration] = useState<number | null>(null);
  const play = useMutation({
    mutationFn: (name: string) => api.playScene(name, duration),
    onSuccess: (r) => toast.show(`Playing ${r.name}`, "lit"),
    onError: toast.error,
  });
  const off = useMutation({ mutationFn: api.off, onError: toast.error });
  const active = ws.effect?.name === "scene" ? ws.scene : null;

  if (scenes.error) return <QueryError error={scenes.error} what="scenes" />;
  return (
    <div className="stack">
      <div className="row between">
        <h1 style={{ margin: 0 }}>Scenes</h1>
        <div className="row">
          <select value={duration ?? ""} onChange={(e) => setDuration(e.target.value === "" ? null : Number(e.target.value))} style={{ minHeight: 36 }}>
            {DURATIONS.map((d) => (
              <option key={d.label} value={d.value ?? ""}>{d.label}</option>
            ))}
          </select>
          <button className="btn" onClick={() => off.mutate()} disabled={!ws.effect}><Icons.off /> Off</button>
        </div>
      </div>
      <p className="muted small">
        Paint the whole shelf by a record attribute. Counts cover every record that belongs on the shelf, so the lists stay put while you file; only placed records light up.
      </p>
      {active && (
        <div className="card accent stack">
          <div className="row between">
            <strong>Now showing: {active.title}</strong>
            <span className="badge accent">live</span>
          </div>
          <Legend legend={active.legend} column={active.legend.some((l) => l.color_name)} />
          {active.note && <span className="small muted">{active.note}</span>}
        </div>
      )}
      <div className="card-grid">
        {(scenes.data?.scenes ?? []).map((s) => {
          const isActive = active?.name === s.name;
          const legend = s.legend ?? []; // absent from servers older than this page
          const unfetched = s.needs_details && legend.some((l) => l.item === "details not fetched yet");
          return (
            <div key={s.name} className={`card stack ${isActive ? "accent" : ""}`}>
              <div className="row between" style={{ flexWrap: "nowrap", alignItems: "flex-start" }}>
                <div className="stack" style={{ gap: 2 }}>
                  <strong>{s.title}</strong>
                  <span className="muted small">{s.description}</span>
                </div>
                {isActive ? (
                  <span className="badge accent">on</span>
                ) : (
                  <button type="button" className="btn sm primary" onClick={() => play.mutate(s.name)} disabled={play.isPending}>
                    Play
                  </button>
                )}
              </div>
              <Legend legend={legend} column={legend.some((l) => l.color_name)} />
              {s.note && <span className="small muted">{s.note}</span>}
              {unfetched && (
                <span className="small muted">
                  Needs release details: <Link to="/settings">fetch them in Settings</Link>.
                </span>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
