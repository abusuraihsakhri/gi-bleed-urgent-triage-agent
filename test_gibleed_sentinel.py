#!/usr/bin/env python3
"""
Tests for GI Bleed Urgent Triage Agent - GBS, Rockall, AIMS65, and Triage.
"""
import json
import sys
import os
import pytest

sys.path.insert(0, os.path.dirname(__file__))

from gibleed_sentinel import (
    calculate_gbs,
    calculate_rockall,
    calculate_aims65,
    triage_gi_bleed,
    main,
    _validate_range,
    _validate_inputs,
)


# =============================================================================
# GBS Tests
# =============================================================================

class TestGBS:
    def test_gbs_zero_score(self):
        """Score 0: all normal values, no clinical features."""
        result = calculate_gbs(bun_mmol_l=4.0, hemoglobin_g_dl=15.0, sex="male",
                               sbp_mmhg=130, heart_rate=72)
        assert result["total_score"] == 0
        assert result["risk_category"] == "Very Low"
        assert result["safe_for_outpatient"] is True

    def test_gbs_bun_6_5(self):
        """BUN 6.5-7.9 scores 2."""
        result = calculate_gbs(bun_mmol_l=7.0)
        assert result["components"]["bun"] == 2

    def test_gbs_bun_8_0(self):
        """BUN 8.0-9.9 scores 3."""
        result = calculate_gbs(bun_mmol_l=9.0)
        assert result["components"]["bun"] == 3

    def test_gbs_bun_10_0(self):
        """BUN 10.0-24.9 scores 4."""
        result = calculate_gbs(bun_mmol_l=15.0)
        assert result["components"]["bun"] == 4

    def test_gbs_bun_25(self):
        """BUN >= 25 scores 6."""
        result = calculate_gbs(bun_mmol_l=30.0)
        assert result["components"]["bun"] == 6

    def test_gbs_hemoglobin_male_low(self):
        """Male hemoglobin < 10 scores 6."""
        result = calculate_gbs(hemoglobin_g_dl=8.5, sex="male")
        assert result["components"]["hemoglobin"] == 6

    def test_gbs_hemoglobin_male_mid(self):
        """Male hemoglobin 10-11.9 scores 3."""
        result = calculate_gbs(hemoglobin_g_dl=11.0, sex="male")
        assert result["components"]["hemoglobin"] == 3

    def test_gbs_hemoglobin_male_borderline(self):
        """Male hemoglobin 12-12.9 scores 1."""
        result = calculate_gbs(hemoglobin_g_dl=12.5, sex="male")
        assert result["components"]["hemoglobin"] == 1

    def test_gbs_hemoglobin_male_normal(self):
        """Male hemoglobin >= 13 scores 0."""
        result = calculate_gbs(hemoglobin_g_dl=14.0, sex="male")
        assert result["components"]["hemoglobin"] == 0

    def test_gbs_hemoglobin_female_low(self):
        """Female hemoglobin < 10 scores 6."""
        result = calculate_gbs(hemoglobin_g_dl=9.0, sex="female")
        assert result["components"]["hemoglobin"] == 6

    def test_gbs_hemoglobin_female_mid(self):
        """Female hemoglobin 10-11.9 scores 1."""
        result = calculate_gbs(hemoglobin_g_dl=11.0, sex="female")
        assert result["components"]["hemoglobin"] == 1

    def test_gbs_sbp_low(self):
        """SBP < 90 scores 3."""
        result = calculate_gbs(sbp_mmhg=80)
        assert result["components"]["sbp"] == 3

    def test_gbs_sbp_mid(self):
        """SBP 90-99 scores 2."""
        result = calculate_gbs(sbp_mmhg=95)
        assert result["components"]["sbp"] == 2

    def test_gbs_sbp_borderline(self):
        """SBP 100-109 scores 1."""
        result = calculate_gbs(sbp_mmhg=105)
        assert result["components"]["sbp"] == 1

    def test_gbs_hr_elevated(self):
        """HR >= 100 scores 1."""
        result = calculate_gbs(heart_rate=110)
        assert result["components"]["heart_rate"] == 1

    def test_gbs_hr_normal(self):
        """HR < 100 scores 0."""
        result = calculate_gbs(heart_rate=80)
        assert result["components"]["heart_rate"] == 0

    def test_gbs_melena(self):
        """Melena scores 1."""
        result = calculate_gbs(melena=True)
        assert result["components"]["melena"] == 1

    def test_gbs_syncope(self):
        """Syncope scores 2."""
        result = calculate_gbs(syncope=True)
        assert result["components"]["syncope"] == 2

    def test_gbs_hepatic_disease(self):
        """Hepatic disease scores 2."""
        result = calculate_gbs(hepatic_disease=True)
        assert result["components"]["hepatic_disease"] == 2

    def test_gbs_cardiac_failure(self):
        """Cardiac failure scores 2."""
        result = calculate_gbs(cardiac_failure=True)
        assert result["components"]["cardiac_failure"] == 2

    def test_gbs_max_score(self):
        """Maximum possible score is 23."""
        result = calculate_gbs(
            bun_mmol_l=30.0, hemoglobin_g_dl=8.0, sex="male",
            sbp_mmhg=80, heart_rate=120,
            melena=True, syncope=True,
            hepatic_disease=True, cardiac_failure=True,
        )
        assert result["total_score"] == 23
        assert result["risk_category"] == "Very High"

    def test_gbs_high_risk_scenario(self):
        """High-risk patient scenario."""
        result = calculate_gbs(
            bun_mmol_l=12.0, hemoglobin_g_dl=9.5, sex="male",
            sbp_mmhg=95, heart_rate=105,
            melena=True, syncope=False,
            hepatic_disease=False, cardiac_failure=False,
        )
        assert result["total_score"] >= 6
        assert result["risk_category"] in ("High", "Very High")

    def test_gbs_none_inputs(self):
        """None inputs are handled gracefully."""
        result = calculate_gbs()
        assert result["total_score"] == 0


# =============================================================================
# AIMS65 Tests
# =============================================================================

class TestAIMS65:
    def test_aims65_zero(self):
        """All normal values give score 0."""
        result = calculate_aims65(albumin_g_dl=4.0, inr=1.0,
                                  mental_status_altered=False,
                                  sbp_mmhg=120, age=50)
        assert result["total_score"] == 0
        assert result["risk_category"] == "Very Low"

    def test_aims65_albumin_low(self):
        """Albumin < 3 scores 1."""
        result = calculate_aims65(albumin_g_dl=2.5)
        assert result["components"]["albumin_low"] == 1

    def test_aims65_albumin_normal(self):
        """Albumin >= 3 scores 0."""
        result = calculate_aims65(albumin_g_dl=3.5)
        assert result["components"]["albumin_low"] == 0

    def test_aims65_inr_elevated(self):
        """INR > 1.5 scores 1."""
        result = calculate_aims65(inr=2.0)
        assert result["components"]["inr_elevated"] == 1

    def test_aims65_inr_normal(self):
        """INR <= 1.5 scores 0."""
        result = calculate_aims65(inr=1.3)
        assert result["components"]["inr_elevated"] == 0

    def test_aims65_mental_status(self):
        """Altered mental status scores 1."""
        result = calculate_aims65(mental_status_altered=True)
        assert result["components"]["mental_status_altered"] == 1

    def test_aims65_sbp_low(self):
        """SBP <= 90 scores 1."""
        result = calculate_aims65(sbp_mmhg=85)
        assert result["components"]["sbp_low"] == 1

    def test_aims65_sbp_normal(self):
        """SBP > 90 scores 0."""
        result = calculate_aims65(sbp_mmhg=110)
        assert result["components"]["sbp_low"] == 0

    def test_aims65_age_elevated(self):
        """Age >= 65 scores 1."""
        result = calculate_aims65(age=70)
        assert result["components"]["age_elevated"] == 1

    def test_aims65_age_normal(self):
        """Age < 65 scores 0."""
        result = calculate_aims65(age=55)
        assert result["components"]["age_elevated"] == 0

    def test_aims65_max_score(self):
        """Maximum score is 5."""
        result = calculate_aims65(
            albumin_g_dl=2.0, inr=2.5,
            mental_status_altered=True,
            sbp_mmhg=80, age=75,
        )
        assert result["total_score"] == 5
        assert result["risk_category"] == "High"


# =============================================================================
# Rockall Tests
# =============================================================================

class TestRockall:
    def test_rockall_zero(self):
        """Young patient, no shock, no comorbidity, no findings."""
        result = calculate_rockall(age=40, shock_hr=70, shock_sbp=130,
                                   comorbidity="none",
                                   endoscopic_diagnosis="none",
                                   major_stigmata="none")
        assert result["total_score"] == 0
        assert result["risk_category"] == "Low"

    def test_rockall_age_60(self):
        """Age 60-79 scores 1."""
        result = calculate_rockall(age=65)
        assert result["clinical_components"]["age"] == 1

    def test_rockall_age_80(self):
        """Age >= 80 scores 2."""
        result = calculate_rockall(age=85)
        assert result["clinical_components"]["age"] == 2

    def test_rockall_shock_tachycardia(self):
        """HR > 100 with SBP >= 100 scores 1."""
        result = calculate_rockall(shock_hr=110, shock_sbp=120)
        assert result["clinical_components"]["shock"] == 1

    def test_rockall_shock_hypotension(self):
        """SBP < 100 scores 2."""
        result = calculate_rockall(shock_hr=120, shock_sbp=85)
        assert result["clinical_components"]["shock"] == 2

    def test_rockall_comorbidity_cardiac(self):
        """Cardiac comorbidity scores 2."""
        result = calculate_rockall(comorbidity="cardiac")
        assert result["clinical_components"]["comorbidity"] == 2

    def test_rockall_comorbidity_major(self):
        """Major comorbidity scores 3."""
        result = calculate_rockall(comorbidity="major")
        assert result["clinical_components"]["comorbidity"] == 3

    def test_rockall_diagnosis_peptic(self):
        """Peptic ulcer scores 1."""
        result = calculate_rockall(endoscopic_diagnosis="peptic_ulcer")
        assert result["endoscopic_components"]["diagnosis"] == 1

    def test_rockall_diagnosis_cancer(self):
        """Cancer scores 2."""
        result = calculate_rockall(endoscopic_diagnosis="cancer")
        assert result["endoscopic_components"]["diagnosis"] == 2

    def test_rockall_stigmata_active(self):
        """Active bleeding scores 2."""
        result = calculate_rockall(major_stigmata="active_bleeding")
        assert result["endoscopic_components"]["major_stigmata"] == 2

    def test_rockall_mortality_at_zero(self):
        """Score 0 has 0.2% mortality."""
        result = calculate_rockall(age=40, shock_sbp=130, shock_hr=70)
        assert result["mortality_percent"] == 0.2

    def test_rockall_mortality_at_5(self):
        """Score 5 has 8% mortality."""
        result = calculate_rockall(age=85, shock_sbp=85, comorbidity="major")
        assert result["total_score"] >= 5
        assert result["mortality_percent"] >= 8.0

    def test_rockall_max_score(self):
        """Maximum score is 11."""
        result = calculate_rockall(
            age=85, shock_hr=120, shock_sbp=80,
            comorbidity="major",
            endoscopic_diagnosis="cancer",
            major_stigmata="active_bleeding",
        )
        assert result["total_score"] == 11
        assert result["mortality_percent"] == 27.0


# =============================================================================
# Triage Tests
# =============================================================================

class TestTriage:
    def test_triage_low_urgency(self):
        """Low-risk patient gets LOW urgency."""
        result = triage_gi_bleed(
            bun_mmol_l=4.0, hemoglobin_g_dl=14.0, sex="male",
            sbp_mmhg=130, heart_rate=72,
        )
        assert result["overall_urgency"] == "LOW"

    def test_triage_critical_urgency(self):
        """High GBS triggers CRITICAL urgency."""
        result = triage_gi_bleed(
            bun_mmol_l=30.0, hemoglobin_g_dl=8.0, sex="male",
            sbp_mmhg=80, heart_rate=120,
            melena=True, syncope=True,
            hepatic_disease=True, cardiac_failure=True,
        )
        assert result["overall_urgency"] == "CRITICAL"

    def test_triage_has_all_scores(self):
        """Triage result contains all three scoring systems."""
        result = triage_gi_bleed(bun_mmol_l=10.0, sbp_mmhg=95)
        assert "gbs" in result
        assert "aims65" in result
        assert "rockall" in result
        assert "overall_urgency" in result


# =============================================================================
# CLI Tests
# =============================================================================

class TestCLI:
    def test_cli_gbs(self):
        """CLI GBS subcommand works."""
        ret = main(["gbs", "--bun", "10.0", "--sbp", "95", "--melena"])
        assert ret == 0

    def test_cli_rockall(self):
        """CLI Rockall subcommand works."""
        ret = main(["rockall", "--age", "70", "--sbp", "85", "--comorbidity", "cardiac"])
        assert ret == 0

    def test_cli_aims65(self):
        """CLI AIMS65 subcommand works."""
        ret = main(["aims65", "--albumin", "2.5", "--inr", "2.0", "--age", "70"])
        assert ret == 0

    def test_cli_triage(self):
        """CLI triage subcommand works."""
        ret = main(["triage", "--bun", "12.0", "--hemoglobin", "9.0", "--sbp", "95"])
        assert ret == 0


# =============================================================================
# Input Validation Tests
# =============================================================================

class TestInputValidation:
    """Tests for input range validation."""

    def test_validate_range_valid(self):
        """Valid values pass validation."""
        _validate_range("bun_mmol_l", 10.0, 0.0, 100.0)
        _validate_range("hemoglobin_g_dl", 12.0, 0.0, 25.0)

    def test_validate_range_none(self):
        """None values are skipped."""
        _validate_range("bun_mmol_l", None, 0.0, 100.0)

    def test_validate_range_below_min(self):
        """Values below minimum raise ValueError."""
        with pytest.raises(ValueError, match="must be between"):
            _validate_range("bun_mmol_l", -5.0, 0.0, 100.0)

    def test_validate_range_above_max(self):
        """Values above maximum raise ValueError."""
        with pytest.raises(ValueError, match="must be between"):
            _validate_range("bun_mmol_l", 150.0, 0.0, 100.0)

    def test_validate_range_nan(self):
        """NaN values raise ValueError."""
        with pytest.raises(ValueError, match="finite number"):
            _validate_range("bun_mmol_l", float("nan"), 0.0, 100.0)

    def test_validate_range_inf(self):
        """Infinite values raise ValueError."""
        with pytest.raises(ValueError, match="finite number"):
            _validate_range("bun_mmol_l", float("inf"), 0.0, 100.0)

    def test_validate_range_wrong_type(self):
        """Non-numeric values raise TypeError."""
        with pytest.raises(TypeError, match="must be a number"):
            _validate_range("bun_mmol_l", "ten", 0.0, 100.0)


class TestGBSInputValidation:
    """Tests for GBS input validation."""

    def test_gbs_negative_bun_raises(self):
        """Negative BUN raises ValueError."""
        with pytest.raises(ValueError):
            calculate_gbs(bun_mmol_l=-5.0)

    def test_gbs_excessive_hemoglobin_raises(self):
        """Excessive hemoglobin raises ValueError."""
        with pytest.raises(ValueError):
            calculate_gbs(hemoglobin_g_dl=50.0)

    def test_gbs_valid_inputs(self):
        """Valid inputs work correctly."""
        result = calculate_gbs(bun_mmol_l=10.0, hemoglobin_g_dl=12.0, sbp_mmhg=120, heart_rate=80)
        assert result["total_score"] >= 0


class TestRockallInputValidation:
    """Tests for Rockall input validation."""

    def test_rockall_negative_age_raises(self):
        """Negative age raises ValueError."""
        with pytest.raises(ValueError):
            calculate_rockall(age=-10)

    def test_rockall_excessive_sbp_raises(self):
        """Excessive SBP raises ValueError."""
        with pytest.raises(ValueError):
            calculate_rockall(shock_sbp=500)

    def test_rockall_valid_inputs(self):
        """Valid inputs work correctly."""
        result = calculate_rockall(age=50, shock_hr=80, shock_sbp=120)
        assert result["total_score"] >= 0


class TestAIMS65InputValidation:
    """Tests for AIMS65 input validation."""

    def test_aims65_negative_albumin_raises(self):
        """Negative albumin raises ValueError."""
        with pytest.raises(ValueError):
            calculate_aims65(albumin_g_dl=-1.0)

    def test_aims65_excessive_inr_raises(self):
        """Excessive INR raises ValueError."""
        with pytest.raises(ValueError):
            calculate_aims65(inr=50.0)

    def test_aims65_valid_inputs(self):
        """Valid inputs work correctly."""
        result = calculate_aims65(albumin_g_dl=3.5, inr=1.2, age=50)
        assert result["total_score"] >= 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
