import { useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api, type LayoutConfig, type RecordOrder } from "../api";
import { useDebounced } from "../hooks";
import { QueryError } from "../components/ErrorBoundary";
import { useToast } from "../components/Toast";
import { layoutToYaml } from "../yaml";
import { ControllersEditor } from "./LayoutControllers";
import { StripsEditor } from "./LayoutStrips";
import { BoxesEditor } from "./LayoutBoxes";
import { LightTests } from "./LayoutTest";

export function LayoutPage() {
  const toast = useToast();
  const qc = useQueryClient();
  const layout = useQuery({ queryKey: ["layout"], queryFn: api.layout });
  const [draft, setDraft] = useState<LayoutConfig | null>(null);
  const [showYaml, setShowYaml] = useState(false);
  const [errors, setErrors] = useState<string[]>([]);
  useEffect(() => { if (layout.data && !draft) setDraft(layout.data); }, [layout.data, draft]);
  const debounced = useDebounced(draft, 400);
  useEffect(() => {
    if (!debounced) return;
    let alive = true;
    api.validateLayout(debounced).then((r) => { if (alive) setErrors(r.ok ? [] : r.errors); }).catch((e) => { if (alive) setErrors([String(e)]); });
    return () => { alive = false; };
  }, [debounced]);
  const save = useMutation({
    mutationFn: (cfg: LayoutConfig) => api.putLayout(cfg),
    onSuccess: (cfg) => { setDraft(cfg); toast.show("Layout saved and applied", "ok"); for (const k of ["layout", "resolved", "order", "status", "releases", "facets"]) void qc.invalidateQueries({ queryKey: [k] }); },
    onError: toast.error,
  });

  if (layout.error) return <QueryError error={layout.error} what="the layout" />;
  if (!draft) return <div className="empty">Loading…</div>;
  const set = (patch: Partial<LayoutConfig>) => setDraft({ ...draft, ...patch });
  const dirty = JSON.stringify(draft) !== JSON.stringify(layout.data);

  return (
    <div className="stack">
      <div className="row between">
        <h1 style={{ margin: 0 }}>Layout</h1>
        <div className="row">
          <button className="btn sm" onClick={() => setShowYaml((s) => !s)}>{showYaml ? "Hide YAML" : "Show YAML"}</button>
          {dirty && <button className="btn ghost sm" onClick={() => setDraft(layout.data ?? null)}>Discard</button>}
          <button className="btn primary sm" onClick={() => save.mutate(draft)} disabled={!dirty || errors.length > 0 || save.isPending}>Save &amp; apply</button>
        </div>
      </div>
      <p className="muted small">Describe the physical shelf: the grid of boxes, the LED controllers, which LEDs run past which boxes, and which boxes hold records. Saved to <code>config/shelf.yaml</code> and applied live.</p>
      {errors.length > 0 && (
        <div className="error-box"><strong>Fix before saving</strong><code>{errors.join("\n")}</code></div>
      )}
      {showYaml && <pre className="yaml">{layoutToYaml(draft)}</pre>}
      <div className="card stack">
        <h2>Shelf</h2>
        <div className="row">
          <label className="field grow">Name<input value={draft.name} onChange={(e) => set({ name: e.target.value })} /></label>
          <label className="field">Rows<input type="number" min={1} max={50} value={draft.rows} onChange={(e) => set({ rows: Math.max(1, Number(e.target.value) || 1) })} style={{ width: "5em" }} /></label>
          <label className="field">Columns<input type="number" min={1} max={50} value={draft.cols} onChange={(e) => set({ cols: Math.max(1, Number(e.target.value) || 1) })} style={{ width: "5em" }} /></label>
          <label className="field">Records per box<input type="number" min={1} value={draft.capacity_default} onChange={(e) => set({ capacity_default: Math.max(1, Number(e.target.value) || 1) })} style={{ width: "6em" }} /></label>
          <label className="field">Records flow
            <select value={draft.record_order} onChange={(e) => set({ record_order: e.target.value as RecordOrder })}>
              <option value="row-major">left→right, then next row</option>
              <option value="column-major">top→bottom, then next column</option>
              <option value="explicit">custom box order</option>
            </select>
          </label>
        </div>
        <span className="small muted">Capacity is only an estimate used until you calibrate a box. Records flow describes how you fill the boxes when sorting.</span>
      </div>
      <ControllersEditor draft={draft} set={set} />
      <StripsEditor draft={draft} set={set} />
      <BoxesEditor draft={draft} set={set} />
      <LightTests draft={draft} />
    </div>
  );
}
