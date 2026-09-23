# 🇮🇳 Manak Setu

### AI-Powered Legal Metrology Label Compliance & Risk Intelligence Platform

> **Manak Setu** bridges product-label inspection and regulatory compliance by transforming a simple package photograph into an explainable, auditable Legal Metrology compliance report.

**Manak Setu** is an offline-capable, production-oriented compliance scanning system designed for the **Legal Metrology (Packaged Commodities) Rules, 2011**.

The platform combines **OCR, machine learning, deterministic rule evaluation, role-based access control, audit logging, and risk analytics** to help inspectors identify missing or potentially non-compliant mandatory declarations on packaged commodities.

---

## ✨ Why Manak Setu?

Traditional label verification can involve manually inspecting multiple declarations across thousands of packaged products.

**Manak Setu automates the first layer of this process:**

📸 **Capture** → 🔍 **Extract** → ⚖️ **Validate** → 🚨 **Identify Violations** → 📊 **Prioritize Risk** → 📄 **Generate Report**

The system is designed around one important principle:

> **AI assists the inspection process; deterministic legal rules produce the compliance verdict.**

This keeps the legal decision-making process **transparent, explainable, and auditable**.

---

# 🎯 Core Objectives

Manak Setu focuses specifically on **mandatory declaration verification** under the applicable provisions of the **Legal Metrology (Packaged Commodities) Rules, 2011**, particularly:

* **Rule 6**
* **Rule 7**
* **Rule 9**
* **Rule 10**

### 🔎 Mandatory declarations checked

| Declaration               | Verification    |
| ------------------------- | --------------- |
| Manufacturer / Packer     | ✅               |
| Net Quantity              | ✅               |
| MRP                       | ✅               |
| Manufacturing Date        | ✅               |
| Expiry / Best Before Date | ✅               |
| Consumer Care Details     | ✅               |
| Batch / Lot Number        | ✅               |
| FSSAI License             | ✅               |
| Country of Origin         | ✅               |
| Ingredients Declaration   | ✅ Presence only |

### ⚠️ Important Scope Limitation

Manak Setu **does not evaluate the correctness of ingredient contents, nutritional values, health claims, or ingredient quality**.

For ingredients, the system only records whether a declaration is present:

```json
{
  "ingredients_declared": {
    "present": true,
    "confidence": 0.94,
    "bbox": [120, 430, 560, 510]
  }
}
```

---

# 🧠 AI + Deterministic Compliance Architecture

Manak Setu deliberately separates **machine learning** from the final legal decision.

### Machine Learning handles:

* 📷 Image quality assessment
* 🔤 OCR assistance
* 🏷️ Field classification
* 📍 Field localization
* 🎯 Inspection-risk prioritization

### Rule Engine handles:

* ⚖️ Legal validation
* 🚨 Violation detection
* 📋 Compliance verdict generation
* 📝 Explainable violation reasons

The compliance engine evaluates extracted information against **versioned legal rule specifications**.

```text
                    ┌──────────────────┐
                    │  Product Label   │
                    │      Image       │
                    └────────┬─────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │ Image Quality    │
                    │     Model        │
                    └────────┬─────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │ Preprocessing    │
                    │ + OCR            │
                    └────────┬─────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │ Field Extraction │
                    │ & Classification │
                    └────────┬─────────┘
                             │
                             ▼
              ┌──────────────────────────────┐
              │     Deterministic Rule       │
              │          Engine               │
              │                               │
              │ legal_metrology_2011.json     │
              └──────────────┬───────────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │ Compliance       │
                    │ Verdict          │
                    └────────┬─────────┘
                             │
                ┌────────────┴────────────┐
                ▼                         ▼
        ┌───────────────┐        ┌────────────────┐
        │ Audit Trail   │        │ Risk Analytics │
        └───────────────┘        └────────────────┘
```

---

# ⚖️ Deterministic Legal Verdicts

The **Rule Engine** is the core compliance component of Manak Setu.

Instead of allowing an ML model to decide whether a label is legally compliant, the system evaluates extracted fields against a version-controlled rule specification:

```text
Extracted Field
      ↓
Normalized Value
      ↓
Legal Rule Evaluation
      ↓
Pass / Violation / Review
      ↓
Explainable Reason
```

This makes every verdict traceable to:

* The extracted declaration
* The applicable rule
* The validation performed
* The resulting violation
* The evidence used for the decision

### Example

```text
❌ NON-COMPLIANT

Field:
Maximum Retail Price

Reason:
Required declaration could not be identified.

Rule:
Applicable Legal Metrology declaration requirement

Evidence:
OCR + field detection result

Status:
Violation
```

---

# 🔐 Role-Based Access Control

Manak Setu implements a **three-tier RBAC architecture**.

| Role                 | Capabilities                                                   |
| -------------------- | -------------------------------------------------------------- |
| 👮 **Inspector**     | Scan labels, view own scans, export own reports                |
| 🧑‍💼 **Supervisor** | Team/region scans, field overrides, dashboards, audit logs     |
| 🛡️ **Admin**        | Global access, rule management, user management, scan deletion |

## 👮 Inspector

Inspectors can:

* Upload or capture product-label images
* Run compliance scans
* View their own scan history
* Inspect detected fields
* View compliance results
* Export PDF / CSV / JSON reports

Database queries are strictly scoped using:

```text
user_id
```

---

## 🧑‍💼 Supervisor

Supervisors can:

* View team/region scans
* Review extracted fields
* Override incorrect field values
* Provide mandatory override reasons
* View team dashboards
* Inspect audit logs

Every manual override creates an audit record.

```text
Field Override
      ↓
Mandatory Reason
      ↓
Database Transaction
      ↓
Updated Field + AuditLog
```

---

## 🛡️ Administrator

Administrators have system-wide access to:

* All scans
* All users
* Rule specifications
* Audit logs
* Global dashboards
* User roles
* Scan deletion
* Legal rule management

---

# 🧾 Atomic Audit Logging

Auditability is a first-class feature of Manak Setu.

The following operations generate audit records:

* Field overrides
* Scan deletion
* Legal rule modification
* User role changes

The application performs the business operation and audit logging within the **same database transaction**.

```text
┌───────────────────────────┐
│      Database Transaction │
│                           │
│  1. Perform Operation     │
│  2. Create AuditLog       │
│  3. Commit Transaction    │
│                           │
└───────────────────────────┘
```

If the transaction fails, the associated audit operation does not silently disappear.

---

# 🤖 Machine Learning Pipeline

Manak Setu contains three ML components.

## 1️⃣ Image Quality Classifier

**Architecture:** Random Forest

Evaluates image characteristics such as:

* Blur
* Glare
* Skew
* Image quality features

Purpose:

> Determine whether the uploaded label image is suitable for reliable downstream processing.

---

## 2️⃣ Field Type Classifier

**Architecture:** TF-IDF + Custom Feature Extractor + Logistic Regression

Classifies extracted OCR text into fields such as:

```text
MRP
Net Quantity
Batch Number
Manufacturer
Consumer Care
Manufacturing Date
Expiry Date
Country of Origin
FSSAI
Ingredients
```

---

## 3️⃣ Priority Risk Scorer

**Architecture:** XGBoost

Generates an inspection-priority risk score based on available scan and compliance-related features.

The risk model is used for:

> **Prioritization and analytics — not the final legal verdict.**

---

# 📊 Model Performance

| Model                 | Architecture               |   Metric | Performance |
| --------------------- | -------------------------- | -------: | ----------: |
| Quality Classifier    | Random Forest              | Accuracy |      >95.0% |
| Field Type Classifier | TF-IDF + Feature Extractor | F1-Score |      >92.0% |
| Priority Risk Scorer  | XGBoost                    |  ROC-AUC |       0.885 |

> **Note:** These figures should be interpreted in the context of the dataset, split strategy, class distribution, and evaluation methodology used during training.

---

# 🏗️ Project Architecture

```text
Manak Setu
│
├── app/
│   ├── main.py
│   │
│   ├── api/
│   │   ├── auth
│   │   ├── scans
│   │   ├── rules
│   │   ├── users
│   │   ├── audit
│   │   ├── reports
│   │   └── dashboard
│   │
│   ├── pipeline/
│   │   ├── preprocess
│   │   ├── quality_check
│   │   ├── ocr_engine
│   │   ├── field_extractor
│   │   ├── rule_engine
│   │   └── risk_model
│   │
│   ├── models/
│   │   ├── user
│   │   ├── scan
│   │   ├── rule
│   │   ├── violation
│   │   ├── audit_log
│   │   └── report
│   │
│   ├── schemas/
│   ├── core/
│   ├── rules_data/
│   │   └── legal_metrology_2011.json
│   │
│   └── db/
│
├── ml/
│   ├── data/
│   ├── train_quality_model.py
│   ├── train_field_classifier.py
│   ├── train_risk_model.py
│   ├── evaluate.py
│   └── saved_models/
│
├── streamlit_app/
│   ├── Home.py
│   └── pages/
│       ├── 1_Scan_Product.py
│       ├── 2_Scan_Result.py
│       ├── 3_Scan_History.py
│       ├── 4_Rules_Admin.py
│       ├── 5_User_Management.py
│       ├── 6_Dashboard.py
│       └── 7_Audit_Log.py
│
├── storage/
├── tests/
├── docker-compose.yml
├── requirements.txt
└── README.md
```

---

# 🖥️ Application Modules

### 📸 1. Scan Product

Upload or capture a product label and initiate an automated compliance scan.

### 🔍 2. Scan Result

Provides:

* Extracted declarations
* OCR confidence
* Bounding boxes
* Compliance status
* Detected violations
* Supervisor override interface

### 🗂️ 3. Scan History

Role-aware scan history with:

* Inspector-level filtering
* Team-level access
* Administrative deletion

### ⚖️ 4. Rule Administration

Administrators can manage versioned legal rules and validation specifications.

### 👥 5. User Management

Administrators can:

* Create users
* Assign roles
* Manage access

### 📊 6. Executive Dashboard

Provides analytics including:

* Compliance trends
* Violation distribution
* Scan statistics
* Risk-priority rankings
* Model insights

### 🧾 7. Audit Log

Provides a read-only history of important system actions.

---

# 🔑 Seed Accounts

For development/demo environments, the database is initialized with the following accounts:

| Role             | Email                         | Default Password |
| ---------------- | ----------------------------- | ---------------- |
| 🛡️ Admin        | `admin@complyerg.gov.in`      | `Admin@123`      |
| 🧑‍💼 Supervisor | `supervisor@complyerg.gov.in` | `Supervisor@123` |
| 👮 Inspector     | `inspector@complyerg.gov.in`  | `Inspector@123`  |

> ⚠️ **Security:** These are development/demo credentials. Change or disable default passwords before any real deployment.

---

# ⚡ Quick Start

## 1. Clone the repository

```bash
git clone <YOUR_REPOSITORY_URL>
cd SIH_CodePulse_034
```

## 2. Create a virtual environment

```bash
python -m venv ocr_env
```

### Windows

```bash
ocr_env\Scripts\activate
```

### Linux / macOS

```bash
source ocr_env/bin/activate
```

---

## 3. Install dependencies

```bash
pip install -r requirements.txt
```

---

## 4. Initialize the database

```bash
python -c "from app.db.init_db import init_db; init_db()"
```

This initializes:

* Database tables
* Seed users
* Legal rule specifications
* Initial application configuration

---

# 🚀 Run Manak Setu

## Terminal 1 — FastAPI Backend

```bash
uvicorn app.main:app --reload --port 8000
```

API:

```text
http://localhost:8000
```

Interactive API documentation:

```text
http://localhost:8000/docs
```

---

## Terminal 2 — Streamlit Portal

```bash
streamlit run streamlit_app/Home.py
```

Application:

```text
http://localhost:8501
```

---

# 🧪 Testing

Run the complete automated test suite:

```bash
python -m pytest tests/ -v
```

The test suite includes:

* Unit tests
* Rule-engine tests
* Authentication tests
* RBAC tests
* Permission-denied scenarios
* Audit logging tests

Example:

```text
Inspector → Own Scan       ✅
Inspector → Other User     ❌ 403
Supervisor → Team Scan     ✅
Admin → Global Scan        ✅
```

---

# 🗄️ Database

### Development

```text
SQLite
sqlite:///./storage/complyerg.db
```

### Production

The repository includes Docker Compose configuration for PostgreSQL.

```text
Application
     │
     ▼
FastAPI
     │
     ▼
PostgreSQL
     │
 ┌───┴──────────────┐
 ▼                  ▼
Scans            Audit Logs
```

---

# 🔒 Security Design

Manak Setu incorporates multiple security controls:

* JWT-based authentication
* Role-based authorization
* User-scoped database queries
* Supervisor-only field overrides
* Mandatory override reasons
* Atomic audit transactions
* Administrative access controls
* Protected API endpoints

The system follows a **least-privilege approach**, ensuring users only access resources permitted by their role.

---

# 📄 Compliance Reports

Manak Setu can generate structured reports containing:

### Scan Information

* Scan ID
* Timestamp
* Inspector
* Product information
* Image reference

### Extracted Declarations

* Field name
* Extracted value
* Confidence
* Bounding box

### Compliance Analysis

* Applicable rule
* Compliance status
* Violation reason
* Evidence

### Audit Information

* Manual overrides
* User performing override
* Override reason
* Timestamp

Supported formats:

```text
PDF
CSV
JSON
```

---

# 🔄 End-to-End Workflow

```text
        📸 Product Label
               │
               ▼
       Image Quality Check
               │
        ┌──────┴──────┐
        │             │
     Poor Image    Good Image
        │             │
        ▼             ▼
     Re-scan        OCR
                      │
                      ▼
              Field Extraction
                      │
                      ▼
             Field Classification
                      │
                      ▼
             Legal Rule Engine
                      │
             ┌────────┴────────┐
             ▼                 ▼
          Compliant         Violation
             │                 │
             └────────┬────────┘
                      ▼
              Risk Prioritization
                      │
                      ▼
              Audit Trail
                      │
                      ▼
             Compliance Report
```

---

# 🌟 Key Features at a Glance

| Capability                      | Manak Setu |
| ------------------------------- | :--------: |
| 📸 Label Image Scanning         |      ✅     |
| 🔤 OCR Extraction               |      ✅     |
| 🧠 ML-Assisted Classification   |      ✅     |
| ⚖️ Deterministic Legal Rules    |      ✅     |
| 📍 Bounding Box Localization    |      ✅     |
| 🔐 RBAC                         |      ✅     |
| 🧾 Atomic Audit Logging         |      ✅     |
| 📊 Risk Analytics               |      ✅     |
| 📄 PDF Reports                  |      ✅     |
| 📑 CSV / JSON Export            |      ✅     |
| 📴 Offline-Capable Architecture |      ✅     |
| 🧪 Automated Tests              |      ✅     |
| 🐘 PostgreSQL Support           |      ✅     |
| 🗂️ Versioned Legal Rules       |      ✅     |

---

# 🛡️ Design Philosophy

### **AI should assist — not replace — legal reasoning.**

Manak Setu therefore follows three architectural principles:

### 1. Explainability

Every compliance result should be traceable to a specific extracted declaration and rule evaluation.

### 2. Determinism

The same normalized input and rule version should produce the same legal evaluation.

### 3. Accountability

Important human actions such as overrides, rule changes, and deletions are recorded in an auditable trail.

---

# 🇮🇳 Vision

**Manak Setu** aims to create a digital bridge between **technology, field inspection, and regulatory compliance**.

By combining computer vision, OCR, machine learning, deterministic legal rules, and secure audit infrastructure, the platform provides a structured approach to large-scale packaged-commodity label verification.

> **Scan. Verify. Explain. Audit.**

### 🇮🇳 Manak Setu

**A digital bridge for transparent and technology-assisted compliance.**

---

## 📌 Technology Stack

```text
Backend        → FastAPI
Frontend       → Streamlit
Database       → SQLite / PostgreSQL
ORM            → SQLAlchemy
Validation     → Pydantic
Authentication → JWT
OCR            → OCR Engine
ML             → Scikit-learn / XGBoost
Data Processing→ NumPy / Pandas
Testing        → Pytest
Deployment     → Docker
Reports        → PDF / CSV / JSON
```

---

## 📜 Project Status

**Manak Setu v2**

Production-oriented prototype for automated Legal Metrology packaged-commodity label compliance.

> Built for intelligent inspection, explainable compliance, and accountable regulatory workflows.
