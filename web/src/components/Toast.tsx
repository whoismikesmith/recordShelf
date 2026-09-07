import { createContext, useCallback, useContext, useMemo, useRef, useState, type ReactNode } from "react";

type Kind = "ok" | "err" | "lit" | "info";
interface Toast { id: number; text: string; kind: Kind }
interface Ctx { show: (text: string, kind?: Kind) => void; error: (e: unknown) => void }

const ToastCtx = createContext<Ctx>({ show: () => {}, error: () => {} });

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);
  const nextId = useRef(1);
  const show = useCallback((text: string, kind: Kind = "info") => {
    const id = nextId.current++;
    setToasts((t) => [...t.slice(-3), { id, text, kind }]);
    window.setTimeout(() => setToasts((t) => t.filter((x) => x.id !== id)), kind === "err" ? 5000 : 2600);
  }, []);
  const error = useCallback((e: unknown) => show(e instanceof Error ? e.message : String(e), "err"), [show]);
  const value = useMemo(() => ({ show, error }), [show, error]);
  return (
    <ToastCtx.Provider value={value}>
      {children}
      <div className="toasts" aria-live="polite">
        {toasts.map((t) => (
          <div key={t.id} className={`toast ${t.kind}`}>{t.text}</div>
        ))}
      </div>
    </ToastCtx.Provider>
  );
}

export const useToast = () => useContext(ToastCtx);
