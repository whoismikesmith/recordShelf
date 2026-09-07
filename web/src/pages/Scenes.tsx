import { useState } from "react";
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

export function Legend({ legend }: { legend: LegendEntry[] }) {
  return (
    <div className="legend">
      {legend.map((l) => (
        <span key={l.label} className="small">
          <span className="sw" style={{ background: rgbCss(l.color) }} />
          {l.label}
          {l.count ? <span className="muted mono"> {l.count}</span> : null}
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
      <p className="muted small">Paint the whole shelf by a record attribute. Scenes use the current shelf order, so calibrate first for accurate colors.</p>
      {active && (
        <div className="card accent stack">
          <div className="row between">
            <strong>Now showing: {active.title}</strong>
            <span className="badge accent">live</span>
          </div>
          <Legend legend={active.legend} />
        </div>
      )}
      <div className="card-grid">
        {(scenes.data?.scenes ?? []).map((s) => {
          const isActive = active?.name === s.name;
          return (
            <button key={s.name} type="button" className={`card stack ${isActive ? "accent" : ""}`} style={{ textAlign: "left", cursor: "pointer", color: "inherit", font: "inherit" }} onClick={() => play.mutate(s.name)} disabled={play.isPending}>
              <div className="row between">
                <strong>{s.title}</strong>
                {isActive && <span className="badge accent">on</span>}
              </div>
              <span className="muted small">{s.description}</span>
            </button>
          );
        })}
      </div>
    </div>
  );
}
