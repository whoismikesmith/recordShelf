const p = { fill: "none", stroke: "currentColor", strokeWidth: 1.8, strokeLinecap: "round", strokeLinejoin: "round" } as const;

export const Icons = {
  search: () => (
    <svg viewBox="0 0 24 24" {...p}><circle cx="11" cy="11" r="7" /><path d="m20 20-3.5-3.5" /></svg>
  ),
  shelf: () => (
    <svg viewBox="0 0 24 24" {...p}><rect x="3" y="3" width="18" height="18" rx="2" /><path d="M3 9h18M3 15h18M9 3v18M15 3v18" /></svg>
  ),
  organize: () => (
    <svg viewBox="0 0 24 24" {...p}><path d="M4 6h16M4 12h10M4 18h6" /><path d="m17 15 3 3-3 3" /></svg>
  ),
  layout: () => (
    <svg viewBox="0 0 24 24" {...p}><path d="M4 7h16M4 17h16" /><circle cx="9" cy="7" r="2.5" fill="var(--bg)" /><circle cx="15" cy="17" r="2.5" fill="var(--bg)" /></svg>
  ),
  scenes: () => (
    <svg viewBox="0 0 24 24" {...p}><path d="M12 3a9 9 0 1 0 0 18c1.5 0 2-1 2-2s-1-1.5-1-2.5S14 15 15.5 15H17a4 4 0 0 0 4-4c0-4.5-4-8-9-8z" /><circle cx="7.5" cy="11" r="1" /><circle cx="10.5" cy="7" r="1" /><circle cx="15" cy="7.5" r="1" /></svg>
  ),
  settings: () => (
    <svg viewBox="0 0 24 24" {...p}><circle cx="12" cy="12" r="3" /><path d="M19.4 15a1.7 1.7 0 0 0 .3 1.8l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.7 1.7 0 0 0-1.8-.3 1.7 1.7 0 0 0-1 1.5V21a2 2 0 1 1-4 0v-.1a1.7 1.7 0 0 0-1.1-1.5 1.7 1.7 0 0 0-1.8.3l-.1.1a2 2 0 1 1-2.8-2.8l.1-.1a1.7 1.7 0 0 0 .3-1.8 1.7 1.7 0 0 0-1.5-1H3a2 2 0 1 1 0-4h.1a1.7 1.7 0 0 0 1.5-1.1 1.7 1.7 0 0 0-.3-1.8l-.1-.1a2 2 0 1 1 2.8-2.8l.1.1a1.7 1.7 0 0 0 1.8.3H9a1.7 1.7 0 0 0 1-1.5V3a2 2 0 1 1 4 0v.1a1.7 1.7 0 0 0 1 1.5 1.7 1.7 0 0 0 1.8-.3l.1-.1a2 2 0 1 1 2.8 2.8l-.1.1a1.7 1.7 0 0 0-.3 1.8V9a1.7 1.7 0 0 0 1.5 1H21a2 2 0 1 1 0 4h-.1a1.7 1.7 0 0 0-1.5 1z" /></svg>
  ),
  record: () => (
    <svg viewBox="0 0 24 24" {...p}><circle cx="12" cy="12" r="9" /><circle cx="12" cy="12" r="3" /><circle cx="12" cy="12" r="0.6" fill="currentColor" /></svg>
  ),
  off: () => (
    <svg viewBox="0 0 24 24" {...p}><path d="M12 3v9" /><path d="M6.3 6.3a8 8 0 1 0 11.4 0" /></svg>
  ),
  more: () => (
    <svg viewBox="0 0 24 24" {...p}><circle cx="5" cy="12" r="1.2" fill="currentColor" /><circle cx="12" cy="12" r="1.2" fill="currentColor" /><circle cx="19" cy="12" r="1.2" fill="currentColor" /></svg>
  ),
  up: () => <svg viewBox="0 0 24 24" {...p}><path d="m6 15 6-6 6 6" /></svg>,
  down: () => <svg viewBox="0 0 24 24" {...p}><path d="m6 9 6 6 6-6" /></svg>,
  x: () => <svg viewBox="0 0 24 24" {...p}><path d="M6 6l12 12M18 6 6 18" /></svg>,
  plus: () => <svg viewBox="0 0 24 24" {...p}><path d="M12 5v14M5 12h14" /></svg>,
  copy: () => <svg viewBox="0 0 24 24" {...p}><rect x="9" y="9" width="11" height="11" rx="2" /><path d="M5 15V5a2 2 0 0 1 2-2h10" /></svg>,
  check: () => <svg viewBox="0 0 24 24" {...p}><path d="m5 12 5 5 9-10" /></svg>,
  bolt: () => <svg viewBox="0 0 24 24" {...p}><path d="M13 2 4 14h7l-1 8 9-12h-7z" /></svg>,
};
