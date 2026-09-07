import type { LayoutConfig } from "./api";

function q(s: string): string {
  return /^[A-Za-z0-9 _.\-]*$/.test(s) && s.trim() === s && s !== "" ? s : JSON.stringify(s);
}

/** Render the layout in the same friendly style as config/shelf.yaml. */
export function layoutToYaml(cfg: LayoutConfig): string {
  const lines: string[] = [];
  lines.push(`version: ${cfg.version}`);
  lines.push(`name: ${q(cfg.name)}`);
  lines.push(`rows: ${cfg.rows}`);
  lines.push(`cols: ${cfg.cols}`);
  lines.push(`capacity_default: ${cfg.capacity_default}`);
  lines.push(`record_order: ${cfg.record_order}`);
  if (cfg.record_order === "explicit") {
    lines.push(`record_box_order: [${cfg.record_box_order.map(([r, c]) => `[${r},${c}]`).join(", ")}]`);
  }
  lines.push("", "controllers:");
  for (const c of cfg.controllers) {
    lines.push(`  - id: ${q(c.id)}`);
    lines.push(`    type: ${c.type}`);
    if (c.host) lines.push(`    host: ${q(c.host)}`);
    if (c.port != null) lines.push(`    port: ${c.port}`);
    lines.push(`    led_count: ${c.led_count}`);
    if (c.brightness !== 1) lines.push(`    brightness: ${c.brightness}`);
    if (c.ddp_type !== 0x0b) lines.push(`    ddp_type: ${c.ddp_type}`);
  }
  lines.push("", "strips:");
  for (const s of cfg.strips) {
    const boxes = s.boxes.map(([r, c]) => `[${r},${c}]`).join(",");
    lines.push(`  - {id: ${q(s.id)}, controller: ${q(s.controller)}, start: ${s.start}, count: ${s.count}, boxes: [${boxes}]}`);
  }
  lines.push("", "boxes:");
  if (cfg.boxes.length === 0) lines.push("  []");
  for (const b of cfg.boxes) {
    const parts = [`at: [${b.at[0]},${b.at[1]}]`, `kind: ${b.kind}`];
    if (b.label) parts.push(`label: ${q(b.label)}`);
    if (b.capacity != null) parts.push(`capacity: ${b.capacity}`);
    if (b.reversed != null) parts.push(`reversed: ${b.reversed}`);
    lines.push(`  - {${parts.join(", ")}}`);
  }
  return lines.join("\n") + "\n";
}
