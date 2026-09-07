import { useState } from "react";
import type { BoxKind, BoxOverride, LayoutConfig } from "../api";
import { MiniGrid } from "../components/MiniGrid";

interface Props { draft: LayoutConfig; set: (p: Partial<LayoutConfig>) => void }

export function BoxesEditor({ draft, set }: Props) {
  const [sel, setSel] = useState<[number, number] | null>(null);
  const find = (r: number, c: number) => draft.boxes.find((b) => b.at[0] === r && b.at[1] === c);
  const current: BoxOverride = (sel && find(sel[0], sel[1])) || { at: sel ?? [0, 0], kind: "records", label: "", capacity: null, reversed: null };
  const setOverride = (patch: Partial<BoxOverride>) => {
    if (!sel) return;
    const next = { ...current, ...patch, at: sel };
    const isDefault = next.kind === "records" && !next.label && next.capacity == null && next.reversed == null;
    const rest = draft.boxes.filter((b) => !(b.at[0] === sel[0] && b.at[1] === sel[1]));
    set({ boxes: isDefault ? rest : [...rest, next] });
  };
  const inExplicit = (r: number, c: number) => draft.record_box_order.findIndex(([a, b]) => a === r && b === c);
  const toggleExplicit = (r: number, c: number) => {
    const i = inExplicit(r, c);
    set({ record_box_order: i >= 0 ? draft.record_box_order.filter((_, j) => j !== i) : [...draft.record_box_order, [r, c]] });
  };

  return (
    <div className="card stack">
      <h2>Boxes</h2>
      <span className="small muted">Every cell holds records unless you say otherwise. Click a cell to mark it as something else (turntable, books, empty) or to give it its own capacity or a reversed LED direction.</span>
      <div className="row" style={{ alignItems: "flex-start" }}>
        <MiniGrid rows={draft.rows} cols={draft.cols} onClick={(r, c) => setSel([r, c])} cell={(r, c) => {
          const o = find(r, c);
          const cls = [o?.kind ?? "", sel && sel[0] === r && sel[1] === c ? "on" : ""].join(" ");
          return { cls, text: o?.label ? o.label.slice(0, 4) : o?.kind === "empty" ? "" : o?.capacity ? String(o.capacity) : "" };
        }} />
        <div className="stack grow" style={{ minWidth: 220 }}>
          {!sel && <span className="muted small">Select a cell.</span>}
          {sel && (
            <>
              <strong className="mono">r{sel[0]}c{sel[1]}</strong>
              <label className="field">Holds
                <select value={current.kind} onChange={(e) => setOverride({ kind: e.target.value as BoxKind })}>
                  <option value="records">records</option><option value="other">something else</option><option value="empty">nothing</option>
                </select>
              </label>
              <label className="field">Label<input value={current.label} onChange={(e) => setOverride({ label: e.target.value })} placeholder="Turntable, Books…" /></label>
              {current.kind === "records" && (
                <label className="field">Capacity override<input type="number" min={1} value={current.capacity ?? ""} onChange={(e) => setOverride({ capacity: e.target.value === "" ? null : Math.max(1, Number(e.target.value) || 1) })} placeholder={String(draft.capacity_default)} /></label>
              )}
              <label className="field">LED direction
                <select value={current.reversed == null ? "auto" : current.reversed ? "reversed" : "normal"} onChange={(e) => setOverride({ reversed: e.target.value === "auto" ? null : e.target.value === "reversed" })}>
                  <option value="auto">auto (from strip order)</option><option value="normal">left → right</option><option value="reversed">right → left</option>
                </select>
              </label>
            </>
          )}
        </div>
      </div>
      {draft.record_order === "explicit" && (
        <div className="row" style={{ alignItems: "flex-start" }}>
          <MiniGrid rows={draft.rows} cols={draft.cols} onClick={toggleExplicit} cell={(r, c) => {
            const i = inExplicit(r, c);
            const o = find(r, c);
            return { cls: i >= 0 ? "on" : o && o.kind !== "records" ? o.kind : "", text: i >= 0 ? String(i + 1) : "" };
          }} />
          <span className="small muted grow">Custom record flow: click the record boxes in the order you fill them.</span>
        </div>
      )}
    </div>
  );
}
