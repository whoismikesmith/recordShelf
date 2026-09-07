import { useMemo, useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { api, boxLabel, type FacetValue, type ReleaseQuery } from "../api";
import { useDebounced } from "../hooks";
import { Icons } from "../icons";
import { ReleaseRow } from "../components/ReleaseRow";
import { QueryError } from "../components/ErrorBoundary";
import { useToast } from "../components/Toast";
import { useShelfSocket } from "../ws";

type Sort = NonNullable<ReleaseQuery["sort"]>;

function FacetChips({ values, selected, onSelect, label }: {
  values: FacetValue[]; selected: string | null; onSelect: (v: string | null) => void; label: (v: string) => string;
}) {
  if (values.length === 0) return null;
  return (
    <div className="chips scroll">
      {values.map((f) => {
        const v = String(f.value);
        const on = selected === v;
        return (
          <button key={v} type="button" className={`chip ${on ? "on" : ""}`} onClick={() => onSelect(on ? null : v)}>
            {label(v)} <span className="n">{f.count}</span>
          </button>
        );
      })}
    </div>
  );
}

export function BrowsePage() {
  const toast = useToast();
  const ws = useShelfSocket();
  const [q, setQ] = useState("");
  const dq = useDebounced(q);
  const [description, setDescription] = useState<string | null>(null);
  const [genre, setGenre] = useState<string | null>(null);
  const [decade, setDecade] = useState<string | null>(null);
  const [section, setSection] = useState<string | null>(null);
  const [box, setBox] = useState<string | null>(null);
  const [sort, setSort] = useState<Sort>("position");
  const [showFilters, setShowFilters] = useState(false);

  const params = useMemo<ReleaseQuery>(
    () => ({ q: dq, description: description ?? undefined, genre: genre ?? undefined, decade: decade ?? undefined,
      section: section ?? undefined, box: box ?? undefined, sort, limit: 500 }),
    [dq, description, genre, decade, section, box, sort],
  );
  const releases = useQuery({ queryKey: ["releases", params], queryFn: () => api.releases(params), placeholderData: (p) => p });
  const facets = useQuery({ queryKey: ["facets"], queryFn: api.facets });
  const locate = useMutation({
    mutationFn: (id: number) => api.locate(id),
    onSuccess: (loc) => toast.show(loc.has_leds ? `Lighting ${boxLabel(loc.box_id)}` : `${boxLabel(loc.box_id)} (no LEDs on that box)`, "lit"),
    onError: toast.error,
  });
  const litId = ws.effect?.name === "locate" ? ws.effect.instance_id : undefined;
  const activeFilters = [description, genre, decade, section, box].filter(Boolean).length;

  return (
    <div className="stack">
      <div className="search">
        <Icons.search />
        <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Artist, title, label, year, genre…" autoFocus inputMode="search" />
        {q && <button className="btn ghost sm" onClick={() => setQ("")} aria-label="Clear"><Icons.x /></button>}
      </div>
      <div className="row between">
        <div className="row">
          <button className={`btn sm ${activeFilters ? "primary" : ""}`} onClick={() => setShowFilters((s) => !s)}>
            Filters{activeFilters ? ` · ${activeFilters}` : ""}
          </button>
          {activeFilters > 0 && (
            <button className="btn ghost sm" onClick={() => { setDescription(null); setGenre(null); setDecade(null); setSection(null); setBox(null); }}>Clear</button>
          )}
        </div>
        <label className="row small muted">
          Sort
          <select value={sort} onChange={(e) => setSort(e.target.value as Sort)} style={{ minHeight: 34, padding: "0.2rem 0.5rem" }}>
            <option value="position">Shelf order</option>
            <option value="artist">Artist</option>
            <option value="title">Title</option>
            <option value="year">Year</option>
            <option value="added">Recently added</option>
            <option value="rating">Rating</option>
          </select>
        </label>
      </div>
      {showFilters && facets.data && (
        <div className="stack">
          <FacetChips values={facets.data.descriptions} selected={description} onSelect={setDescription} label={(v) => v} />
          <FacetChips values={facets.data.genres} selected={genre} onSelect={setGenre} label={(v) => v} />
          <FacetChips values={facets.data.decades} selected={decade} onSelect={setDecade} label={(v) => v} />
          <FacetChips values={facets.data.sections} selected={section} onSelect={setSection} label={(v) => `§ ${v}`} />
          <FacetChips values={facets.data.boxes} selected={box} onSelect={setBox} label={boxLabel} />
        </div>
      )}
      {releases.error && <QueryError error={releases.error} what="releases" />}
      {releases.data && (
        <>
          <div className="small muted">{releases.data.total} record{releases.data.total === 1 ? "" : "s"}{releases.data.total > 500 ? " (showing 500)" : ""}</div>
          <div className="list">
            {releases.data.items.map((r) => (
              <ReleaseRow key={r.instance_id} r={r} lit={litId === r.instance_id} onClick={() => locate.mutate(r.instance_id)} />
            ))}
          </div>
          {releases.data.total === 0 && (
            <div className="empty">
              {releases.data.total === 0 && !dq && !activeFilters
                ? "No records yet. Go to Settings and run a sync."
                : "Nothing matches."}
            </div>
          )}
        </>
      )}
    </div>
  );
}
