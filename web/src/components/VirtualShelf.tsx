import { useCallback, useEffect, useRef } from "react";
import type { ResolvedBox, ResolvedLayout } from "../api";
import { socket, useFrame } from "../ws";

interface Props {
  layout: ResolvedLayout;
  onBoxClick?: (box: ResolvedBox) => void;
  selected?: string | null;
  litBox?: string | null;
  compact?: boolean;
  counts?: Record<string, number>;
}

function drawLeds(canvas: HTMLCanvasElement, box: ResolvedBox, frame: Uint8Array) {
  const dpr = window.devicePixelRatio || 1;
  const w = Math.max(1, Math.round(canvas.clientWidth * dpr));
  const h = Math.max(1, Math.round(canvas.clientHeight * dpr));
  if (canvas.width !== w || canvas.height !== h) {
    canvas.width = w;
    canvas.height = h;
  }
  const ctx = canvas.getContext("2d");
  if (!ctx) return;
  ctx.clearRect(0, 0, w, h);
  const n = box.led_count;
  if (n <= 0) return;
  const slot = w / n;
  const r = Math.max(1, Math.min(h / 2, slot / 2) * 0.8);
  for (let k = 0; k < n; k++) {
    const idx = box.global_start + (box.reversed ? n - 1 - k : k);
    const o = idx * 3;
    const cr = frame[o] ?? 0;
    const cg = frame[o + 1] ?? 0;
    const cb = frame[o + 2] ?? 0;
    const lit = cr + cg + cb > 12;
    ctx.beginPath();
    ctx.arc(slot * (k + 0.5), h / 2, r, 0, Math.PI * 2);
    if (lit) {
      ctx.fillStyle = `rgb(${cr},${cg},${cb})`;
      ctx.shadowColor = ctx.fillStyle;
      ctx.shadowBlur = r * 2;
    } else {
      ctx.fillStyle = "rgba(255,255,255,0.10)";
      ctx.shadowBlur = 0;
    }
    ctx.fill();
  }
  ctx.shadowBlur = 0;
}

export function VirtualShelf({ layout, onBoxClick, selected, litBox, compact, counts }: Props) {
  const canvases = useRef(new Map<string, HTMLCanvasElement>());
  const boxes = useRef(new Map<string, ResolvedBox>());
  boxes.current = new Map(layout.boxes.map((b) => [b.id, b]));

  const draw = useCallback((frame: Uint8Array) => {
    for (const [id, canvas] of canvases.current) {
      const box = boxes.current.get(id);
      if (box) drawLeds(canvas, box, frame);
    }
  }, []);
  useFrame(draw);

  useEffect(() => {
    const ro = new ResizeObserver(() => draw(socket.frame));
    for (const c of canvases.current.values()) ro.observe(c);
    return () => ro.disconnect();
  }, [layout, draw]);

  const style = { gridTemplateColumns: `repeat(${layout.cols}, minmax(0, 1fr))` };
  const cls = ["shelf", compact ? "compact" : "", onBoxClick ? "" : "noclick"].join(" ");
  return (
    <div className={cls} style={style} role="grid" aria-label={layout.name}>
      {layout.boxes.map((box) => {
        const classes = ["cell", box.kind, selected === box.id ? "selected" : "", litBox === box.id ? "lit" : ""].join(" ");
        const count = counts?.[box.id];
        return (
          <button
            key={box.id}
            type="button"
            className={classes}
            onClick={onBoxClick ? () => onBoxClick(box) : undefined}
            title={`${box.id}${box.label ? ` · ${box.label}` : ""}`}
          >
            <div>
              <div className="id">{box.id}</div>
              {box.label && <div className="label">{box.label}</div>}
              {count !== undefined && box.kind === "records" && <div className="count">{count} rec</div>}
            </div>
            {box.led_count > 0 ? (
              <canvas
                className="leds"
                ref={(el) => {
                  if (el) canvases.current.set(box.id, el);
                  else canvases.current.delete(box.id);
                }}
              />
            ) : (
              <div className="count">no LEDs</div>
            )}
          </button>
        );
      })}
    </div>
  );
}
