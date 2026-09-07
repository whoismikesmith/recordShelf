import { useMemo } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api, boxLabel } from "../api";
import { useToast } from "../components/Toast";

export function PlanView() {
  const toast = useToast();
  const qc = useQueryClient();
  const plan = useQuery({ queryKey: ["plan"], queryFn: api.plan, enabled: false });
  const apply = useMutation({
    mutationFn: api.applyPlan,
    onSuccess: (r) => {
      toast.show(`Shelf order set for ${r.total} records`, "ok");
      for (const k of ["order", "releases", "facets", "status", "boundaries"]) void qc.invalidateQueries({ queryKey: [k] });
      void plan.refetch();
    },
    onError: toast.error,
  });
  const moves = useMemo(() => (plan.data?.items ?? []).filter((i) => i.moved), [plan.data]);
  const p = plan.data;

  return (
    <div className="stack">
      <div className="row">
        <button className="btn primary" onClick={() => plan.refetch()} disabled={plan.isFetching}>{plan.isFetching ? "Working…" : p ? "Regenerate plan" : "Generate plan"}</button>
        {p && (
          <button className="btn" onClick={() => { if (window.confirm(`Apply this order to ${p.total} records? Existing calibration is replaced by the plan's estimates.`)) apply.mutate(); }} disabled={apply.isPending}>
            Apply plan
          </button>
        )}
      </div>
      {plan.error && <div className="error-box">{String(plan.error)}</div>}
      {p && (
        <>
          <div className="row">
            <span className="badge">{p.total} on shelf</span>
            <span className={`badge ${p.moved_count ? "warn" : "ok"}`}>{p.moved_count} change box</span>
            {p.excluded > 0 && <span className="badge">{p.excluded} skipped by scheme</span>}
            {p.unassigned > 0 && <span className="badge danger">{p.unassigned} do not fit</span>}
          </div>
          <div className="card-grid">
            {p.boxes.map((b) => (
              <div key={b.box_id} className={`card tight stack ${b.overflow ? "accent" : ""}`} style={{ gap: 4 }}>
                <div className="row between">
                  <strong>{boxLabel(b.box_id)}</strong>
                  <span className={`badge mono ${b.overflow ? "danger" : ""}`}>{b.count}/{b.capacity}</span>
                </div>
                <div className="small muted">{b.sections.length ? b.sections.join(" · ") : b.count ? "—" : "empty"}</div>
                <div className="small faint mono">from #{b.first_position + 1}</div>
              </div>
            ))}
          </div>
          {moves.length > 0 && (
            <div className="card stack">
              <h2>Records that change box</h2>
              <div className="list moves">
                {moves.map((m) => (
                  <div key={m.instance_id} className="rel compact" style={{ cursor: "default" }}>
                    <div className="grow">
                      <div className="title truncate">{m.title}</div>
                      <div className="sub truncate">{m.artist}{m.section ? ` · ${m.section}` : ""}</div>
                    </div>
                    <div className="meta">
                      <span className="small mono muted">{m.current_box_id ? boxLabel(m.current_box_id) : "?"} → <span className="lit" style={{ color: "var(--accent)" }}>{m.box_id ? boxLabel(m.box_id) : "—"}</span></span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
          {moves.length === 0 && p.total > 0 && <div className="muted small">Nothing changes box. Apply anyway to reorder within boxes.</div>}
        </>
      )}
      {!p && !plan.isFetching && <div className="empty">Generate a plan to preview the target order.</div>}
    </div>
  );
}
