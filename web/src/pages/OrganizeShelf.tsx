import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api, boxLabel, type OrderBox, type Release } from "../api";
import { QueryError } from "../components/ErrorBoundary";
import { ReleaseRow } from "../components/ReleaseRow";
import { useToast } from "../components/Toast";
import { Icons } from "../icons";

function useOrderMutations() {
  const toast = useToast();
  const qc = useQueryClient();
  const refresh = () => { for (const k of ["order", "releases", "facets", "status", "boundaries"]) void qc.invalidateQueries({ queryKey: [k] }); };
  const opts = { onSuccess: refresh, onError: toast.error };
  return {
    place: useMutation({ mutationFn: api.place, ...opts }),
    remove: useMutation({ mutationFn: ({ id, exclude }: { id: number; exclude: boolean }) => api.remove(id, exclude), ...opts }),
    calibrate: useMutation({ mutationFn: ({ box, id }: { box: string; id: number }) => api.calibrate(box, id), onSuccess: () => { toast.show("Boundary set", "ok"); refresh(); }, onError: toast.error }),
    uncalibrate: useMutation({ mutationFn: api.uncalibrate, ...opts }),
    override: useMutation({ mutationFn: ({ id, section }: { id: number; section: string | null }) => api.putOverride(id, { section }), ...opts }),
    clearOverride: useMutation({ mutationFn: api.deleteOverride, ...opts }),
    locate: useMutation({ mutationFn: (id: number) => api.locate(id), onSuccess: (l) => toast.show(`Lighting ${boxLabel(l.box_id)}`, "lit"), onError: toast.error }),
  };
}
type Muts = ReturnType<typeof useOrderMutations>;

function RecordMenu({ r, m, boxes, calibrateBox }: { r: Release; m: Muts; boxes: OrderBox[]; calibrateBox?: string }) {
  const [open, setOpen] = useState(false);
  const act = (fn: () => void) => () => { setOpen(false); fn(); };
  return (
    <div className="menu">
      <button className="btn ghost sm" onClick={() => setOpen((o) => !o)} aria-label="Actions"><Icons.more /></button>
      {open && (
        <div className="menu-pop" onMouseLeave={() => setOpen(false)}>
          {r.placed && <button onClick={act(() => m.locate.mutate(r.instance_id))}>Light it up</button>}
          {calibrateBox && <button onClick={act(() => m.calibrate.mutate({ box: calibrateBox, id: r.instance_id }))}>This is the first record in {boxLabel(calibrateBox)}</button>}
          {!r.placed && <button onClick={act(() => m.place.mutate({ instance_id: r.instance_id }))}>Place at suggested spot</button>}
          <button onClick={act(() => { const b = window.prompt(`Move to which box? (${boxes.map((x) => x.box_id).join(", ")})`, r.placed?.box_id ?? boxes[0]?.box_id); if (b) m.place.mutate({ instance_id: r.instance_id, box_id: b }); })}>Move to end of a box…</button>
          <button onClick={act(() => { const s = window.prompt("Section override (blank to clear)", r.section); if (s === null) return; if (s.trim()) m.override.mutate({ id: r.instance_id, section: s.trim() }); else m.clearOverride.mutate(r.instance_id); })}>Set section override…</button>
          {r.placed && <button onClick={act(() => m.remove.mutate({ id: r.instance_id, exclude: false }))}>Take off shelf (keep in inbox)</button>}
          {!r.excluded && <button className="danger" onClick={act(() => m.remove.mutate({ id: r.instance_id, exclude: true }))}>Exclude from this shelf</button>}
          {r.excluded && <button onClick={act(() => m.clearOverride.mutate(r.instance_id))}>Un-exclude</button>}
        </div>
      )}
    </div>
  );
}

function InboxRow({ r, m, boxes }: { r: Release; m: Muts; boxes: OrderBox[] }) {
  const toast = useToast();
  const suggest = async () => {
    try {
      const s = await api.suggest(r.instance_id);
      const after = s.after_instance_id ? boxes.flatMap((b) => b.items).find((x) => x.instance_id === s.after_instance_id) : null;
      const where = `${s.box_id ? boxLabel(s.box_id) : "the shelf"}${after ? `, after ${after.artist} – ${after.title}` : ", at the start"}`;
      if (window.confirm(`Place in ${where}?`)) m.place.mutate({ instance_id: r.instance_id, position: s.position });
    } catch (e) { toast.error(e); }
  };
  return (
    <ReleaseRow r={r} compact showBox={false} right={
      <div className="row" style={{ flexWrap: "nowrap" }}>
        <button className="btn sm primary" onClick={suggest}>Place</button>
        <RecordMenu r={r} m={m} boxes={boxes} />
      </div>
    } />
  );
}

function BoxCard({ b, m, boxes }: { b: OrderBox; m: Muts; boxes: OrderBox[] }) {
  const [open, setOpen] = useState(false);
  return (
    <div className={`card tight stack ${b.calibrated ? "accent" : ""}`} style={{ gap: 6 }}>
      <div className="row between" style={{ cursor: "pointer" }} onClick={() => setOpen((o) => !o)}>
        <div className="row">
          <strong>{boxLabel(b.box_id)}</strong>
          {b.label && <span className="badge">{b.label}</span>}
          <span className={`badge mono ${b.count > b.capacity ? "danger" : ""}`}>{b.count}/{b.capacity}</span>
          {b.calibrated ? <span className="badge accent" title="You marked the first record of this box">calibrated</span> : <span className="badge" title="Boundary estimated from capacity">estimated</span>}
          {!b.has_leds && <span className="badge warn">no LEDs</span>}
        </div>
        <span className="muted">{open ? <Icons.up /> : <Icons.down />}</span>
      </div>
      {open && (
        <>
          <div className="row small">
            {b.calibrated && <button className="btn sm" onClick={() => m.uncalibrate.mutate(b.box_id)}>Clear calibration</button>}
            {b.has_leds && <button className="btn sm" onClick={() => api.lightBox(b.box_id, { duration: 6 })}>Light box</button>}
            <span className="muted">Use a record's menu to mark it as first in this box.</span>
          </div>
          <div className="list">
            {b.items.map((r, i) => (
              <ReleaseRow key={r.instance_id} r={r} compact showBox={false} onClick={() => m.locate.mutate(r.instance_id)} right={
                <div className="row" style={{ flexWrap: "nowrap" }}>
                  {i === 0 && <span className="badge accent">first</span>}
                  <RecordMenu r={r} m={m} boxes={boxes} calibrateBox={b.box_id} />
                </div>
              } />
            ))}
            {b.items.length === 0 && <div className="empty small">Empty</div>}
          </div>
        </>
      )}
    </div>
  );
}

export function ShelfContents() {
  const order = useQuery({ queryKey: ["order"], queryFn: api.order });
  const m = useOrderMutations();
  const [show, setShow] = useState<"inbox" | "skipped" | "excluded">("inbox");
  if (order.error) return <QueryError error={order.error} what="the shelf order" />;
  const o = order.data;
  if (!o) return <div className="empty">Loading…</div>;
  const groups = { inbox: o.inbox, skipped: o.skipped, excluded: o.excluded };
  const list = groups[show];
  return (
    <div className="two-col">
      <div className="stack">
        <div className="row between">
          <h2 style={{ margin: 0 }}>Boxes <span className="muted small">{o.total} records</span></h2>
        </div>
        {o.boxes.map((b) => <BoxCard key={b.box_id} b={b} m={m} boxes={o.boxes} />)}
        {o.boxes.length === 0 && <div className="empty">No record boxes in the layout.</div>}
      </div>
      <div className="stack">
        <div className="chips">
          <button type="button" className={`chip ${show === "inbox" ? "on" : ""}`} onClick={() => setShow("inbox")}>Inbox <span className="n">{o.inbox.length}</span></button>
          <button type="button" className={`chip ${show === "skipped" ? "on" : ""}`} onClick={() => setShow("skipped")}>Skipped <span className="n">{o.skipped.length}</span></button>
          <button type="button" className={`chip ${show === "excluded" ? "on" : ""}`} onClick={() => setShow("excluded")}>Excluded <span className="n">{o.excluded.length}</span></button>
        </div>
        <div className="small muted">
          {show === "inbox" && "New arrivals the scheme wants on the shelf but that have no position yet."}
          {show === "skipped" && "In your collection but not wanted by the scheme (format or folder). Use the menu to force one onto the shelf."}
          {show === "excluded" && "Manually excluded. Un-exclude to bring one back."}
        </div>
        <div className="list">
          {list.map((r) => show === "inbox"
            ? <InboxRow key={r.instance_id} r={r} m={m} boxes={o.boxes} />
            : <ReleaseRow key={r.instance_id} r={r} compact showBox={false} right={<RecordMenu r={r} m={m} boxes={o.boxes} />} />)}
        </div>
        {list.length === 0 && <div className="empty small">Nothing here.</div>}
      </div>
    </div>
  );
}
