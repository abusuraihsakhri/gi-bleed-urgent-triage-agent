# Gi Bleed Urgent Triage Agent

> **Domain:** Gastroenterology, Hepatology & Clinical Nutrition  
> **Reference Guidelines & Standards:** `AASLD & ACG Clinical Practice Guidelines`

<div align="center">

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-3776AB.svg?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688.svg?logo=fastapi&logoColor=white)
![Audit Trail](https://img.shields.io/badge/Audit-HMAC--SHA256_Tamper--Evident-brightgreen.svg)
![Zero-PHI Guard](https://img.shields.io/badge/Guard-Zero--PHI_Outbound-blue.svg)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg?logo=docker&logoColor=white)

</div>

---

## 📖 What It Does

**Gi Bleed Urgent Triage Agent** is an advanced analytical and computational platform implementing Glasgow-Blatchford, Rockall & Oakland GI Bleeding Stager.

---

## ⚙️ Key Capabilities & Algorithmic Modules

### 🔬 Analytical Functions

- **`calculate_gbs()`**: Calculate Glasgow-Blatchford Score for upper GI bleed risk stratification.

Parameters:
    bun_mmol_l: Blood urea nitrogen in mmol/L
    hemoglobin_g_dl: Hemoglobin in g/dL
    sex: 'male' or 'female' (affects hemoglobin scoring)
    sbp_mmhg: Systolic blood pressure in mmHg
    heart_rate: Heart rate in bpm
    melena: Presence of melena (black tarry stool)
    syncope: History of syncope
    hepatic_disease: History of liver disease
    cardiac_failure: History of cardiac failure

Returns:
    Dict with total score, component breakdown, risk category, and recommendation.
- **`calculate_rockall()`**: Calculate Rockall Score for upper GI bleeding (pre- and post-endoscopy).

Parameters:
    age: Patient age in years
    shock_hr: Heart rate in bpm (for shock assessment)
    shock_sbp: Systolic blood pressure in mmHg (for shock assessment)
    comorbidity: 'none', 'cardiac' (CHF/IHD), or 'major' (renal/liver failure, disseminated malignancy)
    endoscopic_diagnosis: 'none'/'mallory-weiss', 'peptic_ulcer'/'esd', or 'cancer'
    major_stigmata: 'none'/'dark_spot', or 'blood'/'visible_vessel'/'active_bleeding'

Returns:
    Dict with clinical score, endoscopic score, total score, mortality risk.
- **`calculate_aims65()`**: Calculate AIMS65 score for in-hospital mortality in upper GI bleeding.

Parameters:
    albumin_g_dl: Serum albumin in g/dL
    inr: International normalized ratio
    mental_status_altered: Altered mental status (GCS <14 or disoriented)
    sbp_mmhg: Systolic blood pressure in mmHg
    age: Patient age in years

Returns:
    Dict with total score (0-5), mortality risk, and component breakdown.
- **`triage_gi_bleed()`**: Perform comprehensive GI bleed triage using all three scoring systems.
- **`main()`** — calculates and validates main parameters.

---

## 📐 Mathematical Formulation & Logic

```text
  Calculate Glasgow-Blatchford Score for upper GI bleed risk stratification.
  risk = "Very Low"
  risk = "Low"
  risk = "Moderate"
  risk = "High"
```

---

## 💻 CLI Quickstart & Usage

### 1. Guided Interactive Mode
```bash
python cli.py
```

### 2. Direct Parameterized Evaluation
```bash
python cli.py --input data.csv
```

### Parameter Reference
- `--interactive`: Launch guided terminal interactive wizard.
- `--input <path>`: Evaluate input from JSON or CSV specification.
- `--json`: Output deterministic structured results in JSON format.

### Input Data Schema

| Field | Description | Requirement |
|:------|:------------|:------------|
| `case_id` | Parameter / observation metric | Required |
| `patient_synthetic_id` | Parameter / observation metric | Required |
| `metric_primary` | Parameter / observation metric | Required |
| `metric_secondary` | Parameter / observation metric | Required |
| `is_stat` | Parameter / observation metric | Required |
| `status_flag` | Parameter / observation metric | Required |

---

## 🛡️ Security & Enterprise Architecture

* **Zero-PHI Outbound Interceptor:** Active AST and regex inspection blocking SSNs, MRNs, phone numbers, and patient identifiers.
* **Tamper-Evident HMAC-SHA256 Audit Trail:** Chained, cryptographically signed logs for every evaluation and state transition.
* **Air-Gapped LLM Reasoning Adapter:** Agnostic integration for local Ollama instances (`llama3`, `mistral`), Claude 3.5 Sonnet, GPT-4o, and deterministic test mocks.
* **Active Learning Bayesian Calibration:** Dynamic tracker updating worker reliability weights and monitoring Brier calibration drift.
* **FastAPI & Prometheus Telemetry:** Exposes OpenAPI 3.1 REST endpoints and operational Prometheus metrics (`/metrics`).

---

## 🧪 Testing & Verification

Run the automated test suite:

```bash
pytest -v
```

Execute high-throughput batch simulation benchmarks:

```bash
python simulator.py --tasks 1000 --concurrency 8
```

---

## 🐳 Container Deployment

```bash
docker build -t gi-bleed-urgent-triage-agent .
docker run -p 8000:8000 gi-bleed-urgent-triage-agent
```
