import { createContext, useCallback, useContext, useState, type ReactNode } from "react";
import { CheckCircle2, AlertTriangle, Info, XCircle, X } from "lucide-react";
import { cn } from "../utils/cn";

type ToastKind = "success" | "warning" | "error" | "info";
interface ToastItem { id: number; kind: ToastKind; title: string; message?: string; }

const ToastContext = createContext<{ push: (kind: ToastKind, title: string, message?: string) => void } | null>(null);

const ICONS: Record<ToastKind, typeof CheckCircle2> = {
  success: CheckCircle2,
  warning: AlertTriangle,
  error: XCircle,
  info: Info,
};
const TONES: Record<ToastKind, string> = {
  success: "border-ok-500/30 text-ok-600",
  warning: "border-warn-500/30 text-warn-600",
  error: "border-bad-500/30 text-bad-600",
  info: "border-signal-500/30 text-signal-500",
};

export function ToastProvider({ children }: { children: ReactNode }) {
  const [items, setItems] = useState<ToastItem[]>([]);

  const push = useCallback((kind: ToastKind, title: string, message?: string) => {
    const id = Date.now() + Math.random();
    setItems((prev) => [...prev, { id, kind, title, message }]);
    setTimeout(() => setItems((prev) => prev.filter((t) => t.id !== id)), 4200);
  }, []);

  const dismiss = (id: number) => setItems((prev) => prev.filter((t) => t.id !== id));

  return (
    <ToastContext.Provider value={{ push }}>
      {children}
      <div className="fixed bottom-5 right-5 z-[100] flex flex-col gap-2 w-[340px] max-w-[92vw]">
        {items.map((t) => {
          const Icon = ICONS[t.kind];
          return (
            <div key={t.id} className={cn("animate-fade-up flex items-start gap-3 rounded-lg border bg-white px-4 py-3 shadow-lg", TONES[t.kind])}>
              <Icon size={18} className="mt-0.5 shrink-0" />
              <div className="min-w-0 flex-1">
                <p className="text-sm font-semibold text-text-1">{t.title}</p>
                {t.message && <p className="mt-0.5 text-xs text-text-2">{t.message}</p>}
              </div>
              <button onClick={() => dismiss(t.id)} className="text-text-3 hover:text-text-1">
                <X size={14} />
              </button>
            </div>
          );
        })}
      </div>
    </ToastContext.Provider>
  );
}

export function useToast() {
  const ctx = useContext(ToastContext);
  if (!ctx) throw new Error("useToast must be used within ToastProvider");
  return ctx;
}
