import { useState } from "react";
import {
  LineChart, Line, BarChart, Bar, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer,
} from "recharts";
import { TrendingUp, ShieldCheck, AlertOctagon, Building2 } from "lucide-react";
import { StatCard } from "../components/StatCard";
import { ChartCard } from "../components/ChartCard";
import { cn } from "../utils/cn";

const RANGES = ["Today", "7 Days", "30 Days", "90 Days", "Custom"];

const TREND = Array.from({ length: 12 }).map((_, i) => ({ label: `W${i + 1}`, rate: Math.round(75 + Math.sin(i / 2) * 5 + i * 0.8) }));

const CATEGORY_VIOLATIONS = [
  { name: "Cooking Oil", value: 38 },
  { name: "Shampoo", value: 29 },
  { name: "Spices", value: 26 },
  { name: "Detergent", value: 21 },
  { name: "Biscuits", value: 18 },
  { name: "Textiles", value: 12 },
];

const MANUFACTURER_RANK = [
  { name: "Shakti Foods Pvt. Ltd.", score: 96 },
  { name: "GreenHarvest Consumer Products", score: 91 },
  { name: "UrbanCare Industries", score: 87 },
  { name: "Nilgiri Agro Exports", score: 82 },
  { name: "Suryodaya Home Essentials", score: 74 },
  { name: "Kaveri Textile Mills", score: 68 },
];

const SEVERITY_DIST = [
  { name: "Critical", value: 14, color: "#dc2626" },
  { name: "High", value: 27, color: "#d97706" },
  { name: "Medium", value: 38, color: "#2563eb" },
  { name: "Low", value: 21, color: "#8891a3" },
];

const HEATMAP_REGIONS = ["Dehradun", "Haridwar", "Nainital", "Roorkee", "Rudrapur", "Rishikesh"];
const HEATMAP = HEATMAP_REGIONS.map((r, i) => ({ region: r, rate: [92, 84, 78, 88, 71, 95][i] }));

const ACTIVITY = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"].map((d, i) => ({ day: d, scans: [38, 52, 47, 61, 58, 24, 12][i] }));

function heatColor(rate: number) {
  if (rate >= 90) return "bg-ok-500";
  if (rate >= 80) return "bg-ok-500/60";
  if (rate >= 72) return "bg-warn-500/70";
  return "bg-bad-500/70";
}

export default function AnalyticsPage() {
  const [range, setRange] = useState("30 Days");

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="font-display text-2xl font-bold text-text-1">Analytics</h1>
          <p className="mt-1 text-sm text-text-2">Enforcement patterns and compliance insights across regions.</p>
        </div>
        <div className="flex gap-1 rounded-lg border border-line bg-paper-card p-1">
          {RANGES.map((r) => (
            <button
              key={r}
              onClick={() => setRange(r)}
              className={cn("rounded-md px-3 py-1.5 text-xs font-semibold transition-colors", range === r ? "bg-ink-900 text-white" : "text-text-2 hover:bg-paper")}
            >
              {r}
            </button>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard icon={TrendingUp} label="Total Inspections" value={3241} trend={6.4} accent="cyan" />
        <StatCard icon={ShieldCheck} label="Compliance Rate" value={86.2} decimals={1} suffix="%" trend={1.8} accent="ok" />
        <StatCard icon={AlertOctagon} label="Potential Violations" value={412} trend={-3.2} accent="bad" />
        <StatCard icon={Building2} label="High-Risk Manufacturers" value={9} trend={-1} accent="warn" />
      </div>

      <div className="grid grid-cols-1 gap-4 xl:grid-cols-2">
        <ChartCard title="Compliance trend" subtitle={`Weekly average · ${range}`}>
          <ResponsiveContainer width="100%" height={220}>
            <LineChart data={TREND} margin={{ left: -20, right: 10, top: 10 }}>
              <CartesianGrid vertical={false} stroke="#e4e7ee" />
              <XAxis dataKey="label" tick={{ fontSize: 11, fill: "#8891a3" }} axisLine={false} tickLine={false} />
              <YAxis domain={[60, 100]} tick={{ fontSize: 11, fill: "#8891a3" }} axisLine={false} tickLine={false} />
              <Tooltip contentStyle={{ borderRadius: 10, border: "1px solid #e4e7ee", fontSize: 12 }} />
              <Line type="monotone" dataKey="rate" stroke="#7c3aed" strokeWidth={2.5} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </ChartCard>

        <ChartCard title="Violations by category" subtitle="Count of flagged findings">
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={CATEGORY_VIOLATIONS} margin={{ left: -20, right: 10, top: 10 }}>
              <CartesianGrid vertical={false} stroke="#e4e7ee" />
              <XAxis dataKey="name" tick={{ fontSize: 10, fill: "#8891a3" }} axisLine={false} tickLine={false} interval={0} angle={-15} textAnchor="end" height={50} />
              <YAxis tick={{ fontSize: 11, fill: "#8891a3" }} axisLine={false} tickLine={false} />
              <Tooltip contentStyle={{ borderRadius: 10, border: "1px solid #e4e7ee", fontSize: 12 }} />
              <Bar dataKey="value" fill="#06b6d4" radius={[6, 6, 0, 0]} barSize={28} />
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>
      </div>

      <div className="grid grid-cols-1 gap-4 xl:grid-cols-3">
        <ChartCard title="Manufacturer compliance ranking" className="xl:col-span-2">
          <div className="space-y-3">
            {MANUFACTURER_RANK.map((m) => (
              <div key={m.name} className="flex items-center gap-3">
                <p className="w-48 shrink-0 truncate text-xs font-medium text-text-2">{m.name}</p>
                <div className="h-2 flex-1 overflow-hidden rounded-full bg-paper">
                  <div className={cn("h-full rounded-full", m.score >= 90 ? "bg-ok-500" : m.score >= 78 ? "bg-warn-500" : "bg-bad-500")} style={{ width: `${m.score}%` }} />
                </div>
                <span className="w-9 text-right font-tabular text-xs font-semibold text-text-1">{m.score}</span>
              </div>
            ))}
          </div>
        </ChartCard>

        <ChartCard title="Violation severity">
          <ResponsiveContainer width="100%" height={190}>
            <PieChart>
              <Pie data={SEVERITY_DIST} dataKey="value" nameKey="name" innerRadius={50} outerRadius={75} paddingAngle={2} strokeWidth={0}>
                {SEVERITY_DIST.map((d) => <Cell key={d.name} fill={d.color} />)}
              </Pie>
              <Tooltip contentStyle={{ borderRadius: 10, border: "1px solid #e4e7ee", fontSize: 12 }} />
            </PieChart>
          </ResponsiveContainer>
          <div className="mt-1 grid grid-cols-2 gap-x-3 gap-y-1.5 text-xs">
            {SEVERITY_DIST.map((d) => (
              <div key={d.name} className="flex items-center gap-1.5 text-text-2">
                <span className="h-2 w-2 rounded-full" style={{ background: d.color }} /> {d.name} · {d.value}%
              </div>
            ))}
          </div>
        </ChartCard>
      </div>

      <div className="grid grid-cols-1 gap-4 xl:grid-cols-2">
        <ChartCard title="Regional compliance heatmap" subtitle="Compliance rate by inspection zone">
          <div className="grid grid-cols-3 gap-2 sm:grid-cols-6">
            {HEATMAP.map((h) => (
              <div key={h.region} className={cn("flex flex-col items-center justify-center rounded-lg py-4 text-white", heatColor(h.rate))}>
                <span className="font-tabular text-lg font-bold">{h.rate}%</span>
                <span className="mt-0.5 text-[10px] font-medium opacity-90">{h.region}</span>
              </div>
            ))}
          </div>
        </ChartCard>

        <ChartCard title="Inspection activity" subtitle="Scans by day of week">
          <ResponsiveContainer width="100%" height={190}>
            <BarChart data={ACTIVITY} margin={{ left: -20, right: 10, top: 10 }}>
              <CartesianGrid vertical={false} stroke="#e4e7ee" />
              <XAxis dataKey="day" tick={{ fontSize: 11, fill: "#8891a3" }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fontSize: 11, fill: "#8891a3" }} axisLine={false} tickLine={false} />
              <Tooltip contentStyle={{ borderRadius: 10, border: "1px solid #e4e7ee", fontSize: 12 }} />
              <Bar dataKey="scans" fill="#2563eb" radius={[6, 6, 0, 0]} barSize={24} />
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>
      </div>
    </div>
  );
}
