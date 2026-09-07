import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { api, type LayoutConfig } from "../api";
import { useToast } from "../components/Toast";
import { Icons } from "../icons";

export function LightTests({ draft }: { draft: LayoutConfig }) {
  const toast = useToast();
  const [box, setBox] = useState("r0c0");
  const [controller, setController] = useState(draft.controllers[0]?.id ?? "");
  const [index, setIndex] = useState(0);
  const lightBox = useMutation({ mutationFn: () => api.lightBox(box, { duration: 6 }), onError: toast.error });
  const lightPixel = useMutation({ mutationFn: () => api.lightPixel(controller || draft.controllers[0]?.id || "", index, 6), onError: toast.error });
  const identify = useMutation({ mutationFn: () => api.identify(20), onSuccess: () => toast.show("First LED of every box lit for 20 s", "lit"), onError: toast.error });
  const wipe = useMutation({ mutationFn: () => api.wipe(), onError: toast.error });
  const off = useMutation({ mutationFn: api.off, onError: toast.error });
  const ids: string[] = [];
  for (let r = 0; r < draft.rows; r++) for (let c = 0; c < draft.cols; c++) ids.push(`r${r}c${c}`);

  return (
    <div className="card stack">
      <h2>Test the lights</h2>
      <span className="small muted">These use the <em>saved</em> layout. Save first if you changed strips or controllers.</span>
      <div className="row">
        <select value={box} onChange={(e) => setBox(e.target.value)}>{ids.map((id) => <option key={id} value={id}>{id}</option>)}</select>
        <button className="btn" onClick={() => lightBox.mutate()}>Light box</button>
      </div>
      <div className="row">
        <select value={controller} onChange={(e) => setController(e.target.value)}>{draft.controllers.map((c) => <option key={c.id} value={c.id}>{c.id}</option>)}</select>
        <input type="number" min={0} value={index} onChange={(e) => setIndex(Math.max(0, Number(e.target.value) || 0))} style={{ width: "6em" }} />
        <button className="btn" onClick={() => lightPixel.mutate()} disabled={!controller}>Light LED #</button>
      </div>
      <div className="row">
        <button className="btn" onClick={() => identify.mutate()} title="First LED of every box in a distinct color">Identify boxes</button>
        <button className="btn" onClick={() => wipe.mutate()}><Icons.bolt /> Wipe all</button>
        <button className="btn" onClick={() => off.mutate()}><Icons.off /> Off</button>
      </div>
    </div>
  );
}
