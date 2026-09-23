export type Role = "Inspector" | "Supervisor" | "Administrator" | "Manufacturer";

export type ResultStatus = "Compliant" | "Review Required" | "Potential Issue";

export type Severity = "Critical" | "High" | "Medium" | "Low";

export interface Officer {
  id: string;
  name: string;
  role: Role;
  department: string;
  region: string;
  status: "Active" | "Inactive";
  lastActive: string;
  avatarColor: string;
}

export interface ExtractedField {
  label: string;
  value: string;
  confidence: number; // 0-100
  box: { x: number; y: number; w: number; h: number }; // % of image
}

export interface RuleCheck {
  ruleId: string;
  name: string;
  category: string;
  status: ResultStatus;
  severity: Severity;
  confidence: number;
  evidence: string;
  recommendation: string;
}

export interface Inspection {
  scanId: string;
  product: string;
  category: string;
  manufacturer: string;
  result: ResultStatus;
  score: number;
  officer: string;
  region: string;
  location: string;
  date: string;
  image: string;
  extracted: ExtractedField[];
  rules: RuleCheck[];
}

export interface Rule {
  ruleId: string;
  name: string;
  category: string;
  version: string;
  severity: Severity;
  status: "Enabled" | "Disabled";
  description: string;
  condition: string;
  recommendation: string;
}

export interface AuditEvent {
  eventId: string;
  scanId: string;
  inspectorId: string;
  timestamp: string;
  action: string;
  device: string;
  ip: string;
  prevHash: string;
  currentHash: string;
}

export interface Notification {
  id: string;
  type: "rule_update" | "flag" | "system";
  message: string;
  relatedRuleId?: string;
  read: boolean;
  timestamp: string;
  targetRole: Role | "All";
}