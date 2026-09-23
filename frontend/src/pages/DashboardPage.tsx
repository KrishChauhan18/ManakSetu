import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import {
  AlertTriangle,
  ArrowRight,
  CheckCircle2,
  Clock3,
  FileSearch,
  Scale,
  ScanLine,
  ShieldCheck,
} from "lucide-react";
import { useAuth } from "../hooks/useAuth";
import { apiListScans, type ScanRecord } from "../services/api";

type Inspection = {
  id: number;
  scan_id: string;
  inspector_id: number | null;
  product?: string | null;
  category?: string | null;
  manufacturer?: string | null;
  result?: string | null;
  score?: number | null;
  region?: string | null;
  location?: string | null;
  image_url: string;
  image_public_id?: string | null;
  extracted?: Record<string, unknown> | null;
  rules?: Record<string, unknown> | null;
  status: string;
  created_at: string;
  updated_at?: string;
};

/** Map a ScanRecord from the backend to the Inspection type used by dashboard components */
function mapScanToInspection(s: ScanRecord): Inspection {
  const rec = s.label_record ?? {};
  const mfr =
    (rec["manufacturer"] as { value?: string } | undefined)?.value ||
    (rec["manufacturer_name"] as { value?: string } | undefined)?.value ||
    null;
  const product =
    (rec["product_name"] as { value?: string } | undefined)?.value ||
    (rec["brand"] as { value?: string } | undefined)?.value ||
    null;

  // Map compliance_pct + violations to a legacy result string
  let result: string | null = null;
  if (s.status === "done" && s.compliance_pct === 100) result = "compliant";
  else if (s.status === "needs_review" || (s.violations && s.violations.length > 0)) result = "non-compliant";
  else if (s.status === "processing") result = "pending";
  else result = null;

  return {
    id: s.id,
    scan_id: String(s.id),
    inspector_id: s.user_id,
    product,
    category: s.category,
    manufacturer: mfr,
    result,
    score: s.compliance_pct,
    region: null,
    location: null,
    image_url: s.image_url,
    image_public_id: null,
    extracted: s.label_record as Record<string, unknown> | null,
    rules: null,
    status: s.status,
    created_at: s.created_at ?? new Date().toISOString(),
  };
}


function normalizeResult(result?: string | null) {
  const value = result?.toLowerCase();
  if (value === "compliant") return "compliant";
  if (
    value === "non-compliant" ||
    value === "noncompliant" ||
    value === "potential issues" ||
    value === "needs_review"
  ) {
    return "non-compliant";
  }
  return "pending";
}

function ResultBadge({ result }: { result?: string | null }) {
  const status = normalizeResult(result);

  if (status === "compliant") {
    return (
      <span className="inline-flex items-center gap-1.5 rounded-full bg-green-50 px-3 py-1 text-xs font-semibold text-green-700 ring-1 ring-inset ring-green-200">
        Compliant
      </span>
    );
  }

  if (status === "non-compliant") {
    return (
      <span className="inline-flex items-center gap-1.5 rounded-full bg-red-50 px-3 py-1 text-xs font-semibold text-red-700 ring-1 ring-inset ring-red-200">
        Non-Compliant
      </span>
    );
  }

  return (
    <span className="inline-flex items-center gap-1.5 rounded-full bg-blue-50 px-3 py-1 text-xs font-semibold text-blue-700 ring-1 ring-inset ring-blue-200">
      Pending
    </span>
  );
}

function StatCard({
  title,
  value,
  delta,
  icon,
  tone,
}: {
  title: string;
  value: number;
  delta?: string;
  icon: React.ReactNode;
  tone: "orange" | "green" | "red" | "blue";
}) {
  const toneMap = {
    orange: "bg-orange-50 text-[#f5a623] ring-orange-100",
    green: "bg-green-50 text-green-600 ring-green-100",
    red: "bg-red-50 text-red-500 ring-red-100",
    blue: "bg-blue-50 text-blue-500 ring-blue-100",
  };

  return (
    <div className="rounded-2xl border border-orange-100/80 bg-white p-5 shadow-sm ring-1 ring-black/[0.02] transition-all duration-200 hover:-translate-y-0.5 hover:shadow-md">
      <div className="flex items-start justify-between">
        <p className="text-sm font-medium text-slate-500">{title}</p>

        <div
          className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-lg ring-1 ${toneMap[tone]}`}
        >
          {icon}
        </div>
      </div>

      <p className="mt-3 text-3xl font-bold tabular-nums text-[#173b68]">
        {value}
      </p>

      {delta && (
        <p className="mt-1.5 text-xs font-medium text-slate-400">{delta}</p>
      )}
    </div>
  );
}

function getLast7DayCounts(inspections: Inspection[]) {
  const days: { label: string; count: number }[] = [];
  const today = new Date();

  for (let i = 6; i >= 0; i -= 1) {
    const day = new Date(today);
    day.setDate(day.getDate() - i);

    const label = day.toLocaleDateString("en-GB", {
      day: "2-digit",
      month: "short",
    });

    const count = inspections.filter((inspection) => {
      const created = new Date(inspection.created_at);
      return created.toDateString() === day.toDateString();
    }).length;

    days.push({ label, count });
  }

  return days;
}

function ScanOverview({ inspections }: { inspections: Inspection[] }) {
  const days = useMemo(() => getLast7DayCounts(inspections), [inspections]);

  const maxCount = Math.max(...days.map((d) => d.count), 5);
  const chartTop = 20;
  const chartBottom = 170;
  const chartLeft = 36;
  const chartRight = 540;

  const points = days.map((day, index) => {
    const x =
      chartLeft + (index / (days.length - 1)) * (chartRight - chartLeft);
    const y =
      chartBottom - (day.count / maxCount) * (chartBottom - chartTop);
    return { x, y, ...day };
  });

  const polyline = points.map((p) => `${p.x},${p.y}`).join(" ");

  const gridValues = [0, 0.25, 0.5, 0.75, 1].map((f) =>
    Math.round(maxCount * f)
  );

  return (
    <div className="rounded-2xl border border-orange-100/80 bg-white p-6 shadow-sm ring-1 ring-black/[0.02]">
      <div className="mb-4 flex items-center justify-between">
        <h2 className="text-lg font-bold text-[#173b68]">Scan Overview</h2>
        <span className="rounded-lg border border-slate-200 px-3 py-1.5 text-xs font-medium text-slate-500">
          Last 7 Days
        </span>
      </div>

      <svg viewBox="0 0 560 210" className="w-full">
        <line
          x1={chartLeft}
          y1={chartTop}
          x2={chartLeft}
          y2={chartBottom}
          stroke="#EDE6D8"
        />
        <line
          x1={chartLeft}
          y1={chartBottom}
          x2={chartRight}
          y2={chartBottom}
          stroke="#EDE6D8"
        />

        {gridValues.map((value, i) => (
          <text
            key={i}
            x={8}
            y={
              chartBottom -
              (i / (gridValues.length - 1)) * (chartBottom - chartTop) +
              3
            }
            fontSize="10"
            fill="#94a3b8"
          >
            {value}
          </text>
        ))}

        <polyline
          points={polyline}
          fill="none"
          stroke="#f5a623"
          strokeWidth="3"
          strokeLinecap="round"
          strokeLinejoin="round"
        />

        {points.map((p, i) => (
          <circle key={i} cx={p.x} cy={p.y} r="4" fill="#f5a623" />
        ))}

        {points.map((p, i) => (
          <text
            key={`label-${i}`}
            x={p.x}
            y={chartBottom + 20}
            fontSize="10"
            textAnchor="middle"
            fill="#94a3b8"
          >
            {p.label}
          </text>
        ))}
      </svg>
    </div>
  );
}

function ComplianceStatus({ inspections }: { inspections: Inspection[] }) {
  const compliant = inspections.filter(
    (item) => normalizeResult(item.result) === "compliant"
  ).length;

  const nonCompliant = inspections.filter(
    (item) => normalizeResult(item.result) === "non-compliant"
  ).length;

  const pending = inspections.filter(
    (item) => normalizeResult(item.result) === "pending"
  ).length;

  const total = inspections.length;

  const compliantPct = total > 0 ? (compliant / total) * 100 : 0;
  const nonCompliantPct = total > 0 ? (nonCompliant / total) * 100 : 0;

  const gradient = `conic-gradient(
    #22c55e 0% ${compliantPct}%,
    #f5a623 ${compliantPct}% ${compliantPct + nonCompliantPct}%,
    #3b82f6 ${compliantPct + nonCompliantPct}% 100%
  )`;

  const percentage = total > 0 ? Math.round(compliantPct) : 0;

  return (
    <div className="rounded-2xl border border-orange-100/80 bg-white p-6 shadow-sm ring-1 ring-black/[0.02]">
      <h2 className="mb-5 text-lg font-bold text-[#173b68]">
        Compliance Status
      </h2>

      <div className="flex items-center gap-6">
        <div
          className="relative flex h-32 w-32 shrink-0 items-center justify-center rounded-full"
          style={{ background: total > 0 ? gradient : "#f1f5f9" }}
        >
          <div className="flex h-[100px] w-[100px] items-center justify-center rounded-full bg-white text-center">
            <div>
              <p className="text-2xl font-bold tabular-nums text-[#173b68]">
                {percentage}%
              </p>
              <p className="text-[10px] text-slate-400">Compliant</p>
            </div>
          </div>
        </div>

        <div className="flex-1 space-y-3">
          <div className="flex items-center justify-between text-sm">
            <span className="flex items-center gap-2 text-slate-600">
              <span className="h-2.5 w-2.5 rounded-full bg-green-500" />
              Compliant
            </span>
            <span className="font-semibold tabular-nums text-slate-700">
              {compliant}
            </span>
          </div>

          <div className="flex items-center justify-between text-sm">
            <span className="flex items-center gap-2 text-slate-600">
              <span className="h-2.5 w-2.5 rounded-full bg-orange-400" />
              Non-Compliant
            </span>
            <span className="font-semibold tabular-nums text-slate-700">
              {nonCompliant}
            </span>
          </div>

          <div className="flex items-center justify-between text-sm">
            <span className="flex items-center gap-2 text-slate-600">
              <span className="h-2.5 w-2.5 rounded-full bg-blue-500" />
              Pending
            </span>
            <span className="font-semibold tabular-nums text-slate-700">
              {pending}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}

function RecentNotifications({ inspections }: { inspections: Inspection[] }) {
  const recent = inspections.slice(0, 3);

  const iconFor = (status: string) => {
    if (status === "compliant")
      return {
        icon: <CheckCircle2 className="h-4 w-4" />,
        tone: "bg-green-50 text-green-600 ring-green-100",
      };
    if (status === "non-compliant")
      return {
        icon: <AlertTriangle className="h-4 w-4" />,
        tone: "bg-red-50 text-red-500 ring-red-100",
      };
    return {
      icon: <ScanLine className="h-4 w-4" />,
      tone: "bg-orange-50 text-[#f5a623] ring-orange-100",
    };
  };

  const titleFor = (status: string) => {
    if (status === "compliant") return "Compliance Confirmed";
    if (status === "non-compliant") return "Non-Compliance Alert";
    return "New Scan Assigned";
  };

  const bodyFor = (inspection: Inspection, status: string) => {
    const name =
      inspection.manufacturer || inspection.product || "This establishment";

    if (status === "compliant") return `${name} has been marked as Compliant.`;
    if (status === "non-compliant") return `${name} flagged for review.`;
    return `A new inspection is pending for ${name}.`;
  };

  return (
    <div className="rounded-2xl border border-orange-100/80 bg-white p-6 shadow-sm ring-1 ring-black/[0.02]">
      <div className="mb-2 flex items-center justify-between">
        <h2 className="text-lg font-bold text-[#173b68]">
          Recent Notifications
        </h2>
        <Link
          to="/history"
          className="flex items-center gap-1 text-sm font-semibold text-[#2f7dd6] hover:text-[#173b68]"
        >
          View All
          <ArrowRight className="h-3.5 w-3.5" />
        </Link>
      </div>

      {recent.length === 0 ? (
        <div className="py-10 text-center">
          <CheckCircle2 className="mx-auto h-9 w-9 text-green-400" />
          <p className="mt-3 text-sm font-medium text-slate-500">
            No new notifications
          </p>
          <p className="mt-1 text-xs text-slate-400">You're all caught up.</p>
        </div>
      ) : (
        <div className="mt-3 divide-y divide-orange-50">
          {recent.map((inspection) => {
            const status = normalizeResult(inspection.result);
            const { icon, tone } = iconFor(status);

            return (
              <div key={inspection.id} className="flex gap-3 py-3.5">
                <div
                  className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-lg ring-1 ${tone}`}
                >
                  {icon}
                </div>

                <div className="min-w-0">
                  <p className="text-sm font-semibold text-[#173b68]">
                    {titleFor(status)}
                  </p>
                  <p className="mt-0.5 text-xs text-slate-500">
                    {bodyFor(inspection, status)}
                  </p>
                  <p className="mt-1 text-[11px] text-slate-400">
                    {new Date(inspection.created_at).toLocaleDateString()}
                  </p>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

function RecentInspections({ inspections }: { inspections: Inspection[] }) {
  const recent = inspections.slice(0, 5);

  return (
    <div className="overflow-hidden rounded-2xl border border-orange-100/80 bg-white shadow-sm ring-1 ring-black/[0.02]">
      <div className="flex items-center justify-between px-6 pb-4 pt-6">
        <h2 className="text-lg font-bold text-[#173b68]">
          Recent Inspections
        </h2>
        <Link
          to="/history"
          className="flex items-center gap-1 text-sm font-semibold text-[#2f7dd6] hover:text-[#173b68]"
        >
          View All
          <ArrowRight className="h-3.5 w-3.5" />
        </Link>
      </div>

      {recent.length === 0 ? (
        <div className="px-6 py-14 text-center">
          <FileSearch className="mx-auto h-10 w-10 text-slate-300" />
          <p className="mt-3 text-sm font-medium text-slate-500">
            No inspections yet
          </p>
          <p className="mt-1 text-xs text-slate-400">
            Start a new scan to see inspection records here.
          </p>
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full min-w-[560px] text-left text-sm">
            <thead>
              <tr className="border-b border-orange-100 text-xs font-semibold text-slate-500">
                <th className="px-6 pb-3 font-semibold">ID</th>
                <th className="px-3 pb-3 font-semibold">Establishment</th>
                <th className="px-3 pb-3 font-semibold">Date</th>
                <th className="px-3 pb-3 font-semibold">Status</th>
                <th className="px-6 pb-3 font-semibold">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-orange-50">
              {recent.map((inspection) => (
                <tr
                  key={inspection.id}
                  className="transition-colors hover:bg-orange-50/40"
                >
                  <td className="px-6 py-3.5 font-semibold text-[#2f7dd6]">
                    {inspection.scan_id}
                  </td>
                  <td className="px-3 py-3.5 text-slate-700">
                    {inspection.manufacturer ||
                      inspection.product ||
                      "Unnamed establishment"}
                  </td>
                  <td className="px-3 py-3.5 text-slate-500">
                    {new Date(inspection.created_at).toLocaleDateString(
                      "en-GB",
                      { day: "2-digit", month: "short", year: "numeric" }
                    )}
                  </td>
                  <td className="px-3 py-3.5">
                    <ResultBadge result={inspection.result} />
                  </td>
                  <td className="px-6 py-3.5">
                    <Link
                      to={`/history?scan=${inspection.scan_id}`}
                      className="flex items-center gap-1 font-semibold text-[#2f7dd6] hover:text-[#173b68]"
                    >
                      View
                      <ArrowRight className="h-3.5 w-3.5" />
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

function TopViolations({ inspections }: { inspections: Inspection[] }) {
  const violations = useMemo(() => {
    const counts: Record<string, number> = {};

    inspections.forEach((inspection) => {
      if (normalizeResult(inspection.result) === "non-compliant") {
        const category = inspection.category || "Other Violations";
        counts[category] = (counts[category] || 0) + 1;
      }
    });

    return Object.entries(counts)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 5);
  }, [inspections]);

  return (
    <div className="rounded-2xl border border-orange-100/80 bg-white p-6 shadow-sm ring-1 ring-black/[0.02]">
      <div className="mb-2 flex items-center justify-between">
        <h2 className="text-lg font-bold text-[#173b68]">Top Violations</h2>
        <Link
          to="/analytics"
          className="flex items-center gap-1 text-sm font-semibold text-[#2f7dd6] hover:text-[#173b68]"
        >
          View All
          <ArrowRight className="h-3.5 w-3.5" />
        </Link>
      </div>

      {violations.length === 0 ? (
        <div className="py-10 text-center">
          <ShieldCheck className="mx-auto h-9 w-9 text-green-400" />
          <p className="mt-3 text-sm font-medium text-slate-500">
            No violations recorded
          </p>
        </div>
      ) : (
        <div className="mt-2 divide-y divide-orange-50">
          {violations.map(([category, count]) => (
            <div
              key={category}
              className="flex items-center justify-between py-3.5"
            >
              <span className="text-sm font-medium text-[#173b68]">
                {category}
              </span>
              <span className="flex h-6 w-6 items-center justify-center rounded-full bg-orange-50 text-xs font-bold text-[#e8862b] ring-1 ring-inset ring-orange-100">
                {count}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function InspectorDashboard({
  inspections,
  userName,
}: {
  inspections: Inspection[];
  userName: string;
}) {
  const total = inspections.length;

  const compliant = inspections.filter(
    (item) => normalizeResult(item.result) === "compliant"
  ).length;

  const nonCompliant = inspections.filter(
    (item) => normalizeResult(item.result) === "non-compliant"
  ).length;

  const pending = Math.max(total - compliant - nonCompliant, 0);

  return (
    <div className="min-h-screen bg-gradient-to-b from-[#FFF1DC] to-[#FFF8EC]">
      <div className="mx-auto max-w-7xl space-y-6 px-4 py-8 sm:px-6 lg:px-8">
        {/* WELCOME */}
        <div className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-[#FCE1B0] to-[#FAD08A] px-7 py-6 shadow-sm">
          <div className="flex items-center justify-between gap-6">
            <div>
              <p className="text-lg text-[#7a5424]">Welcome back,</p>
              <h1 className="mt-1 text-3xl font-bold text-[#173b68]">
                {userName}
              </h1>
              <p className="mt-2 max-w-md text-sm text-[#8a6633]">
                Here's your scan activity and recent inspections today.
              </p>
            </div>

            <div className="hidden h-28 w-28 shrink-0 items-center justify-center rounded-full border-4 border-white/60 bg-white sm:flex">
              <Scale className="h-11 w-11 text-[#e8862b]" />
            </div>
          </div>
        </div>

        {/* STATS */}
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <StatCard
            title="Total Scans"
            value={total}
            tone="orange"
            icon={<ScanLine className="h-4.5 w-4.5" />}
          />
          <StatCard
            title="Compliant Scans"
            value={compliant}
            tone="green"
            icon={<CheckCircle2 className="h-4.5 w-4.5" />}
          />
          <StatCard
            title="Non-Compliant Scans"
            value={nonCompliant}
            tone="red"
            icon={<AlertTriangle className="h-4.5 w-4.5" />}
          />
          <StatCard
            title="Pending Review"
            value={pending}
            tone="blue"
            icon={<Clock3 className="h-4.5 w-4.5" />}
          />
        </div>

        {/* SCAN OVERVIEW + COMPLIANCE + NOTIFICATIONS */}
        <div className="grid gap-6 lg:grid-cols-3">
          <div className="lg:col-span-1">
            <ScanOverview inspections={inspections} />
          </div>
          <div className="lg:col-span-1">
            <ComplianceStatus inspections={inspections} />
          </div>
          <div className="lg:col-span-1">
            <RecentNotifications inspections={inspections} />
          </div>
        </div>

        {/* RECENT + VIOLATIONS */}
        <div className="grid gap-6 lg:grid-cols-2">
          <RecentInspections inspections={inspections} />
          <TopViolations inspections={inspections} />
        </div>
      </div>
    </div>
  );
}
function ManagementDashboard({
  inspections,
  userName,
  role,
}: {
  inspections: Inspection[];
  userName: string;
  role: string;
}) {
  const total = inspections.length;

  const compliant = inspections.filter(
    (item) => normalizeResult(item.result) === "compliant"
  ).length;

  const nonCompliant = inspections.filter(
    (item) => normalizeResult(item.result) === "non-compliant"
  ).length;

  const pending = Math.max(total - compliant - nonCompliant, 0);

  /*
   * =========================
   * SUPERVISOR DASHBOARD
   * =========================
   */

  if (role === "Supervisor") {
    return (
      <div className="min-h-screen bg-gradient-to-b from-[#FFF1DC] to-[#FFF8EC]">
        <div className="mx-auto max-w-7xl space-y-6 px-4 py-8 sm:px-6 lg:px-8">

          {/* WELCOME */}
          <div className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-[#F4A340] to-[#E98C25] px-7 py-7 shadow-sm">
            <div className="flex items-center justify-between gap-6">
              <div>
                <p className="text-lg font-medium text-white/80">
                  Supervisor Portal
                </p>

                <h1 className="mt-1 text-3xl font-bold text-white">
                  Welcome back, {userName}
                </h1>

                <p className="mt-2 max-w-xl text-sm text-white/80">
                  Monitor inspection activity, review compliance performance,
                  and manage your inspection team.
                </p>
              </div>

              <div className="hidden h-28 w-28 shrink-0 items-center justify-center rounded-full border-4 border-white/40 bg-white/20 sm:flex">
                <ShieldCheck className="h-11 w-11 text-white" />
              </div>
            </div>
          </div>

          {/* MANAGEMENT STATS */}
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">

            <StatCard
              title="Total Inspections"
              value={total}
              tone="orange"
              icon={<ScanLine className="h-4.5 w-4.5" />}
            />

            <StatCard
              title="Active Inspectors"
              value={0}
              delta="Awaiting user data"
              tone="blue"
              icon={<ShieldCheck className="h-4.5 w-4.5" />}
            />

            <StatCard
              title="Pending Reviews"
              value={pending}
              tone="orange"
              icon={<Clock3 className="h-4.5 w-4.5" />}
            />

            <StatCard
              title="Issues Detected"
              value={nonCompliant}
              tone="red"
              icon={<AlertTriangle className="h-4.5 w-4.5" />}
            />

          </div>

          {/* INSPECTION ACTIVITY + COMPLIANCE */}
          <div className="grid gap-6 lg:grid-cols-2">

            <ScanOverview inspections={inspections} />

            <ComplianceStatus inspections={inspections} />

          </div>

          {/* TEAM PERFORMANCE */}
          <div className="rounded-2xl border border-orange-100/80 bg-white p-6 shadow-sm ring-1 ring-black/[0.02]">

            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-lg font-bold text-[#173b68]">
                  Inspector Performance
                </h2>

                <p className="mt-1 text-sm text-slate-500">
                  Monitor inspection activity across your team.
                </p>
              </div>

              <Link
                to="/users"
                className="flex items-center gap-1 text-sm font-semibold text-[#2f7dd6] hover:text-[#173b68]"
              >
                Manage Users
                <ArrowRight className="h-3.5 w-3.5" />
              </Link>
            </div>

            <div className="mt-6 rounded-xl border border-dashed border-orange-200 bg-orange-50/40 px-6 py-10 text-center">

              <ShieldCheck className="mx-auto h-10 w-10 text-orange-300" />

              <p className="mt-3 text-sm font-semibold text-slate-600">
                Inspector performance data
              </p>

              <p className="mt-1 text-xs text-slate-400">
                Inspector-wise statistics will appear here once user data is
                connected.
              </p>

            </div>
          </div>

          {/* RECENT INSPECTIONS + VIOLATIONS */}
          <div className="grid gap-6 lg:grid-cols-2">

            <RecentInspections inspections={inspections} />

            <TopViolations inspections={inspections} />

          </div>

        </div>
      </div>
    );
  }

  /*
   * =========================
   * ADMINISTRATOR DASHBOARD
   * =========================
   */

  return (
    <div className="min-h-screen bg-gradient-to-b from-[#FFF1DC] to-[#FFF8EC]">
      <div className="mx-auto max-w-7xl space-y-6 px-4 py-8 sm:px-6 lg:px-8">

        {/* WELCOME */}
        <div className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-[#F4A340] to-[#E98C25] px-7 py-7 shadow-sm">
          <div className="flex items-center justify-between gap-6">

            <div>
              <p className="text-lg font-medium text-white/80">
                Administrator Portal
              </p>

              <h1 className="mt-1 text-3xl font-bold text-white">
                Welcome back, {userName}
              </h1>

              <p className="mt-2 max-w-xl text-sm text-white/80">
                Manage the Manak Setu system, monitor compliance, and oversee
                users, rules, and platform activity.
              </p>
            </div>

            <div className="hidden h-28 w-28 shrink-0 items-center justify-center rounded-full border-4 border-white/40 bg-white/20 sm:flex">
              <Scale className="h-11 w-11 text-white" />
            </div>

          </div>
        </div>

        {/* ADMIN STATS */}
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">

          <StatCard
            title="Total Inspections"
            value={total}
            tone="orange"
            icon={<ScanLine className="h-4.5 w-4.5" />}
          />

          <StatCard
            title="Total Users"
            value={0}
            delta="Awaiting user data"
            tone="blue"
            icon={<ShieldCheck className="h-4.5 w-4.5" />}
          />

          <StatCard
            title="Active Inspectors"
            value={0}
            delta="Awaiting user data"
            tone="green"
            icon={<CheckCircle2 className="h-4.5 w-4.5" />}
          />

          <StatCard
            title="Pending Reviews"
            value={pending}
            tone="orange"
            icon={<Clock3 className="h-4.5 w-4.5" />}
          />

        </div>

        {/* SYSTEM ACTIVITY */}
        <div className="grid gap-6 lg:grid-cols-2">

          <ScanOverview inspections={inspections} />

          <ComplianceStatus inspections={inspections} />

        </div>

        {/* USER OVERVIEW */}
        <div className="rounded-2xl border border-orange-100/80 bg-white p-6 shadow-sm ring-1 ring-black/[0.02]">

          <div className="flex items-center justify-between">

            <div>
              <h2 className="text-lg font-bold text-[#173b68]">
                User Overview
              </h2>

              <p className="mt-1 text-sm text-slate-500">
                Manage officers and system users.
              </p>
            </div>

            <Link
              to="/users"
              className="flex items-center gap-1 text-sm font-semibold text-[#2f7dd6] hover:text-[#173b68]"
            >
              Manage Users
              <ArrowRight className="h-3.5 w-3.5" />
            </Link>

          </div>

          <div className="mt-6 grid gap-4 sm:grid-cols-3">

            <div className="rounded-xl border border-blue-100 bg-blue-50/50 p-5">
              <p className="text-sm font-medium text-slate-500">
                Inspectors
              </p>

              <p className="mt-2 text-3xl font-bold text-[#173b68]">
                0
              </p>

              <p className="mt-1 text-xs text-slate-400">
                Awaiting user data
              </p>
            </div>

            <div className="rounded-xl border border-orange-100 bg-orange-50/50 p-5">
              <p className="text-sm font-medium text-slate-500">
                Supervisors
              </p>

              <p className="mt-2 text-3xl font-bold text-[#173b68]">
                0
              </p>

              <p className="mt-1 text-xs text-slate-400">
                Awaiting user data
              </p>
            </div>

            <div className="rounded-xl border border-green-100 bg-green-50/50 p-5">
              <p className="text-sm font-medium text-slate-500">
                Administrators
              </p>

              <p className="mt-2 text-3xl font-bold text-[#173b68]">
                0
              </p>

              <p className="mt-1 text-xs text-slate-400">
                Awaiting user data
              </p>
            </div>

          </div>
        </div>

        {/* MANAGEMENT SHORTCUTS */}
        <div className="grid gap-6 lg:grid-cols-3">

          <Link
            to="/rules"
            className="rounded-2xl border border-orange-100 bg-white p-6 shadow-sm transition hover:-translate-y-0.5 hover:shadow-md"
          >
            <Scale className="h-8 w-8 text-[#f5a623]" />

            <h3 className="mt-4 font-bold text-[#173b68]">
              Rules Management
            </h3>

            <p className="mt-2 text-sm text-slate-500">
              Configure and manage compliance rules.
            </p>

            <div className="mt-4 flex items-center gap-1 text-sm font-semibold text-[#2f7dd6]">
              Open Rules
              <ArrowRight className="h-3.5 w-3.5" />
            </div>
          </Link>

          <Link
            to="/compliance"
            className="rounded-2xl border border-orange-100 bg-white p-6 shadow-sm transition hover:-translate-y-0.5 hover:shadow-md"
          >
            <ShieldCheck className="h-8 w-8 text-green-500" />

            <h3 className="mt-4 font-bold text-[#173b68]">
              Compliance
            </h3>

            <p className="mt-2 text-sm text-slate-500">
              Review overall compliance performance.
            </p>

            <div className="mt-4 flex items-center gap-1 text-sm font-semibold text-[#2f7dd6]">
              Open Compliance
              <ArrowRight className="h-3.5 w-3.5" />
            </div>
          </Link>

          <Link
            to="/audit"
            className="rounded-2xl border border-orange-100 bg-white p-6 shadow-sm transition hover:-translate-y-0.5 hover:shadow-md"
          >
            <FileSearch className="h-8 w-8 text-[#2f7dd6]" />

            <h3 className="mt-4 font-bold text-[#173b68]">
              Audit Trail
            </h3>

            <p className="mt-2 text-sm text-slate-500">
              Review system activity and administrative actions.
            </p>

            <div className="mt-4 flex items-center gap-1 text-sm font-semibold text-[#2f7dd6]">
              Open Audit Trail
              <ArrowRight className="h-3.5 w-3.5" />
            </div>
          </Link>

        </div>

        {/* RECENT ACTIVITY */}
        <div className="grid gap-6 lg:grid-cols-2">

          <RecentInspections inspections={inspections} />

          <TopViolations inspections={inspections} />

        </div>

      </div>
    </div>
  );
}

export function DashboardPage() {
  const { user } = useAuth();

  const [inspections, setInspections] = useState<Inspection[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!user) return;

    async function loadData() {
      try {
        setLoading(true);
        setError("");

        // Fetch scans — inspector role only sees own scans (enforced by backend)
        const scansResp = await apiListScans({ page: 1, page_size: 100 });
        const mapped = scansResp.items.map(mapScanToInspection);
        setInspections(mapped);
      } catch (err) {
        console.error(err);
        setError("Unable to load inspection data.");
      } finally {
        setLoading(false);
      }
    }

    loadData();
  }, [user]);

  if (!user) return null;

  if (loading) {
    return (
      <div className="flex min-h-[70vh] items-center justify-center bg-gradient-to-b from-[#FFF1DC] to-[#FFF8EC]">
        <div className="text-center">
          <div className="mx-auto h-8 w-8 animate-spin rounded-full border-4 border-orange-100 border-t-[#f5a623]" />
          <p className="mt-3 text-sm text-slate-500">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-[70vh] bg-gradient-to-b from-[#FFF1DC] to-[#FFF8EC] p-6">
        <div className="mx-auto max-w-2xl rounded-2xl border border-red-200 bg-white p-8 text-center shadow-sm">
          <AlertTriangle className="mx-auto h-10 w-10 text-red-500" />
          <h2 className="mt-4 text-lg font-bold text-[#173b68]">
            Dashboard data unavailable
          </h2>
          <p className="mt-2 text-sm text-slate-500">{error}</p>
          <p className="mt-2 text-xs text-slate-400">
            Make sure the FastAPI backend is running on port 8000.
          </p>
        </div>
      </div>
    );
  }

  if (user.role === "Inspector") {
    return (
      <InspectorDashboard inspections={inspections} userName={user.name} />
    );
  }

  return (
    <ManagementDashboard
      inspections={inspections}
      userName={user.name}
      role={user.role}
    />
  );
}