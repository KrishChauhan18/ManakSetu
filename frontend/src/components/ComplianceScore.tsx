import { useEffect, useState } from "react";

export function ComplianceScore({ score, size = 168 }: { score: number; size?: number }) {
  const [animated, setAnimated] = useState(0);
  useEffect(() => {
    let raf: number;
    const start = performance.now();
    const dur = 1000;
    const tick = (now: number) => {
      const t = Math.min(1, (now - start) / dur);
      setAnimated(Math.round(score * (1 - Math.pow(1 - t, 3))));
      if (t < 1) raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [score]);

  const stroke = 12;
  const r = (size - stroke) / 2;
  const c = 2 * Math.PI * r;
  const offset = c - (animated / 100) * c;
  const color = score >= 92 ? "#16a34a" : score >= 75 ? "#d97706" : "#dc2626";
  const label = score >= 92 ? "Compliant" : score >= 75 ? "Review Required" : "Potential Issue";

  return (
    <div className="relative inline-flex items-center justify-center" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="-rotate-90">
        <circle cx={size / 2} cy={size / 2} r={r} stroke="#e4e7ee" strokeWidth={stroke} fill="none" />
        <circle
          cx={size / 2} cy={size / 2} r={r} stroke={color} strokeWidth={stroke} fill="none"
          strokeLinecap="round" strokeDasharray={c} strokeDashoffset={offset}
          style={{ transition: "stroke-dashoffset 0.2s linear" }}
        />
      </svg>
      <div className="absolute flex flex-col items-center">
        <span className="font-display font-tabular text-4xl font-extrabold text-text-1">{animated}%</span>
        <span className="mt-1 text-xs font-semibold" style={{ color }}>{label}</span>
      </div>
    </div>
  );
}
