import { useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api, SECTION_BY, SORT_KEYS, type Scheme, type SortKey } from "../api";
import { QueryError } from "../components/ErrorBoundary";
import { useToast } from "../components/Toast";
import { Icons } from "../icons";

function move<T>(arr: T[], i: number, dir: -1 | 1): T[] {
  const j = i + dir;
  if (j < 0 || j >= arr.length) return arr;
  const out = arr.slice();
  [out[i], out[j]] = [out[j], out[i]];
  return out;
}

function OrderedList({ items, onChange, addOptions, placeholder }: {
  items: string[]; onChange: (v: string[]) => void; addOptions: string[]; placeholder: string;
}) {
  const [draft, setDraft] = useState("");
  const listId = `dl-${placeholder.replace(/\W/g, "")}`;
  const add = () => {
    const v = draft.trim();
    if (v && !items.includes(v)) onChange([...items, v]);
    setDraft("");
  };
  return (
    <div className="stack" style={{ gap: 6 }}>
      <div className="orderable">
        {items.map((s, i) => (
          <div key={s} className="item">
            <span>{s}</span>
            <button className="btn ghost sm" onClick={() => onChange(move(items, i, -1))} disabled={i === 0} aria-label="Up"><Icons.up /></button>
            <button className="btn ghost sm" onClick={() => onChange(move(items, i, 1))} disabled={i === items.length - 1} aria-label="Down"><Icons.down /></button>
            <button className="btn ghost sm" onClick={() => onChange(items.filter((x) => x !== s))} aria-label="Remove"><Icons.x /></button>
          </div>
        ))}
      </div>
      <div className="row">
        <input list={listId} value={draft} onChange={(e) => setDraft(e.target.value)} placeholder={placeholder} onKeyDown={(e) => e.key === "Enter" && add()} className="grow" />
        <datalist id={listId}>{addOptions.filter((o) => !items.includes(o)).map((o) => <option key={o} value={o} />)}</datalist>
        <button className="btn sm" onClick={add}><Icons.plus /> Add</button>
      </div>
    </div>
  );
}

function MapEditor({ map, onChange, keyOptions, valueOptions, keyLabel }: {
  map: Record<string, string>; onChange: (m: Record<string, string>) => void; keyOptions: string[]; valueOptions: string[]; keyLabel: string;
}) {
  const [k, setK] = useState("");
  const [v, setV] = useState("");
  const entries = Object.entries(map);
  const add = () => {
    if (!k.trim() || !v.trim()) return;
    onChange({ ...map, [k.trim()]: v.trim() });
    setK(""); setV("");
  };
  const kid = `k-${keyLabel}`;
  const vid = `v-${keyLabel}`;
  return (
    <div className="table-wrap">
      <table className="t">
        <thead><tr><th>{keyLabel}</th><th>Section</th><th /></tr></thead>
        <tbody>
          {entries.map(([key, val]) => (
            <tr key={key}>
              <td>{key}</td>
              <td>{val}</td>
              <td style={{ width: 40 }}><button className="btn ghost sm" onClick={() => { const m = { ...map }; delete m[key]; onChange(m); }} aria-label="Remove"><Icons.x /></button></td>
            </tr>
          ))}
          <tr>
            <td><input list={kid} value={k} onChange={(e) => setK(e.target.value)} placeholder={keyLabel} /><datalist id={kid}>{keyOptions.map((o) => <option key={o} value={o} />)}</datalist></td>
            <td><input list={vid} value={v} onChange={(e) => setV(e.target.value)} placeholder="Section" onKeyDown={(e) => e.key === "Enter" && add()} /><datalist id={vid}>{valueOptions.map((o) => <option key={o} value={o} />)}</datalist></td>
            <td><button className="btn sm" onClick={add}><Icons.plus /></button></td>
          </tr>
        </tbody>
      </table>
    </div>
  );
}

export function SchemeEditor() {
  const toast = useToast();
  const qc = useQueryClient();
  const scheme = useQuery({ queryKey: ["scheme"], queryFn: api.scheme });
  const facets = useQuery({ queryKey: ["facets"], queryFn: api.facets });
  const [draft, setDraft] = useState<Scheme | null>(null);
  useEffect(() => { if (scheme.data && !draft) setDraft(scheme.data); }, [scheme.data, draft]);
  const save = useMutation({
    mutationFn: (s: Scheme) => api.putScheme(s),
    onSuccess: (s) => { setDraft(s); toast.show("Scheme saved", "ok"); void qc.invalidateQueries({ queryKey: ["scheme"] }); void qc.invalidateQueries({ queryKey: ["releases"] }); void qc.invalidateQueries({ queryKey: ["facets"] }); void qc.invalidateQueries({ queryKey: ["order"] }); },
    onError: toast.error,
  });

  if (scheme.error) return <QueryError error={scheme.error} what="the scheme" />;
  if (!draft) return <div className="empty">Loading…</div>;
  const f = facets.data;
  const genres = (f?.genres ?? []).map((x) => String(x.value));
  const styles = (f?.styles ?? []).map((x) => String(x.value));
  const sections = Array.from(new Set([...(f?.sections ?? []).map((x) => String(x.value)), ...draft.section_order, ...Object.values(draft.genre_map), ...Object.values(draft.style_map), ...genres]));
  const set = (patch: Partial<Scheme>) => setDraft({ ...draft, ...patch });
  const dirty = JSON.stringify(draft) !== JSON.stringify(scheme.data);

  return (
    <div className="stack">
      <div className="two-col">
        <div className="card stack">
          <h2>Sections</h2>
          <label className="field">
            Group the shelf by
            <select value={draft.section_by} onChange={(e) => set({ section_by: e.target.value as Scheme["section_by"] })}>
              {SECTION_BY.map((s) => <option key={s} value={s}>{s === "none" ? "nothing (one continuous run)" : s}</option>)}
            </select>
          </label>
          {draft.section_by !== "none" && (
            <>
              <div className="small muted">Section order on the shelf. Anything not listed goes after these, alphabetically.</div>
              <OrderedList items={draft.section_order} onChange={(v) => set({ section_order: v })} addOptions={sections} placeholder="Add a section" />
            </>
          )}
          {(draft.section_by === "genre" || draft.section_by === "style") && (
            <>
              <h3>Style → section</h3>
              <div className="small muted">Most specific rule wins: a style mapping beats a genre mapping beats the record's first genre.</div>
              <MapEditor map={draft.style_map} onChange={(m) => set({ style_map: m })} keyOptions={styles} valueOptions={sections} keyLabel="Style" />
              <h3>Genre → section</h3>
              <MapEditor map={draft.genre_map} onChange={(m) => set({ genre_map: m })} keyOptions={genres} valueOptions={sections} keyLabel="Genre" />
            </>
          )}
        </div>
        <div className="stack">
          <div className="card stack">
            <h2>Order inside a section</h2>
            <OrderedList items={draft.within} onChange={(v) => set({ within: v.filter((k): k is SortKey => (SORT_KEYS as string[]).includes(k)) })} addOptions={SORT_KEYS} placeholder="Add a sort key" />
            <label className="check"><input type="checkbox" checked={draft.various_last} onChange={(e) => set({ various_last: e.target.checked })} /> Put “Various Artists” at the end of each section</label>
          </div>
          <div className="card stack">
            <h2>What belongs on this shelf</h2>
            <div className="small muted">Formats to include. Records with none of these are skipped (they stay in the collection, just not on the shelf).</div>
            <div className="chips">
              {Array.from(new Set([...(f?.descriptions ?? []).map((x) => String(x.value)), ...draft.include_descriptions])).map((d) => {
                const on = draft.include_descriptions.includes(d);
                return <button key={d} type="button" className={`chip ${on ? "on" : ""}`} onClick={() => set({ include_descriptions: on ? draft.include_descriptions.filter((x) => x !== d) : [...draft.include_descriptions, d] })}>{d}</button>;
              })}
            </div>
            {(f?.folders.length ?? 0) > 1 && (
              <>
                <div className="small muted">Discogs folders to include (none selected = all).</div>
                <div className="chips">
                  {(f?.folders ?? []).map((x) => {
                    const id = Number(x.value);
                    const on = draft.include_folders.includes(id);
                    return <button key={id} type="button" className={`chip ${on ? "on" : ""}`} onClick={() => set({ include_folders: on ? draft.include_folders.filter((y) => y !== id) : [...draft.include_folders, id] })}>folder {id} <span className="n">{x.count}</span></button>;
                  })}
                </div>
              </>
            )}
          </div>
        </div>
      </div>
      <div className="row">
        <button className="btn primary" onClick={() => save.mutate(draft)} disabled={!dirty || save.isPending}>Save scheme</button>
        {dirty && <button className="btn ghost" onClick={() => setDraft(scheme.data ?? null)}>Discard</button>}
      </div>
    </div>
  );
}
