import { useState } from "react";
import { FillBoxes } from "./OrganizeFill";
import { SchemeEditor } from "./OrganizeScheme";
import { PlanView } from "./OrganizePlan";
import { ShelfContents } from "./OrganizeShelf";

type Tab = "shelf" | "fill" | "scheme" | "plan";

export function OrganizePage() {
  const [tab, setTab] = useState<Tab>("shelf");
  return (
    <div className="stack">
      <div className="row between">
        <h1 style={{ margin: 0 }}>Organize</h1>
        <div className="chips">
          {([["shelf", "Shelf"], ["fill", "Fill boxes"], ["scheme", "Scheme"], ["plan", "Plan"]] as [Tab, string][]).map(([t, label]) => (
            <button key={t} type="button" className={`chip ${tab === t ? "on" : ""}`} onClick={() => setTab(t)}>{label}</button>
          ))}
        </div>
      </div>
      {tab === "shelf" && (
        <>
          <p className="muted small">What is in each box right now. Place new arrivals, mark the first record of a box to calibrate its LEDs, or exclude records that are not on this shelf.</p>
          <ShelfContents />
        </>
      )}
      {tab === "fill" && (
        <>
          <p className="muted small">Record what is on the real shelf, one box at a time. Records are added in the order you find them, so work through each box left to right.</p>
          <FillBoxes />
        </>
      )}
      {tab === "scheme" && (
        <>
          <p className="muted small">How the shelf is meant to be sorted. Sections come first (for example by genre), then records sort inside each section.</p>
          <SchemeEditor />
        </>
      )}
      {tab === "plan" && (
        <>
          <p className="muted small">Generate a target order from the scheme and see which records would move. Applying sets the shelf order and estimated box boundaries; you then move the records on the real shelf and calibrate.</p>
          <PlanView />
        </>
      )}
    </div>
  );
}
