import { useEffect, useMemo, useRef, useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { api, boxLabel, type OrderView, type Release } from "../api";
import { QueryError } from "../components/ErrorBoundary";
import { MiniGrid } from "../components/MiniGrid";
import { ReleaseRow } from "../components/ReleaseRow";
import { useToast } from "../components/Toast";
import { useDebounced } from "../hooks";
import { Icons } from "../icons";

const RESULTS = 12;
const PAGE = 50;

type Size = "LP" | '10"' | '7"' | "Other";
const SIZES: Size[] = ["LP", '10"', '7"', "Other"];

function sizeOf(r: Release): Size {
  const d = r.descriptions;
  if (d.includes('7"')) return '7"';
  if (d.includes('10"')) return '10"';
  if (d.includes("LP") || d.includes('12"')) return "LP";
  return "Other";
}

export function FillBoxes() {
  const toast = useToast();
  const qc = useQueryClient();
  const order = useQuery({ queryKey: ["order"], queryFn: api.order });
  const resolved = useQuery({ queryKey: ["resolved"], queryFn: api.resolvedLayout });
  // The whole collection A–Z, fetched once; what is placed comes from the live order instead.
  const collection = useQuery({ queryKey: ["collection-az"], queryFn: () => api.releases({ sort: "artist", limit: 5000 }), staleTime: 5 * 60_000 });
  const [boxId, setBoxId] = useState<string | null>(null);
  const [q, setQ] = useState("");
  const dq = useDebounced(q, 150).trim();
  const [sizes, setSizes] = useState<Size[]>(["LP", '10"']);
  const [fromStart, setFromStart] = useState(false);
  const [limit, setLimit] = useState(PAGE);
  const [pending, setPending] = useState(0);
  const [hidden, setHidden] = useState<Set<number>>(() => new Set());
  const queue = useRef<Promise<unknown>>(Promise.resolve());
  const input = useRef<HTMLInputElement>(null);
  const contents = useRef<HTMLDivElement>(null);
  const params = { q: dq, sort: "relevance" as const, limit: RESULTS };
  const results = useQuery({ queryKey: ["releases", params], queryFn: () => api.releases(params), enabled: dq.length >= 2, placeholderData: (p) => p });

  const boxes = useMemo(() => order.data?.boxes ?? [], [order.data]);
  const box = boxes.find((b) => b.box_id === boxId) ?? null;
  // Resume where you left off: the first record box that is still empty.
  useEffect(() => {
    if (!boxId && boxes.length) setBoxId((boxes.find((b) => b.count === 0) ?? boxes[0]).box_id);
  }, [boxId, boxes]);
  useEffect(() => { setLimit(PAGE); }, [boxId, sizes, fromStart]);
  useEffect(() => { setFromStart(false); }, [boxId]);
  // Keep the newest addition in view inside the contents list without scrolling the page.
  useEffect(() => { const el = contents.current; if (el) el.scrollTop = el.scrollHeight; }, [box?.count]);

  const placed = useMemo(() => new Set(boxes.flatMap((b) => b.items.map((r) => r.instance_id))), [boxes]);
  const all = useMemo(() => collection.data?.items ?? [], [collection.data]);
  const rank = useMemo(() => new Map(all.map((r, i) => [r.instance_id, i])), [all]);
  const unplaced = useMemo(() => all.filter((r) => !r.excluded && !placed.has(r.instance_id) && !hidden.has(r.instance_id)), [all, placed, hidden]);

  const refresh = (view?: OrderView) => {
    if (view) qc.setQueryData(["order"], view);
    for (const k of ["order", "releases", "facets", "status", "boundaries"]) void qc.invalidateQueries({ queryKey: [k] });
  };
  const hide = (id: number, on: boolean) => setHidden((h) => { const n = new Set(h); if (on) n.add(id); else n.delete(id); return n; });
  // Taps run one at a time, in the order they were made, so quick taps down the list file in that order.
  const run = (job: () => Promise<unknown>) => {
    setPending((n) => n + 1);
    queue.current = queue.current.then(job).catch(toast.error).finally(() => setPending((n) => n - 1));
  };
  const addToBox = (r: Release, into: string) => {
    hide(r.instance_id, true);
    run(async () => {
      try {
        const view = await api.place({ instance_id: r.instance_id, box_id: into });
        const b = view.boxes.find((x) => x.box_id === into);
        // Filling a box from its first record is exactly what calibration means. Decide that from the server's
        // answer rather than the tap, so a tap queued behind another never claims to be first.
        if (b?.count === 1 && b.items[0]?.instance_id === r.instance_id) await api.calibrate(into, r.instance_id);
        toast.show(`#${b?.count ?? "?"} in ${boxLabel(into)}: ${r.artist} – ${r.title}`, "ok");
        refresh(view);
      } catch (e) {
        hide(r.instance_id, false);
        throw e;
      }
    });
  };
  const moveTo = (id: number, into: string, index: number) => run(async () => refresh(await api.place({ instance_id: id, box_id: into, index })));
  const takeOff = (r: Release) => run(async () => {
    const view = await api.remove(r.instance_id, false);
    hide(r.instance_id, false);
    toast.show(`Took ${r.title} off the shelf`, "info");
    refresh(view);
  });

  if (order.error) return <QueryError error={order.error} what="the shelf order" />;
  if (resolved.error) return <QueryError error={resolved.error} what="the layout" />;
  if (!order.data || !resolved.data) return <div className="empty">Loading…</div>;
  const layout = resolved.data;
  if (!boxes.length) return <div className="empty">No record boxes in the layout.</div>;

  const pick = (r: Release) => {
    if (!box) return;
    const from = r.placed?.box_id;
    if (from === box.box_id && !window.confirm(`${r.title} is already #${(r.placed?.index_in_box ?? 0) + 1} in this box. Move it to the end?`)) return;
    if (from && from !== box.box_id && !window.confirm(`${r.title} is in ${boxLabel(from)}. Move it to ${boxLabel(box.box_id)}?`)) return;
    addToBox(r, box.box_id);
  };
  const idx = boxes.findIndex((b) => b.box_id === boxId);
  const next = idx >= 0 && idx + 1 < boxes.length ? boxes[idx + 1] : null;
  const hits = dq.length >= 2 ? results.data : undefined;

  // Continue the A–Z list after the last record in this box. An empty box starts from A: the box before it
  // may be a different section (soundtracks, 10"s) and would jump the list somewhere misleading.
  const anchor = box && box.items.length ? box.items[box.items.length - 1] : null;
  const anchorRank = anchor ? rank.get(anchor.instance_id) ?? -1 : -1;
  const sized = unplaced.filter((r) => sizes.includes(sizeOf(r)));
  const earlier = anchor ? sized.filter((r) => (rank.get(r.instance_id) ?? 0) < anchorRank).length : 0;
  const shown = anchor && !fromStart ? sized.filter((r) => (rank.get(r.instance_id) ?? 0) > anchorRank) : sized;
  const sizeCounts = new Map<Size, number>();
  for (const r of unplaced) sizeCounts.set(sizeOf(r), (sizeCounts.get(sizeOf(r)) ?? 0) + 1);

  return (
    <div className="two-col">
      <div className="stack">
        <div className="row" style={{ alignItems: "flex-start" }}>
          <MiniGrid rows={layout.rows} cols={layout.cols} onClick={(r, c) => {
            const id = `r${r}c${c}`;
            if (boxes.some((b) => b.box_id === id)) setBoxId(id);
            else toast.show(`${boxLabel(id)} is not a record box (see Layout → Boxes)`, "info");
          }} cell={(r, c) => {
            const id = `r${r}c${c}`;
            const ob = boxes.find((b) => b.box_id === id);
            if (!ob) {
              const rb = layout.boxes.find((b) => b.id === id);
              return { cls: rb?.kind ?? "", text: rb?.label.slice(0, 4) ?? "", title: rb?.label || rb?.kind };
            }
            return { cls: id === boxId ? "on" : "", text: ob.count ? String(ob.count) : "", title: `${boxLabel(id)} · ${ob.count} records` };
          }} />
          <div className="stack grow" style={{ minWidth: 180, gap: 6 }}>
            <span className="small muted">Pick a box, then tap records in the order they sit, left to right. Each tap adds to the end of the box. Search if one is out of alphabetical order.</span>
          </div>
        </div>
        {box && (
          <>
            <div className="row between">
              <div className="row">
                <strong>{boxLabel(box.box_id)}</strong>
                {box.label && <span className="badge">{box.label}</span>}
                <span className="badge mono">{box.count} record{box.count === 1 ? "" : "s"}</span>
                {pending > 0 && <span className="badge warn">adding {pending}…</span>}
              </div>
              <div className="row">
                {box.has_leds && <button className="btn sm" onClick={() => api.lightBox(box.box_id, { duration: 4 }).catch(toast.error)}><Icons.bolt /> Light</button>}
                {next && <button className="btn sm" onClick={() => setBoxId(next.box_id)}>Next: {boxLabel(next.box_id)} →</button>}
              </div>
            </div>
            <div className="search">
              <Icons.search />
              <input ref={input} value={q} onChange={(e) => setQ(e.target.value)} placeholder="Search any record (or just tap the list below)" inputMode="search" enterKeyHint="done"
                onKeyDown={(e) => { if (e.key === "Enter" && hits?.items.length === 1) pick(hits.items[0]); }} />
              {q && <button className="btn ghost sm" onClick={() => setQ("")} aria-label="Clear"><Icons.x /></button>}
            </div>
            {dq.length >= 2 && results.error && <div className="error-box">Search failed: {String(results.error)}</div>}
            {hits && !results.error && (
              <>
                <div className="list">
                  {hits.items.map((r) => (
                    <ReleaseRow key={r.instance_id} r={r} onClick={() => pick(r)} right={
                      <>
                        {r.year ? <span className="year">{r.year}</span> : null}
                        {r.placed ? <span className={`badge mono ${r.placed.box_id === box.box_id ? "accent" : "warn"}`}>{r.placed.box_id === box.box_id ? `here #${r.placed.index_in_box + 1}` : boxLabel(r.placed.box_id)}</span> : <span className="badge">add</span>}
                      </>
                    } />
                  ))}
                </div>
                {hits.total === 0 && <div className="empty small">Nothing matches “{dq}”. Not in your Discogs collection?</div>}
                {hits.total > RESULTS && <div className="small muted">{hits.total} matches; keep typing to narrow it down.</div>}
              </>
            )}
            {!hits && (
              <>
                <div className="chips">
                  {SIZES.map((s) => {
                    const on = sizes.includes(s);
                    return <button key={s} type="button" className={`chip ${on ? "on" : ""}`} onClick={() => setSizes(on ? sizes.filter((x) => x !== s) : [...sizes, s])}>{s === "LP" ? 'LP / 12"' : s} <span className="n">{sizeCounts.get(s) ?? 0}</span></button>;
                  })}
                </div>
                <div className="row between small">
                  <span className="muted">
                    {shown.length} not in a box yet{anchor && !fromStart ? <>, after <strong>{anchor.artist}</strong> – {anchor.title}</> : ", A–Z"}
                  </span>
                  {anchor && (fromStart
                    ? <button className="btn ghost sm" onClick={() => setFromStart(false)}>Continue after {anchor.artist}</button>
                    : earlier > 0 && <button className="btn ghost sm" onClick={() => setFromStart(true)}>Show {earlier} earlier</button>)}
                </div>
                {collection.error && <QueryError error={collection.error} what="your collection" />}
                {collection.isLoading && <div className="empty small">Loading your collection…</div>}
                <div className="list">
                  {shown.slice(0, limit).map((r) => (
                    <ReleaseRow key={r.instance_id} r={r} onClick={() => addToBox(r, box.box_id)} right={
                      <>
                        {r.year ? <span className="year">{r.year}</span> : null}
                        <span className="badge">{sizeOf(r)}</span>
                      </>
                    } />
                  ))}
                </div>
                {shown.length > limit && <button className="btn" onClick={() => setLimit((l) => l + PAGE)}>Show {Math.min(PAGE, shown.length - limit)} more</button>}
                {collection.data && shown.length === 0 && <div className="empty small">Nothing left to add{earlier ? " after this point" : ""} with these formats.</div>}
              </>
            )}
          </>
        )}
      </div>
      {box && (
        <div className="stack">
          <h2 style={{ margin: 0 }}>In {boxLabel(box.box_id)}, left to right</h2>
          <div ref={contents} className="list" style={{ maxHeight: "60vh", overflowY: "auto" }}>
            {box.items.map((r, i) => (
              <ReleaseRow key={r.instance_id} r={r} compact showBox={false} right={
                <div className="row" style={{ flexWrap: "nowrap", gap: 2 }}>
                  <span className="small muted mono" style={{ minWidth: "2.2em", textAlign: "right" }}>#{i + 1}</span>
                  <button className="btn ghost sm" onClick={() => moveTo(r.instance_id, box.box_id, i - 1)} disabled={i === 0 || pending > 0} aria-label="Move up"><Icons.up /></button>
                  <button className="btn ghost sm" onClick={() => moveTo(r.instance_id, box.box_id, i + 1)} disabled={i === box.items.length - 1 || pending > 0} aria-label="Move down"><Icons.down /></button>
                  <button className="btn ghost sm" onClick={() => takeOff(r)} disabled={pending > 0} aria-label="Take off shelf"><Icons.x /></button>
                </div>
              } />
            ))}
          </div>
          {box.items.length === 0 && <div className="empty small">Empty. The first record you add becomes this box's calibrated start.</div>}
        </div>
      )}
    </div>
  );
}
