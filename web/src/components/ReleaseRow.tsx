import type { ReactNode } from "react";
import { boxLabel, type Release } from "../api";
import { Icons } from "../icons";

interface Props {
  r: Release;
  onClick?: () => void;
  lit?: boolean;
  compact?: boolean;
  right?: ReactNode;
  showBox?: boolean;
}

export function ReleaseRow({ r, onClick, lit, compact, right, showBox = true }: Props) {
  const fmt = r.descriptions[0] ?? r.format ?? "";
  const cls = ["rel", lit ? "lit" : "", compact ? "compact" : ""].join(" ");
  const body = (
    <>
      {!compact &&
        (r.thumb ? (
          <img className="thumb" src={r.thumb} alt="" loading="lazy" />
        ) : (
          <div className="thumb empty"><Icons.record /></div>
        ))}
      <div className="grow">
        <div className="title truncate">{r.title}</div>
        <div className="sub truncate">
          {r.artist}
          {fmt ? ` · ${fmt}` : ""}
          {r.section ? ` · ${r.section}` : ""}
        </div>
      </div>
      <div className="meta">
        {right ?? (
          <>
            {r.year ? <span className="year">{r.year}</span> : null}
            {showBox && r.placed ? <span className="badge mono accent">{boxLabel(r.placed.box_id)}</span> : null}
            {showBox && !r.placed && !r.excluded ? <span className="badge">not placed</span> : null}
            {r.excluded ? <span className="badge">excluded</span> : null}
          </>
        )}
      </div>
    </>
  );
  if (onClick) {
    return (
      <button type="button" className={cls} onClick={onClick}>
        {body}
      </button>
    );
  }
  return <div className={cls} style={{ cursor: "default" }}>{body}</div>;
}
