# GI Bleed Urgent Triage Agent

> **Gastroenterology & Hepatology** — Upper GI Bleeding Risk Stratification

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
![Python](https://img.shields.io/badge/Python-3.10+-3776AB.svg)

---

## Overview

A clinical decision support tool implementing three validated scoring systems for upper gastrointestinal bleeding risk stratification:

1. **Glasgow-Blatchford Score (GBS)** — Pre-endoscopy risk stratification (0-23)
2. **Rockall Score** — Post-endoscopy mortality and rebleeding risk (0-11)
3. **AIMS65 Score** — In-hospital mortality prediction (0-5)

All formulas are based on published clinical literature. Zero external dependencies (Python stdlib only).

---

## Scoring Systems

### Glasgow-Blatchford Score (GBS)
Pre-endoscopy score to identify patients safe for outpatient management.

| Component | Scoring |
|-----------|---------|
| BUN (mmol/L) | 6.5-7.9: 2, 8.0-9.9: 3, 10.0-24.9: 4, ≥25: 6 |
| Hemoglobin (g/dL) Male | 12-12.9: 1, 10-11.9: 3, <10: 6 |
| Hemoglobin (g/dL) Female | 10-11.9: 1, <10: 6 |
| SBP (mmHg) | 100-109: 1, 90-99: 2, <90: 3 |
| HR ≥100 | 1 |
| Melena | 1 |
| Syncope | 2 |
| Hepatic disease | 2 |
| Cardiac failure | 2 |

- **Score 0**: Very low risk — safe for outpatient management
- **Score 1-3**: Low risk
- **Score 4-5**: Moderate risk — inpatient monitoring
- **Score ≥6**: High risk — urgent endoscopy

### Rockall Score
Post-endoscopy score for mortality and rebleeding risk assessment.

| Score | Mortality |
|-------|-----------|
| 0 | 0.2% |
| 1 | 0.4% |
| 2 | 2.2% |
| 3 | 3.3% |
| 4 | 5.3% |
| 5-6 | 8% |
| 7-8 | 14% |
| ≥9 | 27% |

### AIMS65
In-hospital mortality prediction. Points for: Albumin <3, INR >1.5, altered Mental status, SBP ≤90, Age ≥65.

---

## Quick Start

```bash
# GBS calculation
python gibleed_sentinel.py gbs --bun 12.0 --hemoglobin 9.5 --sex male --sbp 95 --heart-rate 110 --melena

# Rockall score
python gibleed_sentinel.py rockall --age 70 --sbp 85 --comorbidity cardiac --diagnosis peptic_ulcer

# AIMS65 score
python gibleed_sentinel.py aims65 --albumin 2.5 --inr 2.0 --mental-status-altered --sbp 85 --age 70

# Comprehensive triage (all scores)
python gibleed_sentinel.py triage --bun 12.0 --hemoglobin 9.0 --sbp 95 --heart-rate 110 --melena --albumin 2.5 --inr 2.0 --age 70

# Batch processing
python gibleed_sentinel.py batch -i patients.csv -o results.csv --score gbs
```

---

## Python API

```python
from gibleed_sentinel import calculate_gbs, calculate_rockall, calculate_aims65, triage_gi_bleed

# GBS
result = calculate_gbs(bun_mmol_l=12.0, hemoglobin_g_dl=9.5, sex="male",
                       sbp_mmhg=95, heart_rate=110, melena=True)
print(f"GBS: {result['total_score']} ({result['risk_category']})")

# Rockall
result = calculate_rockall(age=70, shock_sbp=85, comorbidity="cardiac")
print(f"Rockall: {result['total_score']} (Mortality: {result['mortality_percent']}%)")

# AIMS65
result = calculate_aims65(albumin_g_dl=2.5, inr=2.0, mental_status_altered=True, sbp_mmhg=85, age=70)
print(f"AIMS65: {result['total_score']} (Mortality: {result['mortality_percent']}%)")

# Comprehensive triage
result = triage_gi_bleed(bun_mmol_l=12.0, hemoglobin_g_dl=9.0, sbp_mmhg=95, age=70)
print(f"Urgency: {result['overall_urgency']}")
```

---

## Tests

```bash
python -m pytest test_gibleed_sentinel.py -v
```

---

## References

- Blatchford O, et al. *Lancet* 2000;356:1318-21
- Rockall TA, et al. *Gut* 1996;38:316-21
- Saltzman JR, et al. *Am J Gastroenterol* 2015;110:18-33

## License

MIT License. See [LICENSE](LICENSE).
