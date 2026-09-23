import { useNavigate } from "react-router-dom";
import type { Inspection } from "../types";
import { StatusBadge } from "./StatusBadge";
import { ConfidenceBadge } from "./ConfidenceBadge";
import { formatDate } from "../utils/format";

export function InspectionTable({ rows, compact = false }: { rows: Inspection[]; compact?: boolean }) {
  const navigate = useNavigate();
  return (
    <div className="overflow-x-auto">
      <table className="w-full min-w-[860px] text-left text-sm">
        <thead>
          <tr className="border-b border-line text-xs uppercase tracking-wide text-text-3">
            <th className="py-2.5 pr-4 font-semibold">Scan ID</th>
            <th className="py-2.5 pr-4 font-semibold">Product</th>
            {!compact && <th className="py-2.5 pr-4 font-semibold">Category</th>}
            <th className="py-2.5 pr-4 font-semibold">Result</th>
            <th className="py-2.5 pr-4 font-semibold">Confidence</th>
            {!compact && <th className="py-2.5 pr-4 font-semibold">Officer</th>}
            <th className="py-2.5 pr-4 font-semibold">Date</th>
            <th className="py-2.5 pr-4 font-semibold">Status</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((r) => (
            <tr
              key={r.scanId}
              onClick={() => navigate(`/inspection/${r.scanId}`)}
              className="cursor-pointer border-b border-line/70 transition-colors hover:bg-paper"
            >
              <td className="py-3 pr-4 font-code text-xs font-medium text-text-1">{r.scanId}</td>
              <td className="py-3 pr-4">
                <p className="font-medium text-text-1">{r.product}</p>
                <p className="text-xs text-text-3">{r.manufacturer}</p>
              </td>
              {!compact && <td className="py-3 pr-4 text-text-2">{r.category}</td>}
              <td className="py-3 pr-4"><StatusBadge status={r.result} /></td>
              <td className="py-3 pr-4"><ConfidenceBadge value={r.score} /></td>
              {!compact && <td className="py-3 pr-4 text-text-2">{r.officer}</td>}
              <td className="py-3 pr-4 whitespace-nowrap text-text-2">{formatDate(r.date)}</td>
              <td className="py-3 pr-4">
                <span className="rounded-md bg-paper px-2 py-1 text-xs font-medium text-text-2 border border-line">
                  {r.result === "Compliant" ? "Closed" : "Open"}
                </span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
