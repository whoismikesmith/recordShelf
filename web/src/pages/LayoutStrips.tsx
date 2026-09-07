import { useState } from "react";
import type { LayoutConfig, StripConfig } from "../api";
import { MiniGrid } from "../components/MiniGrid";
import { Icons } from "../icons";

interface Props { draft: LayoutConfig; set: (p: Partial<LayoutConfig>) => void }

export function StripsEditor({ draft, set }: Props) {
  const [editing, setEditing] = useState<number | null>(null);
  const update = (i: number, patch: Partial<StripConfig>) => set({ strips: draft.strips.map((s, j) => (j === i ? { ...s, ...patch } : s)) });
  const add = () => {
    const ctrl = draft.controllers[0]?.id ?? "";
    const used = draft.strips.filter((s) => s.controller === ctrl).reduce((m, s) => Math.max(m, s.start + s.count), 0);
    set({ strips: [...draft.strips, { id: `strip${draft.strips.length + 1}`, controller: ctrl, start: used, count: draft.cols * 20, boxes: [] }] });
    setEditing(draft.strips.length);
  };
  const remove = (i: number) => { set({ strips: draft.strips.filter((_, j) => j !== i) }); setEditing(null); };
  const covered = new Map<string, number>();
  draft.strips.forEach((s, i) => s.boxes.forEach(([r, c]) => covered.set(`${r},${c}`, i)));

  const toggleBox = (i: number, r: number, c: number) => {
    const s = draft.strips[i];
    const idx = s.boxes.findIndex(([br, bc]) => br === r && bc === c);
    if (idx >= 0) update(i, { boxes: s.boxes.filter((_, j) => j !== idx) });
    else if (covered.get(`${r},${c}`) === undefined) update(i, { boxes: [...s.boxes, [r, c]] });
  };

  return (
    <div className="card stack">
      <div className="row between">
        <h2 style={{ margin: 0 }}>Strips</h2>
        <button className="btn sm" onClick={add} disabled={draft.controllers.length === 0}><Icons.plus /> Add strip</button>
      </div>
      <span className="small muted">One entry per physical run of LEDs. <em>Start</em> is the first LED index on that controller. Click the boxes <strong>in the order the LEDs pass them</strong>: a strip wired right-to-left lists its boxes right-to-left, which is how the app knows the direction.</span>
      <div className="table-wrap">
        <table className="t">
          <thead><tr><th>Id</th><th>Controller</th><th>Start</th><th>Count</th><th>Boxes (in LED order)</th><th /></tr></thead>
          <tbody>
            {draft.strips.map((s, i) => (
              <tr key={i} style={editing === i ? { background: "var(--accent-soft)" } : undefined}>
                <td><input value={s.id} onChange={(e) => update(i, { id: e.target.value })} style={{ width: "6em" }} /></td>
                <td>
                  <select value={s.controller} onChange={(e) => update(i, { controller: e.target.value })}>
                    {draft.controllers.map((c) => <option key={c.id} value={c.id}>{c.id}</option>)}
                  </select>
                </td>
                <td><input type="number" min={0} value={s.start} onChange={(e) => update(i, { start: Math.max(0, Number(e.target.value) || 0) })} className="short" /></td>
                <td><input type="number" min={1} value={s.count} onChange={(e) => update(i, { count: Math.max(1, Number(e.target.value) || 1) })} className="short" /></td>
                <td className="mono small">{s.boxes.length ? s.boxes.map(([r, c]) => `r${r}c${c}`).join(" → ") : <span className="faint">none</span>}</td>
                <td style={{ whiteSpace: "nowrap" }}>
                  <button className="btn sm" onClick={() => setEditing(editing === i ? null : i)}>{editing === i ? "Done" : "Pick boxes"}</button>{" "}
                  <button className="btn ghost sm" onClick={() => remove(i)} aria-label="Remove"><Icons.x /></button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {editing !== null && draft.strips[editing] && (
        <div className="row" style={{ alignItems: "flex-start" }}>
          <MiniGrid rows={draft.rows} cols={draft.cols} onClick={(r, c) => toggleBox(editing, r, c)} cell={(r, c) => {
            const owner = covered.get(`${r},${c}`);
            const order = draft.strips[editing].boxes.findIndex(([br, bc]) => br === r && bc === c);
            if (order >= 0) return { cls: "on", text: String(order + 1) };
            if (owner !== undefined) return { cls: "taken", text: draft.strips[owner].id.slice(0, 4), title: `covered by ${draft.strips[owner].id}` };
            return { text: "" };
          }} />
          <div className="small muted grow">
            Editing <strong className="mono">{draft.strips[editing].id}</strong>. Click cells in LED order; click again to remove. Greyed cells belong to another strip.
            <div className="row" style={{ marginTop: 8 }}>
              <button className="btn sm" onClick={() => update(editing, { boxes: [] })}>Clear</button>
              <button className="btn sm" onClick={() => update(editing, { boxes: draft.strips[editing].boxes.slice().reverse() })}>Reverse</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
