import { useState } from "react";
import { api, type ControllerConfig, type ControllerType, type LayoutConfig, type ProbeResult } from "../api";
import { Icons } from "../icons";

interface Props { draft: LayoutConfig; set: (p: Partial<LayoutConfig>) => void }

export function ControllersEditor({ draft, set }: Props) {
  const [probe, setProbe] = useState<Record<string, ProbeResult | "…">>({});
  const update = (i: number, patch: Partial<ControllerConfig>) => {
    const controllers = draft.controllers.map((c, j) => (j === i ? { ...c, ...patch } : c));
    set({ controllers });
  };
  const rename = (i: number, id: string) => {
    const old = draft.controllers[i].id;
    set({
      controllers: draft.controllers.map((c, j) => (j === i ? { ...c, id } : c)),
      strips: draft.strips.map((s) => (s.controller === old ? { ...s, controller: id } : s)),
    });
  };
  const add = () => {
    let n = draft.controllers.length + 1;
    while (draft.controllers.some((c) => c.id === `wled-${n}`)) n++;
    set({ controllers: [...draft.controllers, { id: `wled-${n}`, type: "wled", host: "", port: null, led_count: 100, ddp_type: 11, brightness: 1 }] });
  };
  const remove = (i: number) => {
    const id = draft.controllers[i].id;
    set({ controllers: draft.controllers.filter((_, j) => j !== i), strips: draft.strips.filter((s) => s.controller !== id) });
  };
  const doProbe = async (id: string) => {
    setProbe((p) => ({ ...p, [id]: "…" }));
    try {
      const r = await api.probe(id);
      setProbe((p) => ({ ...p, [id]: r }));
    } catch (e) {
      setProbe((p) => ({ ...p, [id]: { ok: false, error: String(e) } }));
    }
  };
  const saved = (id: string) => draft.controllers.some((c) => c.id === id);

  return (
    <div className="card stack">
      <div className="row between">
        <h2 style={{ margin: 0 }}>Controllers</h2>
        <button className="btn sm" onClick={add}><Icons.plus /> Add</button>
      </div>
      <span className="small muted">A WLED board (GLEDOPTO etc.) is driven over DDP on UDP 4048. All of a board's outputs form one LED index space, in output order. <em>Probe</em> asks a saved WLED board for its name and LED count.</span>
      <div className="table-wrap">
        <table className="t">
          <thead><tr><th>Id</th><th>Type</th><th>Host / IP</th><th>LEDs</th><th>Brightness</th><th /></tr></thead>
          <tbody>
            {draft.controllers.map((c, i) => {
              const pr = probe[c.id];
              return (
                <tr key={i}>
                  <td><input value={c.id} onChange={(e) => rename(i, e.target.value)} className="short" style={{ width: "7em" }} /></td>
                  <td>
                    <select value={c.type} onChange={(e) => update(i, { type: e.target.value as ControllerType })}>
                      <option value="wled">wled</option><option value="opc">opc (Fadecandy)</option><option value="none">none (virtual)</option>
                    </select>
                  </td>
                  <td>
                    <input value={c.host} onChange={(e) => update(i, { host: e.target.value })} placeholder="192.168.1.50" />
                    {pr && pr !== "…" && (
                      <div className={`small ${pr.ok ? "muted" : ""}`} style={{ color: pr.ok ? undefined : "var(--danger)" }}>
                        {pr.ok ? `${pr.name ?? "ok"} ${pr.version ?? ""} · ${pr.led_count ?? "?"} LEDs${pr.led_count !== undefined && pr.led_count !== c.led_count ? ` (config says ${c.led_count})` : ""}` : pr.error}
                      </div>
                    )}
                  </td>
                  <td><input type="number" min={1} value={c.led_count} onChange={(e) => update(i, { led_count: Math.max(1, Number(e.target.value) || 1) })} className="short" /></td>
                  <td><input type="range" min={0.05} max={1} step={0.05} value={c.brightness} onChange={(e) => update(i, { brightness: Number(e.target.value) })} title={String(c.brightness)} /></td>
                  <td style={{ whiteSpace: "nowrap" }}>
                    <button className="btn sm" onClick={() => doProbe(c.id)} disabled={c.type !== "wled" || !saved(c.id) || pr === "…"}>{pr === "…" ? "…" : "Probe"}</button>{" "}
                    <button className="btn ghost sm" onClick={() => remove(i)} aria-label="Remove"><Icons.x /></button>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
