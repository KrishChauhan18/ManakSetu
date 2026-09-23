import { useEffect, useState } from "react";
import type { LucideIcon } from "lucide-react";
import { ArrowUpRight, ArrowDownRight } from "lucide-react";
import { cn } from "../utils/cn";

export function useCountUp(target: number, durationMs = 900) {
  const [value, setValue] = useState(0);
  useEffect(() => {
    let raf: number;
    const start = performance.now();
    const tick = (now: number) => {
      const t = Math.min(1, (now - start) / durationMs);
      const eased = 1 - Math.pow(1 - t, 3);
      setValue(target * eased);
      if (t < 1) raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [target, durationMs]);
  return value;
}

export function StatCard({
  icon: Icon,
  label,
  value,
  decimals = 0,
  suffix = "",
  trend,
  trendLabel,
  accent = "cyan",
}: {
  icon: LucideIcon;
  label: string;
  value: number;
  decimals?: number;
  suffix?: string;
  trend?: number;
  trendLabel?: string;
  accent?: "cyan" | "violet" | "ok" | "warn" | "bad";
}) {
  const animated = useCountUp(value);
  const accentMap: Record<string, string> = {
    cyan: "from-cyan-500/15 to-cyan-500/0 text-cyan-600",
    violet: "from-violet-500/15 to-violet-500/0 text-violet-500",
    ok: "from-ok-500/15 to-ok-500/0 text-ok-600",
    warn: "from-warn-500/15 to-warn-500/0 text-warn-600",
    bad: "from-bad-500/15 to-bad-500/0 text-bad-600",
  };
  return (
    <div className="group relative overflow-hidden rounded-xl border border-line bg-paper-card p-5 transition-shadow hover:shadow-md">
      <div className={cn("absolute -right-6 -top-6 h-24 w-24 rounded-full bg-gradient-to-br", accentMap[accent])} />
      <div className="relative flex items-center justify-between">
        <div className={cn("flex h-10 w-10 items-center justify-center rounded-lg bg-gradient-to-br", accentMap[accent])}>
          <Icon size={20} />
        </div>
        {trend !== undefined && (
          <span className={cn("flex items-center gap-0.5 text-xs font-semibold", trend >= 0 ? "text-ok-600" : "text-bad-600")}>
            {trend >= 0 ? <ArrowUpRight size={14} /> : <ArrowDownRight size={14} />}
            {Math.abs(trend)}%
          </span>
        )}
      </div>
      <p className="relative mt-4 font-display font-tabular text-3xl font-bold text-text-1">
        {animated.toLocaleString("en-IN", { maximumFractionDigits: decimals, minimumFractionDigits: decimals })}
        {suffix}
      </p>
      <p className="relative mt-1 text-sm text-text-2">{label}</p>
      {trendLabel && <p className="relative mt-2 text-xs text-text-3">{trendLabel}</p>}
    </div>
  );
}
