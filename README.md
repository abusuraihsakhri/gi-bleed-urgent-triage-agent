# Gi Bleed Urgent Triage Agent

> **Domain:** Gastroenterology, Hepatology & Clinical Nutrition
> **Reference Guidelines:** AASLD & ACG Clinical Practice Guidelines

<div align="center">

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-3776AB.svg?logo=python&logoColor=white)
![Audit Trail](https://img.shields.io/badge/Audit-HMAC--SHA256_Tamper--Evident-brightgreen.svg)
![Zero-PHI Guard](https://img.shields.io/badge/Guard-Zero--PHI_Outbound-blue.svg)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg?logo=docker&logoColor=white)

</div>

---

## What It Does

**Gi Bleed Urgent Triage Agent** is a clinical decision support tool implementing three validated scoring systems for upper GI bleeding risk stratification:

1. **Glasgow-Blatchford Score (GBS)** - Pre-endoscopy risk stratification
2. **Rockall Score** - Post-endoscopy mortality/rebleeding risk
3. **AIMS65 Score** - In-hospital mortality prediction

All formulas are based on published clinical literature. Zero external dependencies for core scoring.

### References

- Blatchford O, et al. Lancet 2000;356:1318-21
- Rockall TA, et al. Gut 1996;38:316-21
- Saltzman JR, et al. Am J Gastroenterol 2015;110:18-33 (AIMS65)

---

## Installation

```bash
# Clone the repository
git clone https://github.com/abusuraihsakhri/gi-bleed-urgent-triage-agent.git
cd gi-bleed-urgent-triage-agent

# No external dependencies required for core scoring
# Optional: Install development dependencies
pip install pytest
```

---

## Usage

### Command Line Interface

```bash
# Glasgow-Blatchford Score
python cli.py gbs --bun 10.0 --hemoglobin 9.5 --sbp 95 --melena

# Rockall Score
python cli.py rockall --age 70 --sbp 85 --comorbidity cardiac

# AIMS65 Score
python cli.py aims65 --albumin 2.5 --inr 2.0 --age 70

# Comprehensive triage (all scores)
python cli.py triage --bun 12.0 --hemoglobin 9.0 --sbp 95 --age 70

# Batch processing from CSV
python cli.py batch -i sample.csv -o results.csv --score triage
```

### Python API

```python
from gibleed_sentinel import calculate_gbs, calculate_rockall, calculate_aims65, triage_gi_bleed

# Calculate GBS
result = calculate_gbs(bun_mmol_l=10.0, hemoglobin_g_dl=9.5, sbp_mmhg=95, melena=True)
print(result["total_score"], result["risk_category"])

# Comprehensive triage
triage = triage_gi_bleed(bun_mmol_l=12.0, hemoglobin_g_dl=9.0, sbp_mmhg=95, age=70)
print(triage["overall_urgency"])
```

---

## Input Validation

All scoring functions validate inputs against clinically plausible ranges:

| Parameter | Range | Unit |
|-----------|-------|------|
| BUN | 0 - 100 | mmol/L |
| Hemoglobin | 0 - 25 | g/dL |
| Systolic BP | 0 - 300 | mmHg |
| Heart Rate | 0 - 300 | bpm |
| Albumin | 0 - 10 | g/dL |
| INR | 0 - 20 | - |
| Age | 0 - 150 | years |

---

## Security Features

### Zero-PHI Outbound Interceptor
Active regex inspection blocking SSNs, MRNs, phone numbers, and patient identifiers from outbound data.

### Tamper-Evident HMAC-SHA256 Audit Trail
Chained, cryptographically signed logs for every evaluation and state transition.

**Important:** Set `AUDIT_SECRET_KEY` environment variable in production for audit chain continuity:

```bash
# Generate a secure key
python -c "import secrets; print(secrets.token_hex(32))"

# Set it in your environment
export AUDIT_SECRET_KEY="your-generated-key"
```

---

## Testing

```bash
# Run the full test suite
pytest -v

# Run specific test files
pytest test_gibleed_sentinel.py -v
pytest tests/test_gi_bleed_urgent_triage_agent.py -v
pytest tests/test_enrichment.py -v
```

---

## Docker Deployment

```bash
# Build and run with Docker Compose
export AUDIT_SECRET_KEY="$(python -c 'import secrets; print(secrets.token_hex(32))')"
docker-compose up --build

# Or build and run manually
docker build -t gi-bleed-urgent-triage-agent .
docker run -p 8000:8000 -e AUDIT_SECRET_KEY="your-secret-key" gi-bleed-urgent-triage-agent
```

---

## Project Structure

```
gi-bleed-urgent-triage-agent/
├── cli.py                          # CLI entry point (gbs, rockall, aims65, triage, batch)
├── gibleed_sentinel.py             # Core scoring engine with validation
├── gi_bleed_urgent_triage_agent_app.py  # Alternative app entry
├── gibleed_sentinel_app.py         # Sentinel app entry
├── enrichment.py                   # Enrichment feature modules
├── simulator.py                    # High-throughput simulation benchmark
├── agents/                         # Enterprise agent framework
│   ├── base.py                     # Security, PHI guard, audit trail
│   ├── models.py                   # Pydantic schemas
│   ├── supervisor.py               # Multi-worker orchestrator
│   ├── workers.py                  # Specialized domain workers
│   ├── api.py                      # FastAPI REST server
│   ├── metrics.py                  # Prometheus metrics
│   ├── llm_factory.py              # LLM integration (mock/local/remote)
│   ├── learning.py                 # Active learning engine
│   └── streamer.py                 # WebSocket telemetry
├── gi_bleed_urgent_triage_agent/   # Pro package variant
│   ├── cli.py                      # Pro CLI (audit, chat, batch, serve)
│   ├── agents.py                   # Agent hierarchy
│   ├── engine.py                   # Clinical algorithmic engine
│   ├── models.py                   # Clinical data models
│   └── server.py                   # FastAPI server factory
├── tests/                          # Test suites
│   ├── test_gi_bleed_urgent_triage_agent.py
│   └── test_enrichment.py
├── test_gibleed_sentinel.py        # Core scoring tests
├── web/index.html                  # Operations console UI
├── sample.csv                      # Sample batch input
├── sample_payload.json             # Sample API payload
├── benchmark_dataset.json          # Golden benchmark test suite
├── Dockerfile                      # Container build
├── docker-compose.yml              # Container orchestration
└── pyproject.toml                  # Project configuration
```

---

## License

MIT License - see [LICENSE](LICENSE) for details.

---

**Author:** Dr. Abu Suraih Sakhri
