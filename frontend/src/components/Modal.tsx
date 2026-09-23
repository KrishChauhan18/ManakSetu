import type { ReactNode } from "react";
import { X } from "lucide-react";
import { cn } from "../utils/cn";

export function Modal({
  open,
  onClose,
  title,
  subtitle,
  children,
  footer,
  width = "max-w-lg",
}: {
  open: boolean;
  onClose: () => void;
  title: string;
  subtitle?: string;
  children: ReactNode;
  footer?: ReactNode;
  width?: string;
}) {
  if (!open) return null;
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-ink-950/50 backdrop-blur-sm" onClick={onClose} />
      <div className={cn("relative w-full animate-fade-up rounded-xl border border-line bg-white shadow-2xl", width)}>
        <div className="flex items-start justify-between border-b border-line px-6 py-4">
          <div>
            <h3 className="font-display text-base font-bold text-text-1">{title}</h3>
            {subtitle && <p className="mt-0.5 text-xs text-text-2">{subtitle}</p>}
          </div>
          <button onClick={onClose} className="rounded-md p-1 text-text-3 hover:bg-paper hover:text-text-1 focus-ring">
            <X size={18} />
          </button>
        </div>
        <div className="max-h-[70vh] overflow-y-auto px-6 py-5">{children}</div>
        {footer && <div className="flex items-center justify-end gap-2 border-t border-line px-6 py-4">{footer}</div>}
      </div>
    </div>
  );
}
