import type { Inspection, Rule, Officer, AuditEvent, RuleCheck, ExtractedField, ResultStatus, Severity,Notification } from "../types";



export const INITIAL_NOTIFICATIONS: Notification[] = [
  {
    id: "NOTIF-001",
    type: "rule_update",
    message: 'Rule LM-006 "Consumer Care Details" was updated by Administrator.',
    relatedRuleId: "LM-006",
    read: false,
    timestamp: daysAgo(1),
    targetRole: "Inspector",
  },
  {
    id: "NOTIF-002",
    type: "rule_update",
    message: 'Rule LM-019 "FSSAI License Number" severity changed to Critical.',
    relatedRuleId: "LM-019",
    read: true,
    timestamp: daysAgo(3),
    targetRole: "Inspector",
  },
];
export const MANUFACTURERS = [
  "Shakti Foods Pvt. Ltd.",
  "GreenHarvest Consumer Products",
  "UrbanCare Industries",
  "Nilgiri Agro Exports",
  "Suryodaya Home Essentials",
  "Kaveri Textile Mills",
  "Himalayan Springs Beverages",
  "Trivani Cosmetics Ltd.",
  "Rajdhani Grain Co.",
  "BlueLotus Personal Care",
];

export const CATEGORIES = [
  "Biscuits & Bakery",
  "Rice & Grains",
  "Cooking Oil",
  "Shampoo & Haircare",
  "Detergent",
  "Packaged Spices",
  "Bottled Water",
  "Soap",
  "Textile Products",
];

export const PRODUCTS: { name: string; category: string }[] = [
  { name: "Golden Crunch Biscuits 200g", category: "Biscuits & Bakery" },
  { name: "Premium Basmati Rice 5kg", category: "Rice & Grains" },
  { name: "Sunrise Refined Sunflower Oil 1L", category: "Cooking Oil" },
  { name: "Silk Shine Herbal Shampoo 340ml", category: "Shampoo & Haircare" },
  { name: "PowerWash Detergent Powder 1kg", category: "Detergent" },
  { name: "Garam Masala Blend 100g", category: "Packaged Spices" },
  { name: "Himalayan Mineral Water 1L", category: "Bottled Water" },
  { name: "Neem Fresh Bathing Soap 125g", category: "Soap" },
  { name: "Cotton Weave Bedsheet Set", category: "Textile Products" },
  { name: "Classic Marie Biscuits 250g", category: "Biscuits & Bakery" },
  { name: "Sona Masoori Rice 10kg", category: "Rice & Grains" },
  { name: "Mustard Kachi Ghani Oil 1L", category: "Cooking Oil" },
  { name: "Anti-Dandruff Shampoo 200ml", category: "Shampoo & Haircare" },
  { name: "Turmeric Powder 200g", category: "Packaged Spices" },
  { name: "Sparkle Dishwash Bar 200g", category: "Soap" },
];

const REGIONS = ["Dehradun", "Haridwar", "Nainital", "Roorkee", "Rudrapur", "Rishikesh"];
const OFFICER_NAMES = [
  "Anjali Sharma", "Vikram Rawat", "Priya Nair", "Rohit Bisht", "Sana Qureshi",
  "Arjun Mehta", "Kavita Joshi", "Deepak Rana", "Meera Pillai", "Farhan Ali",
];

function seededRandom(seed: number) {
  let s = seed;
  return () => {
    s = (s * 9301 + 49297) % 233280;
    return s / 233280;
  };
}
const rnd = seededRandom(42);
const pick = <T,>(arr: T[]) => arr[Math.floor(rnd() * arr.length)];
const int = (min: number, max: number) => Math.floor(rnd() * (max - min + 1)) + min;

function pad(n: number, len = 3) {
  return String(n).padStart(len, "0");
}

export const RULES: Rule[] = [
  { ruleId: "LM-001", name: "Manufacturer / Packer / Importer Details", category: "All", version: "2023", severity: "High", status: "Enabled", description: "Name and complete address of the manufacturer, packer, or importer must be declared.", condition: "manufacturer_field IS NOT EMPTY AND address IS NOT EMPTY", recommendation: "Ensure manufacturer name and full address are clearly printed." },
  { ruleId: "LM-002", name: "Net Quantity Declaration", category: "All", version: "2023", severity: "Critical", status: "Enabled", description: "Net quantity must be declared in standard units (g, kg, ml, l).", condition: "net_quantity MATCHES unit_pattern", recommendation: "Declare net quantity using standard SI units in the prescribed format." },
  { ruleId: "LM-003", name: "MRP Declaration", category: "All", version: "2023", severity: "Critical", status: "Enabled", description: "Maximum Retail Price inclusive of all taxes must be declared with ₹ symbol.", condition: "mrp MATCHES currency_pattern", recommendation: "Print MRP inclusive of all taxes with the ₹ symbol clearly visible." },
  { ruleId: "LM-004", name: "Manufacturing Date", category: "All", version: "2023", severity: "High", status: "Enabled", description: "Month and year of manufacture or packing must be declared.", condition: "mfg_date MATCHES MM/YYYY", recommendation: "Print manufacturing/packing date in MM/YYYY format." },
  { ruleId: "LM-005", name: "Expiry / Best Before Date", category: "Food, Cosmetics", version: "2023", severity: "Critical", status: "Enabled", description: "Expiry or best-before date must be declared and later than the manufacturing date.", condition: "expiry_date > mfg_date", recommendation: "Ensure expiry date is present and logically after the manufacturing date." },
  { ruleId: "LM-006", name: "Consumer Care Details", category: "All", version: "2023", severity: "Medium", status: "Enabled", description: "Name, address, telephone number or email of consumer care must be declared.", condition: "consumer_care IS NOT EMPTY", recommendation: "Verify declaration visibility and completeness of consumer care contact." },
  { ruleId: "LM-007", name: "Country of Origin", category: "All", version: "2023", severity: "High", status: "Enabled", description: "Country of origin must be declared for imported goods.", condition: "country_of_origin IS NOT EMPTY", recommendation: "Declare the country of origin prominently on the principal display panel." },
  { ruleId: "LM-008", name: "Unit Sale Price", category: "All", version: "2018", severity: "Medium", status: "Enabled", description: "Price per unit quantity (per kg / per litre) should be declared where applicable.", condition: "unit_price IS NOT EMPTY", recommendation: "Add unit sale price to assist price comparison." },
  { ruleId: "LM-009", name: "Language Requirement (Hindi + English)", category: "All", version: "2011", severity: "Medium", status: "Enabled", description: "Declarations must appear in Hindi (Devanagari) and English.", condition: "hindi_text_present = TRUE", recommendation: "Add bilingual declaration in Hindi and English." },
  { ruleId: "LM-010", name: "Batch / Lot Number", category: "All", version: "2023", severity: "Medium", status: "Enabled", description: "A batch or lot number must be declared for traceability.", condition: "batch_number IS NOT EMPTY", recommendation: "Print a unique batch/lot identifier on every unit." },
  { ruleId: "LM-011", name: "Ingredients / Contents List", category: "Food, Cosmetics", version: "2023", severity: "Medium", status: "Enabled", description: "List of ingredients in descending order of composition.", condition: "ingredients_list IS NOT EMPTY", recommendation: "Declare full ingredient list in descending order of quantity." },
  { ruleId: "LM-012", name: "Allergen Declaration", category: "Food", version: "2023", severity: "High", status: "Enabled", description: "Common allergens must be highlighted separately.", condition: "allergen_field IS NOT EMPTY", recommendation: "Highlight allergen information distinctly from the ingredients list." },
  { ruleId: "LM-013", name: "Nutritional Information", category: "Food", version: "2023", severity: "Low", status: "Enabled", description: "Nutritional facts panel should be present for packaged food.", condition: "nutrition_table IS NOT EMPTY", recommendation: "Include a nutritional information table per serving." },
  { ruleId: "LM-014", name: "Font Size Compliance", category: "All", version: "2011", severity: "Low", status: "Enabled", description: "Declarations must meet minimum font size requirements based on package size.", condition: "font_height >= min_required", recommendation: "Increase font size of mandatory declarations to meet minimum standards." },
  { ruleId: "LM-015", name: "Legibility & Contrast", category: "All", version: "2011", severity: "Medium", status: "Enabled", description: "Text must be printed with sufficient contrast against background for legibility.", condition: "ocr_confidence >= threshold", recommendation: "Improve print contrast to ensure legibility under normal light." },
  { ruleId: "LM-016", name: "Textile Fibre Composition", category: "Textile", version: "2023", severity: "Medium", status: "Enabled", description: "Fibre composition percentage must be declared for textile products.", condition: "fibre_composition IS NOT EMPTY", recommendation: "Declare fibre composition percentage on the label." },
  { ruleId: "LM-017", name: "Care Instructions (Textile)", category: "Textile", version: "2018", severity: "Low", status: "Enabled", description: "Washing/care instructions should be present for textile products.", condition: "care_instructions IS NOT EMPTY", recommendation: "Add standard care/washing instruction symbols or text." },
  { ruleId: "LM-018", name: "Cosmetic Usage Direction", category: "Cosmetics", version: "2023", severity: "Low", status: "Enabled", description: "Directions for use should be declared for cosmetic products.", condition: "usage_direction IS NOT EMPTY", recommendation: "Add clear usage directions on the label." },
  { ruleId: "LM-019", name: "FSSAI License Number", category: "Food", version: "2023", severity: "Critical", status: "Enabled", description: "A valid 14-digit FSSAI license number must be printed on food packages.", condition: "fssai_number MATCHES 14_digit_pattern", recommendation: "Print the valid FSSAI license number on the package." },
  { ruleId: "LM-020", name: "Recycling / Plastic Declaration", category: "All", version: "2023", severity: "Low", status: "Enabled", description: "Plastic packaging must carry recycling code and material declaration.", condition: "recycling_code IS NOT EMPTY", recommendation: "Add applicable recycling code as per plastic waste rules." },
  { ruleId: "LM-021", name: "Declaration Placement (Principal Display Panel)", category: "All", version: "2018", severity: "Medium", status: "Disabled", description: "All mandatory declarations should be grouped on the principal display panel where feasible.", condition: "declarations_grouped = TRUE", recommendation: "Group mandatory declarations together for easier verification." },
  { ruleId: "LM-022", name: "State-specific Multilingual Requirement", category: "All", version: "2015", severity: "Low", status: "Disabled", description: "Certain states require an additional regional language declaration.", condition: "regional_language_present = TRUE", recommendation: "Add the applicable state regional language declaration." },
];

const VIOLATION_POOL = ["LM-003", "LM-006", "LM-007", "LM-004", "LM-009", "LM-002", "LM-019", "LM-014"];

function buildExtractedFields(seed: number): ExtractedField[] {
  const r = seededRandom(seed);
  return [
    { label: "Manufacturer", value: pick(MANUFACTURERS), confidence: 90 + Math.floor(r() * 9), box: { x: 8, y: 10, w: 55, h: 8 } },
    { label: "MRP", value: `₹${int(20, 899)}`, confidence: 92 + Math.floor(r() * 8), box: { x: 65, y: 8, w: 27, h: 10 } },
    { label: "Net Quantity", value: `${pick([100, 200, 250, 500, 1, 5, 10])}${pick(["g", "g", "ml", "kg", "L"])}`, confidence: 88 + Math.floor(r() * 10), box: { x: 8, y: 22, w: 30, h: 8 } },
    { label: "Manufacturing Date", value: `${pick(["01", "03", "05", "07", "08", "11"])}/2026`, confidence: 85 + Math.floor(r() * 12), box: { x: 8, y: 34, w: 26, h: 7 } },
    { label: "Best Before", value: `${pick([3, 6, 9, 12, 18, 24])} Months`, confidence: 80 + Math.floor(r() * 15), box: { x: 40, y: 34, w: 24, h: 7 } },
    { label: "Consumer Care", value: `1800-${int(100, 999)}-${int(1000, 9999)}`, confidence: 78 + Math.floor(r() * 18), box: { x: 8, y: 46, w: 45, h: 7 } },
    { label: "Batch Number", value: `B${int(100000, 999999)}`, confidence: 90 + Math.floor(r() * 9), box: { x: 60, y: 46, w: 32, h: 7 } },
  ];
}

function buildRuleChecks(seed: number): RuleCheck[] {
  const r = seededRandom(seed);
  const violationCount = Math.floor(r() * 3);
  const chosen = new Set<string>();
  while (chosen.size < violationCount) chosen.add(VIOLATION_POOL[Math.floor(r() * VIOLATION_POOL.length)]);

  return RULES.filter((rl) => rl.status === "Enabled").slice(0, 12).map((rule) => {
    const isViolation = chosen.has(rule.ruleId);
    const status: ResultStatus = !isViolation ? "Compliant" : r() > 0.5 ? "Potential Issue" : "Review Required";
    return {
      ruleId: rule.ruleId,
      name: rule.name,
      category: rule.category,
      status,
      severity: rule.severity,
      confidence: status === "Compliant" ? 94 + Math.floor(r() * 6) : 60 + Math.floor(r() * 30),
      evidence: status === "Compliant" ? "Field detected and validated against pattern." : `Field "${rule.name}" not clearly detected or does not satisfy required format.`,
      recommendation: rule.recommendation,
    };
  });
}

function scoreFromRules(rules: RuleCheck[]): number {
  const weight: Record<Severity, number> = { Critical: 4, High: 3, Medium: 2, Low: 1 };
  const total = rules.reduce((s, r) => s + weight[r.severity], 0);
  const lost = rules.filter((r) => r.status !== "Compliant").reduce((s, r) => s + weight[r.severity], 0);
  return Math.max(38, Math.round(((total - lost) / total) * 100));
}

function resultFromScore(score: number): ResultStatus {
  if (score >= 92) return "Compliant";
  if (score >= 75) return "Review Required";
  return "Potential Issue";
}

const IMAGES = [
  "https://images.unsplash.com/photo-1584473457406-6240486418e9?w=600&q=80",
  "https://images.unsplash.com/photo-1601599963565-b7f49deb4a86?w=600&q=80",
  "https://images.unsplash.com/photo-1620574387735-3624d75b2dbc?w=600&q=80",
  "https://images.unsplash.com/photo-1610725664285-7c57e6eeac3f?w=600&q=80",
  "https://images.unsplash.com/photo-1583947581924-860bda6a26df?w=600&q=80",
  "https://images.unsplash.com/photo-1615486511262-c7a8c8b0b4f5?w=600&q=80",
];

function daysAgo(n: number) {
  const d = new Date();
  d.setDate(d.getDate() - n);
  return d.toISOString();
}

export const INSPECTIONS: Inspection[] = Array.from({ length: 48 }).map((_, i) => {
  const seed = i * 17 + 3;
  const rules = buildRuleChecks(seed);
  const score = scoreFromRules(rules);
  const product = pick(PRODUCTS);
  return {
    scanId: `MA-2026-${pad(4821 + i)}`,
    product: product.name,
    category: product.category,
    manufacturer: pick(MANUFACTURERS),
    result: resultFromScore(score),
    score,
    officer: pick(OFFICER_NAMES),
    region: pick(REGIONS),
    location: `${pick(REGIONS)} Market Inspection Zone ${int(1, 6)}`,
    date: daysAgo(int(0, 45)),
    image: IMAGES[i % IMAGES.length],
    extracted: buildExtractedFields(seed),
    rules,
  };
});

export const OFFICERS: Officer[] = OFFICER_NAMES.map((name, i) => ({
  id: `OFC-${pad(101 + i)}`,
  name,
  role: (["Inspector", "Inspector", "Inspector", "Supervisor", "Administrator"] as const)[i % 5],
  department: pick(["Legal Metrology Division", "Consumer Affairs Cell", "Field Enforcement Unit"]),
  region: pick(REGIONS),
  status: i === 6 ? "Inactive" : "Active",
  lastActive: daysAgo(int(0, 6)),
  avatarColor: pick(["#2563eb", "#7c3aed", "#06b6d4", "#16a34a", "#d97706"]),
}));

function hash(seed: string) {
  let h = 0;
  for (let i = 0; i < seed.length; i++) h = (h * 31 + seed.charCodeAt(i)) >>> 0;
  return h.toString(16).padStart(8, "0");
}

export function buildAuditTrail(scanId: string, officer: string, date: string): AuditEvent[] {
  const steps = [
    "Inspector Login",
    "Image Uploaded",
    "OCR Completed",
    "Rules Evaluated",
    "Issue Detected",
    "Inspector Decision",
    "Report Generated",
  ];
  let prev = "0".repeat(8);
  return steps.map((action, i) => {
    const current = hash(`${scanId}-${action}-${i}`);
    const evt: AuditEvent = {
      eventId: `EVT-${pad(i + 1)}`,
      scanId,
      inspectorId: officer,
      timestamp: date,
      action,
      device: pick(["Android · Field Tablet", "Windows · Desk Terminal", "iOS · Field Phone"]),
      ip: `10.${int(0, 255)}.${int(0, 255)}.${int(1, 254)}`,
      prevHash: prev,
      currentHash: current,
    };
    prev = current;
    return evt;
  });
}

export const CURRENT_OFFICER = {
  id: "OFC-101",
  name: "Anjali Sharma",
  role: "Inspector" as const,
  region: "Dehradun",
};
