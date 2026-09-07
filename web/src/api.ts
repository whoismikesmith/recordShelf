// Typed client for the recordShelf API. Shapes mirror src/recordshelf/api/*.py.

export type RGB = [number, number, number];

export interface Placed {
  position: number;
  box_id: string;
  index_in_box: number;
  count_in_box: number;
  pixel: number | null;
}

export interface Release {
  instance_id: number;
  release_id: number;
  master_id: number | null;
  title: string;
  artist: string;
  artist_sort: string;
  year: number | null;
  label: string | null;
  catno: string | null;
  format: string | null;
  descriptions: string[];
  genres: string[];
  styles: string[];
  rating: number;
  date_added: string | null;
  folder_id: number | null;
  thumb: string | null;
  cover: string | null;
  section: string;
  on_shelf: boolean;
  excluded: boolean;
  placed: Placed | null;
}

export interface ReleaseList {
  items: Release[];
  total: number;
}

export interface FacetValue {
  value: string | number;
  count: number;
}

export interface Facets {
  descriptions: FacetValue[];
  genres: FacetValue[];
  styles: FacetValue[];
  decades: FacetValue[];
  labels: FacetValue[];
  sections: FacetValue[];
  folders: FacetValue[];
  boxes: FacetValue[];
}

export interface OrderBox {
  box_id: string;
  row: number;
  col: number;
  label: string;
  first_position: number;
  count: number;
  capacity: number;
  calibrated: boolean;
  has_leds: boolean;
  items: Release[];
}

export interface OrderView {
  boxes: OrderBox[];
  total: number;
  inbox: Release[];
  skipped: Release[];
  excluded: Release[];
}

export type SectionBy = "none" | "genre" | "style" | "decade" | "label" | "format" | "folder";
export type SortKey = "artist" | "title" | "year" | "added" | "rating" | "label" | "catno";
export const SORT_KEYS: SortKey[] = ["artist", "title", "year", "added", "rating", "label", "catno"];
export const SECTION_BY: SectionBy[] = ["none", "genre", "style", "decade", "label", "format", "folder"];

export interface Scheme {
  section_by: SectionBy;
  section_order: string[];
  style_map: Record<string, string>;
  genre_map: Record<string, string>;
  within: SortKey[];
  include_descriptions: string[];
  include_folders: number[];
  various_last: boolean;
}

export interface PlanItem {
  instance_id: number;
  position: number;
  section: string;
  box_id: string | null;
  current_box_id: string | null;
  moved: boolean;
  artist?: string;
  title?: string;
  year?: number | null;
}

export interface PlanBox {
  box_id: string;
  first_position: number;
  count: number;
  capacity: number;
  sections: string[];
  overflow: boolean;
}

export interface Plan {
  items: PlanItem[];
  boxes: PlanBox[];
  unassigned: number;
  excluded: number;
  moved_count: number;
  total: number;
}

export type ControllerType = "wled" | "opc" | "none";
export type BoxKind = "records" | "other" | "empty";
export type RecordOrder = "row-major" | "column-major" | "explicit";

export interface ControllerConfig {
  id: string;
  type: ControllerType;
  host: string;
  port: number | null;
  led_count: number;
  ddp_type: number;
  brightness: number;
}

export interface StripConfig {
  id: string;
  controller: string;
  start: number;
  count: number;
  boxes: [number, number][];
}

export interface BoxOverride {
  at: [number, number];
  kind: BoxKind;
  label: string;
  capacity: number | null;
  reversed: boolean | null;
}

export interface LayoutConfig {
  version: number;
  name: string;
  rows: number;
  cols: number;
  capacity_default: number;
  record_order: RecordOrder;
  record_box_order: [number, number][];
  controllers: ControllerConfig[];
  strips: StripConfig[];
  boxes: BoxOverride[];
}

export interface ResolvedBox {
  id: string;
  row: number;
  col: number;
  kind: BoxKind;
  label: string;
  capacity: number;
  controller: string | null;
  led_start: number;
  led_count: number;
  reversed: boolean;
  global_start: number;
}

export interface ResolvedLayout {
  name: string;
  rows: number;
  cols: number;
  total_pixels: number;
  controllers: { id: string; type: string; host: string; led_count: number; offset: number }[];
  boxes: ResolvedBox[];
  record_boxes: string[];
}

export interface Effect {
  name: string;
  elapsed: number;
  instance_id?: number;
  box_id?: string;
  pixel?: number | null;
  scene?: string;
}

export interface LegendEntry {
  label: string;
  color: RGB;
  count: number;
}

export interface ActiveScene {
  name: string;
  title: string;
  legend: LegendEntry[];
}

export interface SceneInfo {
  name: string;
  title: string;
  description: string;
}

export interface SyncStatus {
  state: "idle" | "running" | "done" | "error";
  page: number;
  pages: number;
  fetched: number;
  added: number;
  updated: number;
  removed: number;
  error: string | null;
  started_at: string | null;
  finished_at: string | null;
  last_sync: string | null;
}

export interface ControllerInfo {
  id: string;
  type: string;
  host: string;
  led_count: number;
  connected: boolean;
  error: string | null;
  frames_sent: number;
}

export interface Status {
  name: string;
  username: string;
  has_token: boolean;
  last_sync: string | null;
  release_count: number;
  on_shelf: number;
  inbox: number;
  skipped: number;
  excluded: number;
  effect: Effect | null;
  scene: ActiveScene | null;
  controllers: ControllerInfo[];
  sync: SyncStatus;
  websocket_clients: number;
}

export interface Located {
  instance_id: number;
  artist: string | null;
  title: string | null;
  position: number;
  box_id: string;
  row: number;
  col: number;
  index_in_box: number;
  count_in_box: number;
  pixel: number | null;
  has_leds: boolean;
}

export interface Suggestion {
  position: number;
  box_id: string | null;
  after_instance_id: number | null;
}

export interface Boundaries {
  stored: Record<string, number>;
  effective: Record<string, number>;
  calibrated: string[];
}

export interface ProbeResult {
  ok: boolean;
  error?: string;
  type?: string;
  name?: string;
  version?: string;
  led_count?: number;
  configured_led_count?: number;
  ip?: string;
  live?: boolean;
  udp_port?: number;
}

export interface ValidateResult {
  ok: boolean;
  errors: string[];
}

export interface Override {
  instance_id: number;
  section: string | null;
  sort_key: string | null;
  excluded: boolean;
}

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers: Record<string, string> = { Accept: "application/json" };
  if (init.body !== undefined) headers["Content-Type"] = "application/json";
  const resp = await fetch(path, { ...init, headers: { ...headers, ...(init.headers as Record<string, string>) } });
  const text = await resp.text();
  let data: unknown = null;
  try {
    data = text ? JSON.parse(text) : null;
  } catch {
    data = text;
  }
  if (!resp.ok) {
    let detail = resp.statusText;
    if (data && typeof data === "object" && "detail" in data) {
      const d = (data as { detail: unknown }).detail;
      detail = typeof d === "string" ? d : JSON.stringify(d);
    }
    throw new ApiError(resp.status, detail || `HTTP ${resp.status}`);
  }
  return data as T;
}

const get = <T>(path: string) => request<T>(path);
const post = <T>(path: string, body?: unknown) =>
  request<T>(path, { method: "POST", body: body === undefined ? undefined : JSON.stringify(body) });
const put = <T>(path: string, body: unknown) => request<T>(path, { method: "PUT", body: JSON.stringify(body) });
const del = <T>(path: string) => request<T>(path, { method: "DELETE" });

function qs(params: object): string {
  const p = new URLSearchParams();
  for (const [k, v] of Object.entries(params as Record<string, unknown>)) {
    if (v === undefined || v === null || v === "") continue;
    if (typeof v === "string" || typeof v === "number" || typeof v === "boolean") p.set(k, String(v));
  }
  const s = p.toString();
  return s ? `?${s}` : "";
}

export interface ReleaseQuery {
  q?: string;
  description?: string;
  genre?: string;
  style?: string;
  decade?: string;
  section?: string;
  box?: string;
  folder?: number;
  on_shelf?: boolean;
  sort?: "position" | "artist" | "title" | "year" | "added" | "rating";
  limit?: number;
  offset?: number;
}

export const api = {
  status: () => get<Status>("/api/status"),
  sync: () => get<SyncStatus>("/api/sync"),
  startSync: () => post<SyncStatus>("/api/sync"),
  probe: (id: string) => post<ProbeResult>(`/api/controllers/${encodeURIComponent(id)}/probe`),

  releases: (q: ReleaseQuery = {}) => get<ReleaseList>(`/api/releases${qs(q)}`),
  release: (id: number) => get<Release>(`/api/releases/${id}`),
  facets: () => get<Facets>("/api/facets"),

  order: () => get<OrderView>("/api/order"),
  putOrder: (order: number[]) => put<OrderView>("/api/order", { order }),
  putBoxes: (boxes: Record<string, number[]>) => put<OrderView>("/api/order/boxes", { boxes }),
  suggest: (id: number) => get<Suggestion>(`/api/order/suggest/${id}`),
  place: (body: { instance_id: number; position?: number; box_id?: string; after?: number }) =>
    post<OrderView>("/api/order/place", body),
  remove: (instance_id: number, exclude = false) => post<OrderView>("/api/order/remove", { instance_id, exclude }),
  boundaries: () => get<Boundaries>("/api/boundaries"),
  putBoundaries: (boundaries: Record<string, number>) => put<Boundaries>("/api/boundaries", { boundaries }),
  calibrate: (box_id: string, instance_id: number) => post<Boundaries>("/api/calibrate", { box_id, instance_id }),
  uncalibrate: (box_id: string) => del<Boundaries>(`/api/calibrate/${encodeURIComponent(box_id)}`),
  scheme: () => get<Scheme>("/api/scheme"),
  putScheme: (scheme: Scheme) => put<Scheme>("/api/scheme", scheme),
  plan: () => post<Plan>("/api/plan"),
  applyPlan: () => post<{ ok: boolean; total: number }>("/api/plan/apply"),
  overrides: () => get<Record<string, Override>>("/api/overrides"),
  putOverride: (id: number, body: { section?: string | null; sort_key?: string | null; excluded?: boolean }) =>
    put<Override>(`/api/overrides/${id}`, body),
  deleteOverride: (id: number) => del<{ ok: boolean }>(`/api/overrides/${id}`),

  locate: (id: number, duration?: number) => post<Located>(`/api/locate/${id}${qs({ duration })}`),
  locateQuery: (q: string, duration?: number) => post<Located>(`/api/locate${qs({ q, duration })}`),
  lightBox: (box_id: string, body: { color?: RGB; duration?: number | null; pulse?: boolean } = {}) =>
    post<{ ok: boolean }>(`/api/lights/box/${encodeURIComponent(box_id)}`, body),
  lightPixel: (controller: string, index: number, duration = 5) =>
    post<{ ok: boolean; pixel: number }>("/api/lights/pixel", { controller, index, duration }),
  wipe: (body: { color?: RGB; duration?: number } = {}) => post<{ ok: boolean }>("/api/lights/wipe", body),
  identify: (duration = 20) => post<{ ok: boolean; boxes: { box_id: string; color: RGB; pixel: number }[] }>(
    `/api/lights/identify${qs({ duration })}`,
  ),
  off: () => post<{ ok: boolean }>("/api/lights/off"),
  scenes: () => get<{ scenes: SceneInfo[]; active: ActiveScene | null }>("/api/scenes"),
  playScene: (name: string, duration: number | null) =>
    post<{ ok: boolean; name: string; legend: LegendEntry[] }>(`/api/scenes/${encodeURIComponent(name)}`, { duration }),

  layout: () => get<LayoutConfig>("/api/layout"),
  putLayout: (cfg: LayoutConfig) => put<LayoutConfig>("/api/layout", cfg),
  validateLayout: (cfg: LayoutConfig) => post<ValidateResult>("/api/layout/validate", cfg),
  resolvedLayout: () => get<ResolvedLayout>("/api/layout/resolved"),
};

export function boxLabel(id: string): string {
  const m = /^r(\d+)c(\d+)$/.exec(id);
  return m ? `R${Number(m[1]) + 1}·C${Number(m[2]) + 1}` : id;
}

export function rgbCss(c: RGB): string {
  return `rgb(${c[0]}, ${c[1]}, ${c[2]})`;
}

export function errorMessage(e: unknown): string {
  if (e instanceof ApiError) return e.message;
  if (e instanceof Error) return e.message;
  return String(e);
}
