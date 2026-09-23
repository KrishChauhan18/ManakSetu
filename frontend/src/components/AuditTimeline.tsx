import { LogIn, ImagePlus, ScanText, ListChecks, ShieldAlert, UserCheck, FileCheck } from "lucide-react";
import type { AuditEvent } from "../types";
import { formatDateTime } from "../utils/format";

const ICONS: Record<string, typeof LogIn> = {
  "Inspector Login": LogIn,
  "Image Uploaded": ImagePlus,
  "OCR Completed": ScanText,
  "Rules Evaluated": ListChecks,
  "Issue Detected": ShieldAlert,
  "Inspector Decision": UserCheck,
  "Report Generated": FileCheck,
};

export function AuditTimeline({ events }: { events: AuditEvent[] }) {
  return (
    <div className="relative pl-8">
      <div className="absolute left-[15px] top-2 bottom-2 w-px bg-line" />
      <div className="space-y-6">
        {events.map((e) => {
          const Icon = ICONS[e.action] ?? LogIn;
          return (
            <div key={e.eventId} className="relative">
              <div className="absolute -left-8 top-0 flex h-8 w-8 items-center justify-center rounded-full border-2 border-cyan-500 bg-white">
                <Icon size={14} className="text-cyan-600" />
              </div>
              <div className="rounded-lg border border-line bg-paper-card p-4">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <p className="font-display text-sm font-bold text-text-1">{e.action}</p>
                  <span className="font-code text-[11px] text-text-3">{e.eventId}</span>
                </div>
                <div className="mt-2 grid grid-cols-2 gap-x-4 gap-y-1 text-xs text-text-2 sm:grid-cols-4">
                  <p><span className="text-text-3">Inspector:</span> {e.inspectorId}</p>
                  <p><span className="text-text-3">Time:</span> {formatDateTime(e.timestamp)}</p>
                  <p><span className="text-text-3">Device:</span> {e.device}</p>
                  <p><span className="text-text-3">IP:</span> {e.ip}</p>
                </div>
                <div className="mt-2 flex flex-wrap items-center gap-2 border-t border-line pt-2 font-code text-[11px] text-text-3">
                  <span>prev: {e.prevHash}</span>
                  <span className="text-cyan-600">→</span>
                  <span className="font-semibold text-text-1">hash: {e.currentHash}</span>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
