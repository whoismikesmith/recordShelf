import { useMutation, useQuery } from "@tanstack/react-query";
import { api, boxLabel } from "../api";
import { useShelfSocket } from "../ws";
import { Icons } from "../icons";
import { VirtualShelf } from "./VirtualShelf";
import { useToast } from "./Toast";

export function StatusStrip({ hideShelf }: { hideShelf?: boolean }) {
  const ws = useShelfSocket();
  const toast = useToast();
  const status = useQuery({ queryKey: ["status"], queryFn: api.status, refetchInterval: 30000 });
  const off = useMutation({ mutationFn: api.off, onError: toast.error });
  const effect = ws.effect;
  const sync = ws.sync ?? status.data?.sync;
  const errors = (status.data?.controllers ?? []).filter((c) => c.error);

  let text: string;
  if (!effect) text = "Lights idle";
  else if (effect.name === "locate") text = `Locating in ${effect.box_id ? boxLabel(effect.box_id) : "?"}`;
  else if (effect.name === "scene") text = `Scene: ${ws.scene?.title ?? effect.scene ?? ""}`;
  else if (effect.name === "box") text = `Lighting ${effect.box_id ? boxLabel(effect.box_id) : "box"}`;
  else text = `Effect: ${effect.name}`;

  return (
    <div className="status-strip">
      <span className={`dot ${ws.connected ? "on" : ""}`} title={ws.connected ? "Live" : "Reconnecting…"} />
      <span className={effect ? "lit" : "muted"}>{text}</span>
      {effect && !hideShelf && ws.layout && (
        <div className="mini-shelf"><VirtualShelf layout={ws.layout} compact /></div>
      )}
      {effect && (
        <button className="btn sm" onClick={() => off.mutate()} disabled={off.isPending}>
          <Icons.off /> Off
        </button>
      )}
      <span className="grow" />
      {sync?.state === "running" && (
        <span className="badge accent">
          Syncing {sync.pages ? `${sync.page}/${sync.pages}` : "…"}
        </span>
      )}
      {sync?.state === "error" && <span className="badge danger" title={sync.error ?? ""}>Sync failed</span>}
      {errors.map((c) => (
        <span key={c.id} className="badge danger" title={c.error ?? ""}>{c.id}: offline</span>
      ))}
    </div>
  );
}
