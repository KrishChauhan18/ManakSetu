# AUDIT_REPORT.md — MANAK SETU / ComplyErg Technical Audit

**Date:** 2026-09-14  
**Auditor:** Lead System Architect & QA Lead  
**Repository:** SIH_CodePulse_034 (MANAK SETU / ComplyErg / METRAEGIS)

---

## 1. Executive Summary
This audit inspects the current runtime state, service configuration, pipeline modules, database bindings, OCR engines, API contracts, and test suites. Mismatches and gaps between the desired architecture and existing codebase have been cataloged with concrete remediation steps.

---

## 2. Actual Services and Ports

| Service | Target Port | Status in Codebase | Notes |
|---|---|---|---|
| **FastAPI Backend** | 8000 | Active (`app.main:app`) | Primary backend mounted on 8000. Text comments in `START_ALL.bat` referenced port 8001. |
| **React / Vite Frontend** | 5173 | Active (`frontend/`) | Proxies `/api` and `/storage` to `http://127.0.0.1:8000`. |
| **PostgreSQL Database** | 5432 | Configured in `docker-compose.yml` | Docker is not running in host environment; SQLAlchemy fallback to SQLite (`sqlite:///./storage/complyerg.db`) is actively functional. |
| **Streamlit Portal** | 8501 | Active (`streamlit_app/Home.py`) | Auxiliary inspection & executive demo portal. |

---

## 3. Actual Route List & API Base URL

- **Authoritative API Base URL:** `http://localhost:8000/api/v1`
- **Route Inventory:**
  - `POST /api/v1/auth/login`, `POST /api/v1/auth/register`, `GET /api/v1/auth/me`
  - `POST /api/v1/scan/upload` (and `/api/v1/scan/` upload handler)
  - `GET /api/v1/scan/` (list scans with pagination)
  - `GET /api/v1/scan/{scan_id}` (get detailed scan record)
  - `GET /api/v1/scan/{scan_id}/image` (retrieve raw or annotated label image)
  - `PATCH /api/v1/scan/{scan_id}/override` (inspector/supervisor field override)
  - `GET /api/v1/scan/{scan_id}/status-stream` (WebSocket progress stream)
  - `GET /api/v1/reports/{scan_id}/pdf` (ReportLab statutory evidence PDF)
  - `GET /api/v1/reports/{scan_id}/json`
  - `GET /api/v1/reports/{scan_id}/csv`
  - `GET /api/v1/rules/`, `POST /api/v1/rules/`, `PATCH /api/v1/rules/{rule_id}`, `DELETE /api/v1/rules/{rule_id}`
  - `GET /api/v1/users/`, `POST /api/v1/users/`, `PATCH /api/v1/users/{user_id}`
  - `GET /api/v1/audit/` (immutable audit trail)
  - `GET /api/v1/dashboard/stats`, `GET /api/v1/dashboard/trend`
  - `GET /api/v1/health` (system health check)
  - `GET /api/v1/diagnostics` (needs implementation for multi-tier OCR & system inspection)

---

## 4. Actual Database & Storage Backend

- **Database:**
  - Configured: `postgresql+psycopg2://complyerg_admin:...@localhost:5432/complyerg_db`
  - Active: SQLite fallback at `storage/complyerg.db` when Docker PostgreSQL is unreachable.
  - Health check: SQLAlchemy 2.0-compliant `SELECT 1` execution.
- **Storage:**
  - `LocalStorageBackend` implemented in `app/core/storage_backend.py`.
  - Storage path structure: `storage/images`, `storage/reports`.
  - Required enhancement: Standardize into `storage/uploads/`, `storage/processed/`, `storage/annotated/`, `storage/reports/`, `storage/temp/`, enforce strict path traversal guards, and store relative storage keys in DB.

---

## 5. Actual OCR Engines Availability & Status

| OCR Engine | Enabled Flag | Actual Status in Environment | Notes |
|---|---|---|---|
| **Google Cloud Vision** | `GOOGLE_VISION_ENABLED=false` | Module not installed | Tier 1 primary engine when credentials configured; gracefully handles missing package/credentials. |
| **PaddleOCR** | `PADDLEOCR_ENABLED=true` | Module not installed | Tier 2 local fallback; gracefully defers to Tesseract when package is missing. |
| **Tesseract OCR** | `TESSERACT_ENABLED=true` | Binary **installed** at `C:\Program Files\Tesseract-OCR\tesseract.exe` | 42 languages/scripts present (including `eng`, `hin`, `script/Devanagari`). Python wrapper `pytesseract` needs to be linked in `ocr_env`. |

---

## 6. Discovered Inconsistencies & Mismatches

1. **OCR Architecture Missing Dedicated Package:**
   - Multi-tier OCR cascade (`google_vision` -> `paddleocr` -> `tesseract`) was partially sketched in loose files rather than a clean modular `app/pipeline/ocr/` package.
2. **Field Extractor Field Naming:**
   - `field_extractor.py` was returning keys like `manufacturer` while test suite and rules expected `manufacturer_name` / `manufacturer`. Also missing standardized output schema (`value`, `normalized`, `confidence`, `bbox`, `source_text`, `source_engine`, `human_verified`).
3. **Rule Engine Tuple Return Order:**
   - In `rule_engine.py`, `evaluate_rules()` returned `(compliance_pct, violations)` in class method, but `(violations, compliance_pct)` in wrapper. Tests expecting `comp_pct, violations = rule_engine.evaluate_rules(label_record, seed_rules)` threw unpack errors.
4. **Test Suite Envelope Mismatches:**
   - Tests in `tests/test_api.py` called un-prefixed `/rules/` and `/dashboard/stats` expecting raw lists/dicts instead of the standardized envelope `{"success": true, "data": ...}`.
5. **START_ALL.bat References to 8001:**
   - Banner and echo text in `START_ALL.bat` referenced port 8001 as "ComplyErg Engine", confusing users and violating single-backend rule.
6. **Bcrypt 72-Byte Warning:**
   - Passwords exceeding 72 bytes triggered bcrypt CryptContext logs; requires safe truncation to 72 bytes before hash/verify.
7. **Frontend Axios Client:**
   - `frontend/src/api/client.ts` was an empty file; needs standard Axios client with baseURL from `VITE_API_BASE_URL` and token handling.
8. **PDF ReportLab Image & Unicode Safety:**
   - `reporter.py` embedded raw image paths directly without converting to RGB via Pillow first (which can break ReportLab on CMYK/RGBA PNGs), and lacked regional font fallback warning.

---

## 7. Action Plan for Repair
1. Implement `app/pipeline/ocr/` cascade with `google_vision_engine`, `paddleocr_engine`, `tesseract_engine`, `orchestrator`, and `diagnostics`.
2. Standardize `app/pipeline/field_extractor.py` and `rule_engine.py` with consistent schemas and robust backward compatibility.
3. Add `GET /api/v1/diagnostics` and update `GET /api/v1/health` with comprehensive engine checks.
4. Refactor `app/core/storage_backend.py` with path traversal security and canonical subdirectories.
5. Populate `frontend/src/api/client.ts` and ensure clean Vite proxy routing.
6. Clean up `START_ALL.bat` to eliminate port 8001 references.
7. Fix test assertions and run full `pytest -q` and `npm run build`.
