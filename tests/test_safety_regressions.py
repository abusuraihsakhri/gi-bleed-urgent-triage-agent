"""Boundary, missing-value, audit, API, and packaging regressions."""
import pytest

from agents.base import AuditTrail
from gibleed_sentinel import (
    calculate_aims65, calculate_gbs, calculate_rockall,
    triage_gi_bleed, _bool_str, _float_or_none,
)


def test_gbs_incomplete_cannot_clear_for_outpatient():
    result = calculate_gbs()
    assert result["total_score"] == 0
    assert not result["score_complete"]
    assert not result["safe_for_outpatient"]
    assert result["risk_category"] == "Indeterminate"
    assert triage_gi_bleed()["overall_urgency"] == "INDETERMINATE"


def test_gbs_very_low_risk_boundary():
    inputs = dict(bun_mmol_l=4, hemoglobin_g_dl=15, sex="male",
                  sbp_mmhg=130, heart_rate=80)
    result = calculate_gbs(**inputs, melena=True)
    assert result["total_score"] == 1
    assert result["safe_for_outpatient"] is True
    assert calculate_gbs(**inputs, syncope=True)["safe_for_outpatient"] is False


def test_gbs_bun_and_hemoglobin_boundaries():
    assert calculate_gbs(bun_mmol_l=25)["components"]["bun"] == 4
    assert calculate_gbs(bun_mmol_l=25.01)["components"]["bun"] == 6
    assert calculate_gbs(hemoglobin_g_dl=12.95)["components"]["hemoglobin"] == 1
    assert calculate_gbs(hemoglobin_g_dl=13)["components"]["hemoglobin"] == 0


def test_aims65_age_is_strict():
    assert calculate_aims65(age=65)["components"]["age_elevated"] == 0
    assert calculate_aims65(age=66)["components"]["age_elevated"] == 1


def test_aims65_missing_is_not_mortality_zero():
    result = calculate_aims65()
    assert result["risk_category"] == "Indeterminate"
    assert result["score_complete"] is False
    assert result["mortality_percent"] is None


def test_rockall_no_fabricated_mortality():
    result = calculate_rockall(age=85, shock_hr=110, shock_sbp=85,
                               comorbidity="major", endoscopic_diagnosis="cancer",
                               major_stigmata="blood")
    assert result["total_score"] == 11
    assert result["mortality_percent"] is None


@pytest.mark.parametrize("value", [float("nan"), float("inf"), True, -1])
def test_invalid_numerics(value):
    with pytest.raises((ValueError, TypeError)):
        calculate_gbs(bun_mmol_l=value)


def test_invalid_sex_rejected():
    with pytest.raises(ValueError):
        calculate_gbs(hemoglobin_g_dl=12, sex="unknown")


def test_hmac_tampering_detected():
    trail = AuditTrail(secret_key="0123456789abcdef0123456789abcdef")
    trail.log("service", "test", "EVALUATE", {"count": 1})
    trail.log("service", "test", "EVALUATE", {"count": 2})
    assert trail.verify_integrity()
    exported = trail.get_trail()
    exported[0]["event_type"] = "MODIFIED"
    assert trail.verify_integrity()
    trail.logs[0]["event_type"] = "MODIFIED"
    assert not trail.verify_integrity()


def test_api_rejects_unexpected_identifiers():
    from fastapi.testclient import TestClient
    from agents.clinical_api import app
    client = TestClient(app)
    fields = dict(bun_mmol_l=4, hemoglobin_g_dl=15, sex="male", sbp_mmhg=130,
                  heart_rate=80, melena=False, syncope=False,
                  hepatic_disease=False, cardiac_failure=False)
    res = client.post("/api/gbs", json=fields)
    assert res.status_code == 200 and res.json()["score_complete"]
    assert res.json()["safe_for_outpatient"]
    assert res.headers["Cache-Control"] == "no-store"
    assert client.post("/api/gbs", json={**fields, "patient_name": "Jane Doe"}).status_code == 422
    assert client.post("/api/gbs", json={**fields, "bun_mmol_l": -2}).status_code == 422
    assert client.get("/health").status_code == 200
