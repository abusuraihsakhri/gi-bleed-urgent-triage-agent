# GI Bleed Urgent Triage Agent

Deterministic calculators for **Glasgow–Blatchford (GBS)**, **AIMS65**, and **Rockall** scores in upper gastrointestinal bleeding. Includes a local command-line application, a stateless clinical-score HTTP API, and an offline-capable static browser application for GBS and AIMS65.

**Clinical scope:** Educational clinical decision support, not a medical device or an autonomous triage system. Scores do **not** diagnose bleeding, mandate intensive care or endoscopy, or independently authorize discharge. Suspected active bleeding, instability, and clinical red flags require immediate clinical assessment.

## Features

- **GBS (0–23):** pre-endoscopic scoring from blood urea, hemoglobin, blood pressure, pulse, and four clinical features. A complete GBS of 0–1 meets the ACG *very-low-risk screening criterion*; this is not a discharge authorization.
- **AIMS65 (0–5):** prognostic score using albumin, INR, mental status, systolic pressure, and age **older than 65**. Does not assign uncalibrated mortality percentages.
- **Rockall (0–11):** incorporates clinical and endoscopic inputs. Unavailable values produce an incomplete score; no mortality percentage is extrapolated.
- **Combined CLI assessment:** displays all three scores and an **unvalidated** descriptive priority indicator, never a treatment protocol.
- **Browser app:** entirely client-side JavaScript, responsive design, explicit units, optional AIMS65, local JSON export, no remote code, analytics, or patient identifiers.
- **API and Docker:** stateless FastAPI endpoints with required structured observations and unknown fields rejected. The legacy generic multi-agent demonstration is not a validated bleeding-risk engine.

## Use in a browser

Open `web/index.html` directly, or serve the `web/` folder with any static web server:

```bash
python -m http.server --directory web 8080
```

Then open `http://localhost:8080`. A repository-root `index.html` redirects to `web/` for GitHub Pages deployments when Pages is configured to publish from the repository root.

All calculations occur inside the browser. Data are not sent to an endpoint, persisted in browser storage, or included in network requests. JSON export includes only numerical scores, component points, and interpretation text.

## Install and CLI

Python 3.10 or later is recommended:

```bash
python -m pip install -e ".[server,test]"
gi-bleed-urgent-triage-engine gbs --bun 4 --hemoglobin 15 --sex male --sbp 125 --heart-rate 78 --history-confirmed
gi-bleed-urgent-triage-engine aims65 --albumin 2.8 --inr 1.8 --sbp 110 --age 70 --mental-status-assessed
gi-bleed-urgent-triage-engine rockall --age 70 --hr 88 --sbp 105 --comorbidity none --diagnosis peptic_ulcer --stigmata none
```

The equivalent repository entry point is `python cli.py`. The flags `--history-confirmed` and `--mental-status-assessed` signify that negative findings have been **assessed**, not merely omitted. Without required clinical observations, score outputs are explicitly labeled indeterminate. All CLI commands print JSON.

Batch CSV mode is also available:

```bash
python cli.py batch -i patients.csv -o results.csv --score gbs
```

Input columns follow CLI parameter names without hyphens (e.g. `bun`, `hemoglobin`, `sbp`, `heart_rate`, `sex`, `history_confirmed`). Invalid nonempty numeric and boolean values cause errors rather than silent coercion. Batch processing is local, but source and result CSVs **may contain sensitive patient data**: protect them appropriately.

## HTTP API and Docker

```bash
uvicorn agents.clinical_api:app --host 127.0.0.1 --port 8000
# Or run docker compose up --build
```

Endpoints: `GET /health`; `POST /api/gbs`, `POST /api/aims65`, and `POST /api/rockall`. Interactive schema: `/docs`. All parameters of each selected score are required; requests containing unknown identifier fields are rejected. The API does not persist case data. Use TLS, authentication, monitoring, and appropriate data governance if exposed beyond a trusted local environment; **these infrastructure controls are not provided**.

The older `agents.api` and `gi_bleed_urgent_triage_agent` demonstration modules remain for compatibility. Their generic threshold logic does not implement validated GI-bleeding algorithms. The legacy audit endpoint is disabled unless `ENABLE_DEMO_AUDIT_API=1`, and reading its audit logs requires `AUDIT_LOG_READ_TOKEN`. `AUDIT_SECRET_KEY` is required for durable HMAC key continuity if using legacy in-memory audit facilities; these facilities are not a durable audit-log service.

## Development and verification

```bash
python -m pip install -e ".[server,test]"
python -m pytest -q
node --check web/app.js
node --test web/app.test.cjs
python -m compileall -q gibleed_sentinel.py agents gi_bleed_urgent_triage_agent
```

GitHub Actions executes Python tests on 3.10–3.13, package installation, CLI/API smoke tests, and Node-based browser score-boundary checks. Browser layout is intended for modern desktop and mobile browsers; this repository has not undergone clinical validation or production security certification.

## Evidence and limitations

- Blatchford O et al. *Lancet*. 2000;356:1318–1321 (GBS).
- Rockall TA et al. *Gut*. 1996;38:316–321 (Rockall).
- Saltzman JR et al. *Gastrointest Endosc*. 2011;74:1215–1224 (AIMS65). [PubMed](https://pubmed.ncbi.nlm.nih.gov/21907980/).
- Laine L et al. *Am J Gastroenterol*. 2021;116:899–917 (ACG upper GI bleeding guidance). [PubMed](https://pubmed.ncbi.nlm.nih.gov/33929377/).

**Interpretation:** ACG suggests that carefully selected patients with GBS 0–1 *may* be discharged with outpatient follow-up after clinical evaluation. Higher score cutoffs, the combined priority categories, and individual absolute mortality predictions are **not validated as automatic care pathways**. Rockall interpretation requires correct classification of endoscopic findings. AIMS65 predicts population-level prognosis, not individual disposition.

## License

MIT; see [LICENSE](LICENSE).
