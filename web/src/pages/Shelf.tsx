import { useMemo, useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { api, boxLabel, type ResolvedBox } from "../api";
import { VirtualShelf } from "../components/VirtualShelf";
import { ReleaseRow } from "../components/ReleaseRow";
import { QueryError } from "../components/ErrorBoundary";
import { useToast } from "../components/Toast";
import { useShelfSocket } from "../ws";
import { Icons } from "../icons";

export function ShelfPage() {
  const toast = useToast();
  const ws = useShelfSocket();
  const resolved = useQuery({ queryKey: ["resolved"], queryFn: api.resolvedLayout });
  const order = useQuery({ queryKey: ["order"], queryFn: api.order });
  const [selected, setSelected] = useState<ResolvedBox | null>(null);
  const layout = resolved.data ?? ws.layout;

  const counts = useMemo(() => {
    const out: Record<string, number> = {};
    for (const b of order.data?.boxes ?? []) out[b.box_id] = b.count;
    return out;
  }, [order.data]);
  const boxItems = useMemo(
    () => order.data?.boxes.find((b) => b.box_id === selected?.id) ?? null,
    [order.data, selected],
  );

  const lightBox = useMutation({ mutationFn: (id: string) => api.lightBox(id, { duration: 8 }), onError: toast.error });
  const locate = useMutation({
    mutationFn: (id: number) => api.locate(id),
    onSuccess: (loc) => toast.show(`Lighting ${boxLabel(loc.box_id)}`, "lit"),
    onError: toast.error,
  });
  const off = useMutation({ mutationFn: api.off, onError: toast.error });
  const wipe = useMutation({ mutationFn: () => api.wipe(), onError: toast.error });
  const identify = useMutation({
    mutationFn: () => api.identify(20),
    onSuccess: () => toast.show("First LED of every box lit for 20 s", "lit"),
    onError: toast.error,
  });
  const litId = ws.effect?.name === "locate" ? ws.effect.instance_id : undefined;
  const litBox = ws.effect?.box_id ?? null;

  if (resolved.error && !layout) return <QueryError error={resolved.error} what="the layout" />;
  if (!layout) return <div className="empty">Loading shelf…</div>;

  return (
    <div className="two-col shelf-first">
      <div className="stack">
        <div className="row between">
          <h1 style={{ margin: 0 }}>{layout.name}</h1>
          <span className="muted small mono">{layout.total_pixels} LEDs</span>
        </div>
        <VirtualShelf layout={layout} onBoxClick={setSelected} selected={selected?.id ?? null} litBox={litBox} counts={counts} />
        <div className="row">
          <button className="btn" onClick={() => off.mutate()}><Icons.off /> Off</button>
          <button className="btn" onClick={() => wipe.mutate()}><Icons.bolt /> Wipe test</button>
          <button className="btn" onClick={() => identify.mutate()} title="Lights the first LED of every box in a distinct color so you can check the wiring and strip direction.">
            Identify
          </button>
        </div>
        <p className="small muted">
          Tap a box to see what is in it. <strong>Identify</strong> lights the first LED of every box in its own color so you can check wiring and direction against the real shelf.
        </p>
      </div>
      <div className="stack">
        {!selected && <div className="card muted">Select a box to see its records.</div>}
        {selected && (
          <div className="card stack">
            <div className="row between">
              <div>
                <div className="row">
                  <strong>{boxLabel(selected.id)}</strong>
                  <span className="badge mono">{selected.id}</span>
                  {selected.label && <span className="badge">{selected.label}</span>}
                  {selected.kind !== "records" && <span className="badge">{selected.kind}</span>}
                </div>
                <div className="small muted mono">
                  {selected.led_count > 0
                    ? `${selected.controller} #${selected.led_start}–${selected.led_start + selected.led_count - 1}${selected.reversed ? " (reversed)" : ""}`
                    : "no LEDs"}
                  {boxItems ? ` · ${boxItems.count}/${boxItems.capacity} records` : ""}
                </div>
              </div>
              <button className="btn sm primary" onClick={() => lightBox.mutate(selected.id)} disabled={selected.led_count === 0}>
                Light this box
              </button>
            </div>
            {boxItems && boxItems.items.length > 0 ? (
              <div className="list">
                {boxItems.items.map((r) => (
                  <ReleaseRow key={r.instance_id} r={r} compact showBox={false} lit={litId === r.instance_id} onClick={() => locate.mutate(r.instance_id)} />
                ))}
              </div>
            ) : (
              <div className="muted small">{selected.kind === "records" ? "No records placed here yet." : "Not a record box."}</div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
