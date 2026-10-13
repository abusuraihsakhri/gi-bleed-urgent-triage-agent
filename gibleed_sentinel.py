#!/usr/bin/env python3
"""
GI Bleed Urgent Triage Agent
Implements three validated scoring systems for upper GI bleeding risk stratification:
  1. Glasgow-Blatchford Score (GBS) - pre-endoscopy risk stratification
  2. Rockall Score - post-endoscopy mortality/rebleeding risk
  3. AIMS65 Score - in-hospital mortality prediction

All formulas are based on published clinical literature. Zero external dependencies.

References:
  - Blatchford O, et al. Lancet 2000;356:1318-21
  - Rockall TA, et al. Gut 1996;38:316-21
  - Saltzman JR, et al. Am J Gastroenterol 2015;110:18-33 (AIMS65)

Author: Dr. Abu Suraih Sakhri
License: MIT
"""

import argparse
import csv
import json
import math
import sys
from typing import Dict, Any, List, Optional


# =============================================================================
# Input Validation
# =============================================================================

# Clinically plausible ranges for input parameters
VALID_RANGES = {
    "bun_mmol_l": (0.0, 100.0),
    "hemoglobin_g_dl": (0.0, 25.0),
    "sbp_mmhg": (0.0, 300.0),
    "heart_rate": (0.0, 300.0),
    "albumin_g_dl": (0.0, 10.0),
    "inr": (0.0, 20.0),
    "age": (0, 150),
}


def _validate_range(name: str, value: Optional[float], min_val: float, max_val: float) -> None:
    """Validate that a numeric value falls within an acceptable clinical range."""
    if value is None:
        return
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{name} must be a number, got {type(value).__name__}")
    if math.isnan(value) or math.isinf(value):
        raise ValueError(f"{name} must be a finite number, got {value}")
    if value < min_val or value > max_val:
        raise ValueError(f"{name} must be between {min_val} and {max_val}, got {value}")


def _validate_inputs(**kwargs) -> None:
    """Validate multiple input parameters against their defined ranges."""
    for name, value in kwargs.items():
        if name in VALID_RANGES:
            min_val, max_val = VALID_RANGES[name]
            _validate_range(name, value, min_val, max_val)


# =============================================================================
# Glasgow-Blatchford Score (GBS) - Pre-endoscopy
# =============================================================================

def calculate_gbs(
    bun_mmol_l: Optional[float] = None,
    hemoglobin_g_dl: Optional[float] = None,
    sex: str = "male",
    sbp_mmhg: Optional[float] = None,
    heart_rate: Optional[float] = None,
    melena: bool = False,
    syncope: bool = False,
    hepatic_disease: bool = False,
    cardiac_failure: bool = False,
    history_confirmed: bool = False,
) -> Dict[str, Any]:
    """
    Calculate Glasgow-Blatchford Score for upper GI bleed risk stratification.

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

    Raises:
        ValueError: If any input is outside clinically plausible range.
        TypeError: If any input is not a number.
    """
    _validate_inputs(
        bun_mmol_l=bun_mmol_l, hemoglobin_g_dl=hemoglobin_g_dl,
        sbp_mmhg=sbp_mmhg, heart_rate=heart_rate,
    )

    if not isinstance(sex, str) or sex.lower() not in ("male", "female"):
        raise ValueError("sex must be 'male' or 'female'")
    missing = [key for key, val in (
        ("bun_mmol_l", bun_mmol_l), ("hemoglobin_g_dl", hemoglobin_g_dl),
        ("sbp_mmhg", sbp_mmhg), ("heart_rate", heart_rate)
    ) if val is None]
    components = {}
    total = 0

    # BUN scoring (mmol/L)
    if bun_mmol_l is not None:
        if bun_mmol_l > 25.0:
            components["bun"] = 6
        elif bun_mmol_l >= 10.0:
            components["bun"] = 4
        elif bun_mmol_l >= 8.0:
            components["bun"] = 3
        elif bun_mmol_l >= 6.5:
            components["bun"] = 2
        else:
            components["bun"] = 0
        total += components["bun"]

    # Hemoglobin scoring (sex-dependent)
    if hemoglobin_g_dl is not None:
        sex_lower = sex.lower()
        if sex_lower == "male":
            if hemoglobin_g_dl < 10.0:
                components["hemoglobin"] = 6
            elif hemoglobin_g_dl < 12.0:
                components["hemoglobin"] = 3
            elif hemoglobin_g_dl < 13.0:
                components["hemoglobin"] = 1
            else:
                components["hemoglobin"] = 0
        else:  # female
            if hemoglobin_g_dl < 10.0:
                components["hemoglobin"] = 6
            elif hemoglobin_g_dl < 12.0:
                components["hemoglobin"] = 1
            else:
                components["hemoglobin"] = 0
        total += components["hemoglobin"]

    # SBP scoring
    if sbp_mmhg is not None:
        if sbp_mmhg < 90:
            components["sbp"] = 3
        elif sbp_mmhg < 100:
            components["sbp"] = 2
        elif sbp_mmhg <= 109:
            components["sbp"] = 1
        else:
            components["sbp"] = 0
        total += components["sbp"]

    # Heart rate scoring
    if heart_rate is not None:
        components["heart_rate"] = 1 if heart_rate >= 100 else 0
        total += components["heart_rate"]

    # Clinical features
    components["melena"] = 1 if melena else 0
    total += components["melena"]

    components["syncope"] = 2 if syncope else 0
    total += components["syncope"]

    components["hepatic_disease"] = 2 if hepatic_disease else 0
    total += components["hepatic_disease"]

    components["cardiac_failure"] = 2 if cardiac_failure else 0
    total += components["cardiac_failure"]

    if not isinstance(history_confirmed, bool):
        raise TypeError("history_confirmed must be boolean")
    if not history_confirmed:
        missing.append("clinical_features_confirmation")
    # Higher score categories are descriptive, not validated disposition thresholds.
    if missing and total <= 1:
        risk = "Indeterminate"
        recommendation = "Partial GBS: confirm clinical features and missing observations before considering discharge."
    elif total <= 1:
        risk = "Very Low"
        recommendation = "GBS 0-1 may support outpatient follow-up after clinician assessment of stability and other risks."
    elif total <= 3:
        risk = "Low"
        recommendation = "Clinical assessment required; GBS above 1 does not meet the ACG very-low-risk discharge criterion."
    elif total <= 5:
        risk = "Moderate"
        recommendation = "Assess clinically; GBS category alone does not determine treatment or endoscopy timing."
    elif total <= 8:
        risk = "High"
        recommendation = "Prompt senior clinical assessment; stabilize and investigate as indicated."
    else:
        risk = "Very High"
        recommendation = "Urgent clinical evaluation and resuscitation if indicated; score alone does not mandate ICU care."

    return {
        "tool": "glasgow-blatchford-score",
        "total_score": total,
        "max_possible_score": 23,
        "components": components,
        "risk_category": risk,
        "recommendation": recommendation,
        "score_complete": not missing,
        "missing_fields": missing,
        "safe_for_outpatient": False,  # A score alone cannot authorize discharge.
        "meets_very_low_risk_criterion": not missing and total <= 1,
        "clinical_caveat": "Screening score only; does not replace clinician judgment.",
    }


# =============================================================================
# Rockall Score - Post-endoscopy
# =============================================================================

def calculate_rockall(
    age: Optional[int] = None,
    shock_hr: Optional[float] = None,
    shock_sbp: Optional[float] = None,
    comorbidity: str = "none",
    endoscopic_diagnosis: str = "none",
    major_stigmata: str = "none",
) -> Dict[str, Any]:
    """
    Calculate Rockall Score for upper GI bleeding (pre- and post-endoscopy).

    Parameters:
        age: Patient age in years
        shock_hr: Heart rate in bpm (for shock assessment)
        shock_sbp: Systolic blood pressure in mmHg (for shock assessment)
        comorbidity: 'none', 'cardiac' (CHF/IHD), or 'major' (renal/liver failure, disseminated malignancy)
        endoscopic_diagnosis: 'none'/'mallory-weiss', 'peptic_ulcer'/'esd', or 'cancer'
        major_stigmata: 'none'/'dark_spot', or 'blood'/'visible_vessel'/'active_bleeding'

    Returns:
        Dict with clinical score, endoscopic score, total score, mortality risk.

    Raises:
        ValueError: If any input is outside clinically plausible range.
        TypeError: If any input is not a number.
    """
    _validate_inputs(
        age=age, heart_rate=shock_hr, sbp_mmhg=shock_sbp,
    )

    missing = [key for key, val in (
        ("age", age), ("shock_hr", shock_hr), ("shock_sbp", shock_sbp),
        ("endoscopic_diagnosis", endoscopic_diagnosis), ("major_stigmata", major_stigmata)
    ) if val is None]
    clinical_score = 0
    clinical_components = {}

    # Age
    if age is not None:
        if age >= 80:
            clinical_components["age"] = 2
        elif age >= 60:
            clinical_components["age"] = 1
        else:
            clinical_components["age"] = 0
        clinical_score += clinical_components["age"]

    # Shock
    if shock_hr is not None or shock_sbp is not None:
        hr = shock_hr if shock_hr is not None else 0
        sbp = shock_sbp if shock_sbp is not None else 200
        if sbp < 100:
            clinical_components["shock"] = 2
        elif hr >= 100 and sbp >= 100:
            clinical_components["shock"] = 1
        else:
            clinical_components["shock"] = 0
        clinical_score += clinical_components["shock"]

    # Comorbidity
    comorb_lower = comorbidity.lower().strip()
    if comorb_lower in ("major", "renal", "liver", "malignancy", "renal_failure",
                         "liver_failure", "disseminated_malignancy"):
        clinical_components["comorbidity"] = 3
    elif comorb_lower in ("cardiac", "chf", "ihd", "cardiac_failure",
                           "ischemic_heart_disease"):
        clinical_components["comorbidity"] = 2
    else:
        clinical_components["comorbidity"] = 0
    clinical_score += clinical_components["comorbidity"]

    # Endoscopic components
    endo_score = 0
    endo_components = {}

    # Diagnosis
    diag_lower = endoscopic_diagnosis.lower().strip()
    if diag_lower in ("cancer", "malignant", "gastric_cancer"):
        endo_components["diagnosis"] = 2
    elif diag_lower in ("peptic_ulcer", "esd", "erosive_disease", "duodenal_ulcer",
                         "gastric_ulcer", "peptic"):
        endo_components["diagnosis"] = 1
    else:
        endo_components["diagnosis"] = 0
    endo_score += endo_components["diagnosis"]

    # Major stigmata of recent hemorrhage
    stig_lower = major_stigmata.lower().strip()
    if stig_lower in ("blood", "visible_vessel", "active_bleeding",
                       "active", "vessel", "blood_in_ugit"):
        endo_components["major_stigmata"] = 2
    else:
        endo_components["major_stigmata"] = 0
    endo_score += endo_components["major_stigmata"]

    total = clinical_score + endo_score

    # Risk estimates require a calibrated clinical population; do not fabricate
    # individual mortality percentages from this uncalibrated lookup table.
    mortality_pct = None

    # Risk category
    if missing:
        risk = "Indeterminate"
        recommendation = "Partial Rockall only; collect missing inputs and assess clinically."
    elif total <= 2:
        risk = "Low"
        recommendation = "Relatively low Rockall score; disposition requires clinical assessment."
    elif total <= 4:
        risk = "Moderate"
        recommendation = "Correlate score with clinical course and endoscopic findings."
    elif total <= 6:
        risk = "High"
        recommendation = "Senior clinical review advised; score alone does not mandate ICU care."
    else:
        risk = "Very High"
        recommendation = "Urgent clinical review; interventions depend on bleeding and stability."

    return {
        "tool": "rockall-score",
        "clinical_score": clinical_score,
        "clinical_components": clinical_components,
        "endoscopic_score": endo_score,
        "endoscopic_components": endo_components,
        "total_score": total,
        "max_possible_score": 11,
        "mortality_percent": mortality_pct,
        "score_complete": not missing,
        "missing_fields": missing,
        "risk_category": risk,
        "recommendation": recommendation,
    }


# =============================================================================
# AIMS65 Score - In-hospital mortality
# =============================================================================

def calculate_aims65(
    albumin_g_dl: Optional[float] = None,
    inr: Optional[float] = None,
    mental_status_altered: bool = False,
    sbp_mmhg: Optional[float] = None,
    age: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Calculate AIMS65 score for in-hospital mortality in upper GI bleeding.

    Parameters:
        albumin_g_dl: Serum albumin in g/dL
        inr: International normalized ratio
        mental_status_altered: Altered mental status (GCS <14 or disoriented)
        sbp_mmhg: Systolic blood pressure in mmHg
        age: Patient age in years

    Returns:
        Dict with total score (0-5), mortality risk, and component breakdown.

    Raises:
        ValueError: If any input is outside clinically plausible range.
        TypeError: If any input is not a number.
    """
    _validate_inputs(
        albumin_g_dl=albumin_g_dl, inr=inr,
        sbp_mmhg=sbp_mmhg, age=age,
    )

    missing = [key for key, val in (
        ("albumin_g_dl", albumin_g_dl), ("inr", inr),
        ("sbp_mmhg", sbp_mmhg), ("age", age)
    ) if val is None]
    components = {}
    total = 0

    if albumin_g_dl is not None:
        components["albumin_low"] = 1 if albumin_g_dl < 3.0 else 0
        total += components["albumin_low"]

    if inr is not None:
        components["inr_elevated"] = 1 if inr > 1.5 else 0
        total += components["inr_elevated"]

    components["mental_status_altered"] = 1 if mental_status_altered else 0
    total += components["mental_status_altered"]

    if sbp_mmhg is not None:
        components["sbp_low"] = 1 if sbp_mmhg <= 90 else 0
        total += components["sbp_low"]

    if age is not None:
        components["age_elevated"] = 1 if age > 65 else 0
        total += components["age_elevated"]

    # AIMS65 is prognostic; absolute mortality varies across cohorts.
    mortality_pct = None
    if missing:
        risk = "Indeterminate"
        recommendation = "Partial AIMS65 only; do not infer low mortality risk."
    elif total == 0:
        risk = "Very Low"
        recommendation = "No AIMS65 risk factors detected; clinical assessment still required."
    elif total <= 1:
        risk = "Low"
        recommendation = "Interpret in clinical context; AIMS65 does not determine level of care."
    elif total <= 2:
        risk = "Moderate"
        recommendation = "Clinical reassessment indicated; score alone does not determine care setting."
    else:
        risk = "High"
        recommendation = "Escalate clinical assessment; score alone does not mandate ICU admission."

    return {
        "tool": "aims65",
        "total_score": total,
        "max_possible_score": 5,
        "components": components,
        "mortality_percent": mortality_pct,
        "score_complete": not missing,
        "missing_fields": missing,
        "risk_category": risk,
        "recommendation": recommendation,
    }


# =============================================================================
# Combined Triage Assessment
# =============================================================================

def triage_gi_bleed(
    # GBS parameters
    bun_mmol_l: Optional[float] = None,
    hemoglobin_g_dl: Optional[float] = None,
    sex: str = "male",
    sbp_mmhg: Optional[float] = None,
    heart_rate: Optional[float] = None,
    melena: bool = False,
    syncope: bool = False,
    hepatic_disease: bool = False,
    cardiac_failure: bool = False,
    history_confirmed: bool = False,
    # AIMS65 parameters
    albumin_g_dl: Optional[float] = None,
    inr: Optional[float] = None,
    mental_status_altered: bool = False,
    age: Optional[int] = None,
    # Rockall post-endoscopy (optional)
    comorbidity: str = "none",
    endoscopic_diagnosis: str = "none",
    major_stigmata: str = "none",
) -> Dict[str, Any]:
    """
    Perform comprehensive GI bleed triage using all three scoring systems.
    """
    gbs = calculate_gbs(
        bun_mmol_l=bun_mmol_l, hemoglobin_g_dl=hemoglobin_g_dl,
        sex=sex, sbp_mmhg=sbp_mmhg, heart_rate=heart_rate,
        melena=melena, syncope=syncope,
        hepatic_disease=hepatic_disease, cardiac_failure=cardiac_failure,
        history_confirmed=history_confirmed,
    )

    aims65 = calculate_aims65(
        albumin_g_dl=albumin_g_dl, inr=inr,
        mental_status_altered=mental_status_altered,
        sbp_mmhg=sbp_mmhg, age=age,
    )

    rockall = calculate_rockall(
        age=age, shock_hr=heart_rate, shock_sbp=sbp_mmhg,
        comorbidity=comorbidity,
        endoscopic_diagnosis=endoscopic_diagnosis,
        major_stigmata=major_stigmata,
    )

    # Descriptive, unvalidated composite prioritization. Incomplete data
    # must never generate a reassuring LOW result.
    if (sbp_mmhg is not None and sbp_mmhg < 90) or (hemoglobin_g_dl is not None and hemoglobin_g_dl < 7) or mental_status_altered:
        urgency = "CRITICAL"
    elif not gbs["score_complete"] and gbs["total_score"] < 2:
        urgency = "INDETERMINATE"
    elif gbs["total_score"] >= 6 or (aims65["score_complete"] and aims65["total_score"] >= 3):
        urgency = "CRITICAL"
    elif gbs["total_score"] >= 3 or (aims65["score_complete"] and aims65["total_score"] >= 2):
        urgency = "HIGH"
    elif gbs["total_score"] >= 2 or (aims65["score_complete"] and aims65["total_score"] >= 1):
        urgency = "MODERATE"
    else:
        urgency = "LOW"

    return {
        "tool": "gi-bleed-triage-agent",
        "gbs": gbs,
        "aims65": aims65,
        "rockall": rockall,
        "overall_urgency": urgency,
        "clinical_caveat": "Unvalidated composite indicator, not a disposition or treatment recommendation.",
    }


# =============================================================================
# CLI
# =============================================================================

def _print_result(result: Dict[str, Any]) -> None:
    """Pretty-print a scoring result."""
    print(json.dumps(result, indent=2))


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="gi-bleed-urgent-triage-agent",
        description="GI Bleed Urgent Triage Agent - GBS, Rockall, and AIMS65 scoring",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # GBS subcommand
    p_gbs = subparsers.add_parser("gbs", help="Calculate Glasgow-Blatchford Score")
    p_gbs.add_argument("--bun", type=float, help="BUN in mmol/L")
    p_gbs.add_argument("--hemoglobin", type=float, help="Hemoglobin in g/dL")
    p_gbs.add_argument("--sex", choices=["male", "female"], default="male")
    p_gbs.add_argument("--sbp", type=float, help="Systolic BP in mmHg")
    p_gbs.add_argument("--heart-rate", type=float, help="Heart rate in bpm")
    p_gbs.add_argument("--melena", action="store_true")
    p_gbs.add_argument("--syncope", action="store_true")
    p_gbs.add_argument("--hepatic-disease", action="store_true")
    p_gbs.add_argument("--cardiac-failure", action="store_true")
    p_gbs.add_argument("--history-confirmed", action="store_true",
                       help="Confirm all symptoms/comorbidities assessed, including absent findings")

    # Rockall subcommand
    p_rock = subparsers.add_parser("rockall", help="Calculate Rockall Score")
    p_rock.add_argument("--age", type=int, help="Patient age")
    p_rock.add_argument("--hr", type=float, help="Heart rate in bpm")
    p_rock.add_argument("--sbp", type=float, help="Systolic BP in mmHg")
    p_rock.add_argument("--comorbidity", default="none",
                        choices=["none", "cardiac", "major"])
    p_rock.add_argument("--diagnosis", default="none",
                        choices=["none", "peptic_ulcer", "cancer"])
    p_rock.add_argument("--stigmata", default="none",
                        choices=["none", "blood", "visible_vessel", "active_bleeding"])

    # AIMS65 subcommand
    p_aims = subparsers.add_parser("aims65", help="Calculate AIMS65 Score")
    p_aims.add_argument("--albumin", type=float, help="Albumin in g/dL")
    p_aims.add_argument("--inr", type=float, help="INR")
    p_aims.add_argument("--mental-status-altered", action="store_true")
    p_aims.add_argument("--sbp", type=float, help="Systolic BP in mmHg")
    p_aims.add_argument("--age", type=int, help="Patient age")

    # Triage subcommand (combined)
    p_triage = subparsers.add_parser("triage", help="Comprehensive triage (all scores)")
    p_triage.add_argument("--bun", type=float, help="BUN in mmol/L")
    p_triage.add_argument("--hemoglobin", type=float, help="Hemoglobin in g/dL")
    p_triage.add_argument("--sex", choices=["male", "female"], default="male")
    p_triage.add_argument("--sbp", type=float, help="Systolic BP in mmHg")
    p_triage.add_argument("--heart-rate", type=float, help="Heart rate in bpm")
    p_triage.add_argument("--melena", action="store_true")
    p_triage.add_argument("--syncope", action="store_true")
    p_triage.add_argument("--hepatic-disease", action="store_true")
    p_triage.add_argument("--cardiac-failure", action="store_true")
    p_triage.add_argument("--history-confirmed", action="store_true",
                          help="Confirm symptoms/comorbidities assessed")
    p_triage.add_argument("--albumin", type=float, help="Albumin in g/dL")
    p_triage.add_argument("--inr", type=float, help="INR")
    p_triage.add_argument("--mental-status-altered", action="store_true")
    p_triage.add_argument("--age", type=int, help="Patient age")
    p_triage.add_argument("--comorbidity", default="none")
    p_triage.add_argument("--diagnosis", default="none")
    p_triage.add_argument("--stigmata", default="none")

    # Batch subcommand
    p_batch = subparsers.add_parser("batch", help="Batch process CSV")
    p_batch.add_argument("-i", "--input", required=True, help="Input CSV file")
    p_batch.add_argument("-o", "--output", default="results.csv", help="Output CSV file")
    p_batch.add_argument("--score", choices=["gbs", "rockall", "aims65", "triage"],
                         default="gbs", help="Which score to calculate")

    args = parser.parse_args(argv)

    if args.command == "gbs":
        result = calculate_gbs(
            bun_mmol_l=args.bun, hemoglobin_g_dl=args.hemoglobin,
            sex=args.sex, sbp_mmhg=args.sbp, heart_rate=args.heart_rate,
            melena=args.melena, syncope=args.syncope,
            hepatic_disease=args.hepatic_disease, cardiac_failure=args.cardiac_failure,
            history_confirmed=args.history_confirmed,
        )
        _print_result(result)

    elif args.command == "rockall":
        result = calculate_rockall(
            age=args.age, shock_hr=args.hr, shock_sbp=args.sbp,
            comorbidity=args.comorbidity,
            endoscopic_diagnosis=args.diagnosis,
            major_stigmata=args.stigmata,
        )
        _print_result(result)

    elif args.command == "aims65":
        result = calculate_aims65(
            albumin_g_dl=args.albumin, inr=args.inr,
            mental_status_altered=args.mental_status_altered,
            sbp_mmhg=args.sbp, age=args.age,
        )
        _print_result(result)

    elif args.command == "triage":
        result = triage_gi_bleed(
            bun_mmol_l=args.bun, hemoglobin_g_dl=args.hemoglobin,
            sex=args.sex, sbp_mmhg=args.sbp, heart_rate=args.heart_rate,
            melena=args.melena, syncope=args.syncope,
            hepatic_disease=args.hepatic_disease, cardiac_failure=args.cardiac_failure,
            history_confirmed=args.history_confirmed,
            albumin_g_dl=args.albumin, inr=args.inr,
            mental_status_altered=args.mental_status_altered, age=args.age,
            comorbidity=args.comorbidity,
            endoscopic_diagnosis=args.diagnosis,
            major_stigmata=args.stigmata,
        )
        _print_result(result)

    elif args.command == "batch":
        _run_batch(args.input, args.output, args.score)

    return 0


def _run_batch(input_csv: str, output_csv: str, score_type: str) -> None:
    """Process a CSV file through the selected scoring system."""
    with open(input_csv, mode="r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        fieldnames = list(reader.fieldnames or [])
        rows = list(reader)

    out_rows = []
    for r in rows:
        if score_type == "gbs":
            result = calculate_gbs(
                bun_mmol_l=_float_or_none(r.get("bun")),
                hemoglobin_g_dl=_float_or_none(r.get("hemoglobin")),
                sex=r.get("sex", "male"),
                sbp_mmhg=_float_or_none(r.get("sbp")),
                heart_rate=_float_or_none(r.get("heart_rate")),
                melena=_bool_str(r.get("melena")),
                syncope=_bool_str(r.get("syncope")),
                hepatic_disease=_bool_str(r.get("hepatic_disease")),
                cardiac_failure=_bool_str(r.get("cardiac_failure")),
                history_confirmed=_bool_str(r.get("history_confirmed")),
            )
        elif score_type == "aims65":
            result = calculate_aims65(
                albumin_g_dl=_float_or_none(r.get("albumin")),
                inr=_float_or_none(r.get("inr")),
                mental_status_altered=_bool_str(r.get("mental_status_altered")),
                sbp_mmhg=_float_or_none(r.get("sbp")),
                age=_int_or_none(r.get("age")),
            )
        elif score_type == "rockall":
            result = calculate_rockall(
                age=_int_or_none(r.get("age")),
                shock_hr=_float_or_none(r.get("heart_rate")),
                shock_sbp=_float_or_none(r.get("sbp")),
                comorbidity=r.get("comorbidity", "none"),
                endoscopic_diagnosis=r.get("diagnosis", "none"),
                major_stigmata=r.get("stigmata", "none"),
            )
        else:
            result = triage_gi_bleed(
                bun_mmol_l=_float_or_none(r.get("bun")),
                hemoglobin_g_dl=_float_or_none(r.get("hemoglobin")),
                sex=r.get("sex", "male"),
                sbp_mmhg=_float_or_none(r.get("sbp")),
                heart_rate=_float_or_none(r.get("heart_rate")),
                melena=_bool_str(r.get("melena")),
                syncope=_bool_str(r.get("syncope")),
                hepatic_disease=_bool_str(r.get("hepatic_disease")),
                cardiac_failure=_bool_str(r.get("cardiac_failure")),
                history_confirmed=_bool_str(r.get("history_confirmed")),
                albumin_g_dl=_float_or_none(r.get("albumin")),
                inr=_float_or_none(r.get("inr")),
                mental_status_altered=_bool_str(r.get("mental_status_altered")),
                age=_int_or_none(r.get("age")),
                comorbidity=r.get("comorbidity", "none"),
                endoscopic_diagnosis=r.get("diagnosis", "none"),
                major_stigmata=r.get("stigmata", "none"),
            )

        row_dict = dict(r)
        row_dict["score"] = result.get("total_score", result.get("gbs", {}).get("total_score", ""))
        row_dict["risk_category"] = result.get("risk_category", result.get("overall_urgency", ""))
        out_rows.append(row_dict)

    out_fields = fieldnames + ["score", "risk_category"]
    with open(output_csv, mode="w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=out_fields)
        writer.writeheader()
        writer.writerows(out_rows)
    print(f"Processed {len(out_rows)} records -> {output_csv}")


def _float_or_none(val) -> Optional[float]:
    if val is None or val == "":
        return None
    try:
        number = float(val)
    except (ValueError, TypeError) as exc:
        raise ValueError(f"Invalid numeric CSV value: {val!r}") from exc
    if not math.isfinite(number):
        raise ValueError(f"Non-finite CSV value: {val!r}")
    return number


def _int_or_none(val) -> Optional[int]:
    if val is None or val == "":
        return None
    number = _float_or_none(val)
    if not number.is_integer():
        raise ValueError(f"Expected an integer in CSV: {val!r}")
    return int(number)


def _bool_str(val) -> bool:
    if val is None or str(val).strip() == "":
        return False
    text = str(val).lower().strip()
    if text in ("true", "1", "yes", "y"):
        return True
    if text in ("false", "0", "no", "n"):
        return False
    raise ValueError(f"Invalid boolean CSV value: {val!r}")


if __name__ == "__main__":
    sys.exit(main())
