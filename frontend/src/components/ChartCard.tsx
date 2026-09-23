import type { ReactNode } from "react";
import { cn } from "../utils/cn";

export function ChartCard({
  title,
  subtitle,
  action,
  children,
  className,
}: {
  title: string;
  subtitle?: string;
  action?: ReactNode;
  children: ReactNode;
  className?: string;
}) {
  return (
    <div className={cn("rounded-xl border border-line bg-paper-card p-5", className)}>
      <div className="mb-4 flex items-start justify-between gap-3">
        <div>
          <h3 className="font-display text-sm font-bold text-text-1">{title}</h3>
          {subtitle && <p className="mt-0.5 text-xs text-text-3">{subtitle}</p>}
        </div>
        {action}
      </div>
      {children}
    </div>
  );
}
