import { confidenceTone } from "../utils/format";
import { cn } from "../utils/cn";

export function ConfidenceBadge({ value, showBar = true }: { value: number; showBar?: boolean }) {
  const tone = confidenceTone(value);
  return (
    <div className="flex items-center gap-2">
      <span className={cn("font-tabular text-xs font-bold", tone.text)}>{value}%</span>
      {showBar && (
        <div className={cn("h-1.5 w-14 overflow-hidden rounded-full", tone.track)}>
          <div className={cn("h-full rounded-full transition-all duration-700", tone.bg)} style={{ width: `${value}%` }} />
        </div>
      )}
    </div>
  );
}
