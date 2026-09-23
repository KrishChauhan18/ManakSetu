import { createContext, useContext, useState, type ReactNode } from "react";
import type { Inspection, RuleCheck } from "../types";
import { PRODUCTS, MANUFACTURERS, RULES, INSPECTIONS, buildAuditTrail } from "../data/mockData";
import type { ResultStatus, Severity, ExtractedField } from "../types";

interface Decision {
  ruleId: string;
  decision: "Confirmed" | "Marked Compliant" | "Re-analysis Requested";
  overrideReason?: string;
}

interface FlowState {
  active: Inspection | null;
  decisions: Decision[];
  images: { id: string; label: string; url: string }[];
  generateInspection: () => void;
  updateExtractedField: (label: string, value: string) => void;
  setImages: (imgs: { id: string; label: string; url: string }[]) => void;
  recordDecision: (d: Decision) => void;
  finalize: () => Inspection | null;
  getInspection: (scanId: string) => Inspection | undefined;
}

const FlowContext = createContext<FlowState | null>(null);

function pad(n: number) { return String(n).padStart(3, "0"); }

function seededRandom(seed: number) {
  let s = seed;
  return () => { s = (s * 9301 + 49297) % 233280; return s / 233280; };
}

function generate(): Inspection {
  const r = seededRandom(Date.now() % 100000);
  const pick = <T,>(arr: T[]) => arr[Math.floor(r() * arr.length)];
  const product = pick(PRODUCTS);
  const extracted: ExtractedField[] = [
    { label: "Manufacturer", value: pick(MANUFACTURERS), confidence: 95 + Math.floor(r() * 4), box: { x: 8, y: 10, w: 55, h: 8 } },
    { label: "MRP", value: `₹${Math.floor(r() * 400 + 40)}`, confidence: 97 + Math.floor(r() * 3), box: { x: 65, y: 8, w: 27, h: 10 } },
    { label: "Net Quantity", value: `${pick([100, 200, 500, 1])}${pick(["g", "ml", "kg"])}`, confidence: 94 + Math.floor(r() * 5), box: { x: 8, y: 22, w: 30, h: 8 } },
    { label: "Manufacturing Date", value: "08/2026", confidence: 91 + Math.floor(r() * 8), box: { x: 8, y: 34, w: 26, h: 7 } },
    { label: "Best Before", value: "6 Months", confidence: 87 + Math.floor(r() * 10), box: { x: 40, y: 34, w: 24, h: 7 } },
    { label: "Consumer Care", value: "1800-XXX-XXXX", confidence: 82 + Math.floor(r() * 12), box: { x: 8, y: 46, w: 45, h: 7 } },
    { label: "Batch Number", value: `B${Math.floor(r() * 900000 + 100000)}`, confidence: 96 + Math.floor(r() * 4), box: { x: 60, y: 46, w: 32, h: 7 } },
  ];

  const enabledRules = RULES.filter((rl) => rl.status === "Enabled").slice(0, 12);
  const violationIdx = new Set<number>();
  violationIdx.add(5); // Consumer Care -> Review Required
  violationIdx.add(6); // Country of Origin -> Potential Issue
  const rules: RuleCheck[] = enabledRules.map((rule, i) => {
    const isViolation = violationIdx.has(i);
    const status: ResultStatus = !isViolation ? "Compliant" : i === 6 ? "Potential Issue" : "Review Required";
    return {
      ruleId: rule.ruleId,
      name: rule.name,
      category: rule.category,
      status,
      severity: rule.severity as Severity,
      confidence: status === "Compliant" ? 96 : status === "Review Required" ? 82 : 91,
      evidence: status === "Compliant" ? "Field detected and validated against pattern." : `"${rule.name}" not clearly detected or fails required format.`,
      recommendation: rule.recommendation,
    };
  });

  const weight: Record<Severity, number> = { Critical: 4, High: 3, Medium: 2, Low: 1 };
  const total = rules.reduce((s, ru) => s + weight[ru.severity], 0);
  const lost = rules.filter((ru) => ru.status !== "Compliant").reduce((s, ru) => s + weight[ru.severity], 0);
  const score = Math.round(((total - lost) / total) * 100);

  return {
    scanId: `MA-2026-${pad(Math.floor(r() * 900 + 100))}`,
    product: product.name,
    category: product.category,
    manufacturer: extracted[0].value,
    result: score >= 92 ? "Compliant" : score >= 75 ? "Review Required" : "Potential Issue",
    score,
    officer: "Anjali Sharma",
    region: "Dehradun",
    location: "Dehradun Market Inspection Zone 3",
    date: new Date().toISOString(),
    image: "https://images.unsplash.com/photo-1584473457406-6240486418e9?w=600&q=80",
    extracted,
    rules,
  };
}

export function InspectionFlowProvider({ children }: { children: ReactNode }) {
  const [active, setActive] = useState<Inspection | null>(null);
  const [decisions, setDecisions] = useState<Decision[]>([]);
  const [images, setImages] = useState<{ id: string; label: string; url: string }[]>([]);
  const [finalized, setFinalized] = useState<Record<string, Inspection>>({});

  const generateInspection = () => {
    const insp = generate();
    setActive(insp);
    setDecisions([]);
  };

  const updateExtractedField = (label: string, value: string) => {
    setActive((prev) => prev ? { ...prev, extracted: prev.extracted.map((f) => f.label === label ? { ...f, value } : f) } : prev);
  };

  const recordDecision = (d: Decision) => {
    setDecisions((prev) => [...prev.filter((x) => x.ruleId !== d.ruleId), d]);
  };

  const finalize = () => {
    if (!active) return null;
    setFinalized((prev) => ({ ...prev, [active.scanId]: active }));
    return active;
  };

  const getInspection = (scanId: string) => {
    if (active?.scanId === scanId) return active;
    if (finalized[scanId]) return finalized[scanId];
    return INSPECTIONS.find((i) => i.scanId === scanId);
  };

  return (
    <FlowContext.Provider value={{ active, decisions, images, generateInspection, updateExtractedField, setImages, recordDecision, finalize, getInspection }}>
      {children}
    </FlowContext.Provider>
  );
}

export function useInspectionFlow() {
  const ctx = useContext(FlowContext);
  if (!ctx) throw new Error("useInspectionFlow must be used within InspectionFlowProvider");
  return ctx;
}

export { buildAuditTrail };
