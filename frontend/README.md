# METRIAEGIS — AI-Assisted Packaged Commodity Compliance & Inspection Platform

Frontend-only Smart India Hackathon prototype. React + TypeScript + Tailwind CSS + React Router + Recharts + Lucide icons. All data is mocked — there is no real backend, OCR, or auth server.

## Run locally

```bash
npm install
npm run dev
```

Then open the printed local URL (usually http://localhost:5173).

## Build for production

```bash
npm run build
npm run preview
```

## Demo flow

1. **Login** — pick a role (Inspector / Supervisor / Administrator) and sign in with any credentials.
2. **Dashboard** — overview stats, trend charts, recent inspections.
3. **New Inspection** (sidebar) — upload/capture images, review image quality, click "Analyze Product".
4. **AI Analysis** — watch the OCR pipeline animate, review extracted fields (editable), continue.
5. **Compliance Analysis** — see the compliance score and rule-by-rule validation, view evidence.
6. **Inspector Verification** — confirm or override each AI finding (override requires a reason).
7. **Finalize Inspection** -> generates the **Inspection Report**, viewable/exportable (mocked).
8. Explore **Inspection History**, **Analytics**, **Rule Management**, **User Management**, and the
   **Audit Trail** (hash-linked, tamper-evident event log) from the sidebar.

## Project structure

```
src/
  components/   Reusable UI (StatCard, RuleCard, Sidebar, Navbar, Modal, charts, etc.)
  pages/        The 13 route-level pages
  layouts/      AppLayout (sidebar + navbar shell)
  data/         Mock data generators (products, manufacturers, rules, officers, audit events)
  hooks/        Auth context, toast notifications, inspection-flow state
  types/        Shared TypeScript types
  utils/        Formatting + styling helpers
```

## Notes

- All manufacturers and figures are fictional; no real brands are referenced.
- The audit trail is explicitly described as a "hash-linked tamper-evident audit trail," not a blockchain.
- AI findings are always labeled "Potential Issue" / "Review Required" and require inspector verification before a report is finalized.
