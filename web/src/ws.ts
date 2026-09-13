// One websocket for the whole app. Frames go to a ref-style subscription so only the
// virtual shelf redraws; everything else reads the low-frequency state snapshot.

import { useEffect, useSyncExternalStore } from "react";
import type { QueryClient } from "@tanstack/react-query";
import type { ActiveScene, Effect, EnrichStatus, ResolvedLayout, SyncStatus } from "./api";

export interface SocketState {
  connected: boolean;
  layout: ResolvedLayout | null;
  effect: Effect | null;
  scene: ActiveScene | null;
  sync: SyncStatus | null;
  enrich: EnrichStatus | null;
}

type Listener = () => void;
type FrameListener = (frame: Uint8Array) => void;

function decodeHex(hex: string): Uint8Array {
  const out = new Uint8Array(hex.length >> 1);
  for (let i = 0; i < out.length; i++) {
    out[i] = parseInt(hex.substr(i * 2, 2), 16);
  }
  return out;
}

class ShelfSocket {
  frame: Uint8Array = new Uint8Array(0);
  state: SocketState = { connected: false, layout: null, effect: null, scene: null, sync: null, enrich: null };
  private stateListeners = new Set<Listener>();
  private frameListeners = new Set<FrameListener>();
  private retry = 0;
  private timer: number | null = null;
  private queryClient: QueryClient | null = null;
  private started = false;

  start(queryClient: QueryClient): void {
    this.queryClient = queryClient;
    if (this.started) return;
    this.started = true;
    this.connect();
  }

  private connect(): void {
    const proto = location.protocol === "https:" ? "wss" : "ws";
    const ws = new WebSocket(`${proto}://${location.host}/ws`);
    ws.onopen = () => {
      this.retry = 0;
      this.setState({ connected: true });
    };
    ws.onmessage = (ev) => this.handle(ev.data as string);
    ws.onclose = () => {
      this.setState({ connected: false });
      this.scheduleReconnect();
    };
    ws.onerror = () => ws.close();
  }

  private scheduleReconnect(): void {
    if (this.timer !== null) return;
    const delay = Math.min(15000, 500 * 2 ** this.retry);
    this.retry += 1;
    this.timer = window.setTimeout(() => {
      this.timer = null;
      this.connect();
    }, delay);
  }

  private setState(patch: Partial<SocketState>): void {
    this.state = { ...this.state, ...patch };
    this.stateListeners.forEach((fn) => fn());
  }

  private invalidate(keys: string[]): void {
    const qc = this.queryClient;
    if (!qc) return;
    for (const k of keys) void qc.invalidateQueries({ queryKey: [k] });
  }

  private handle(raw: string): void {
    let msg: { type: string } & Record<string, unknown>;
    try {
      msg = JSON.parse(raw);
    } catch {
      return;
    }
    switch (msg.type) {
      case "frame":
        this.frame = decodeHex(msg.hex as string);
        this.frameListeners.forEach((fn) => fn(this.frame));
        break;
      case "hello":
        this.setState({
          layout: msg.layout as ResolvedLayout,
          effect: (msg.effect as Effect | null) ?? null,
          scene: (msg.scene as ActiveScene | null) ?? null,
          sync: (msg.sync as SyncStatus | null) ?? null,
          enrich: (msg.enrich as EnrichStatus | null) ?? null,
        });
        break;
      case "effect":
        this.setState({ effect: (msg.active as Effect | null) ?? null });
        if (!msg.active) {
          this.frame = new Uint8Array(this.frame.length);
          this.frameListeners.forEach((fn) => fn(this.frame));
        }
        this.invalidate(["status"]);
        break;
      case "layout":
        this.setState({ layout: msg.layout as ResolvedLayout });
        this.invalidate(["layout", "resolved", "order", "status", "releases", "facets", "boundaries"]);
        break;
      case "sync": {
        const { type: _t, ...rest } = msg;
        void _t;
        const sync = rest as unknown as SyncStatus;
        this.setState({ sync });
        if (sync.state === "done" || sync.state === "error") {
          this.invalidate(["status", "releases", "facets", "order", "plan", "scenes"]);
        }
        break;
      }
      case "enrich": {
        const { type: _t, ...rest } = msg;
        void _t;
        const enrich = rest as unknown as EnrichStatus;
        this.setState({ enrich });
        if (enrich.state === "done" || enrich.state === "error") {
          this.invalidate(["status", "scenes"]);
        }
        break;
      }
    }
  }

  subscribeState = (fn: Listener): (() => void) => {
    this.stateListeners.add(fn);
    return () => this.stateListeners.delete(fn);
  };

  subscribeFrame = (fn: FrameListener): (() => void) => {
    this.frameListeners.add(fn);
    return () => this.frameListeners.delete(fn);
  };
}

export const socket = new ShelfSocket();

export function useShelfSocket(): SocketState {
  return useSyncExternalStore(socket.subscribeState, () => socket.state);
}

/** Run `draw` on every frame without re-rendering the component. */
export function useFrame(draw: FrameListener): void {
  useEffect(() => {
    draw(socket.frame);
    return socket.subscribeFrame(draw);
  }, [draw]);
}
