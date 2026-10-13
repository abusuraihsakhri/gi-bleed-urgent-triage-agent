"use strict";

/* Deterministic, dependency-free score calculations used by the static app. */
function numeric(value, name, min, max) {
  if (typeof value !== "number" || !Number.isFinite(value) || value < min || value > max) {
    throw new RangeError(name + " must be between " + min + " and " + max);
  }
  return value;
}
function flag(value, name) {
  if (typeof value !== "boolean") throw new TypeError(name + " must be true or false");
  return value;
}
function scoreGBS(p) {
  const bun = numeric(p.bun, "BUN (mmol/L)", 0, 100);
  const hb = numeric(p.hemoglobin, "Hemoglobin (g/dL)", 0, 25);
  const sbp = numeric(p.sbp, "Systolic BP (mmHg)", 0, 300);
  const hr = numeric(p.heartRate, "Heart rate (bpm)", 0, 300);
  if (p.sex !== "male" && p.sex !== "female") throw new TypeError("Sex is required for hemoglobin scoring");
  for (const key of ["melena", "syncope", "hepaticDisease", "cardiacFailure"]) flag(p[key], key);
  if (p.historyConfirmed !== true) throw new Error("Confirm that all four clinical features were assessed.");
  const components = {
    bun: bun >= 25 ? 6 : bun >= 10 ? 4 : bun >= 8 ? 3 : bun >= 6.5 ? 2 : 0,
    hemoglobin: p.sex === "male"
      ? (hb < 10 ? 6 : hb < 12 ? 3 : hb < 13 ? 1 : 0)
      : (hb < 10 ? 6 : hb < 12 ? 1 : 0),
    sbp: sbp < 90 ? 3 : sbp < 100 ? 2 : sbp < 110 ? 1 : 0,
    heartRate: hr >= 100 ? 1 : 0,
    melena: p.melena ? 1 : 0,
    syncope: p.syncope ? 2 : 0,
    hepaticDisease: p.hepaticDisease ? 2 : 0,
    cardiacFailure: p.cardiacFailure ? 2 : 0
  };
  const score = Object.values(components).reduce((a, b) => a + b, 0);
  return {
    score, maxScore: 23, components,
    meetsVeryLowRiskCriterion: score <= 1,
    interpretation: score <= 1
      ? "GBS 0–1: may support outpatient follow-up after clinician assessment; not an authorization to discharge."
      : "GBS above 1: does not meet the ACG very-low-risk outpatient criterion. Clinical assessment is required."
  };
}
function scoreAIMS65(p) {
  numeric(p.albumin, "Albumin (g/dL)", 0, 10);
  numeric(p.inr, "INR", 0, 20);
  numeric(p.sbp, "Systolic BP (mmHg)", 0, 300);
  numeric(p.age, "Age (years)", 0, 150);
  if (!Number.isInteger(p.age)) throw new RangeError("Age must be a whole number");
  flag(p.mentalStatusAltered, "mentalStatusAltered");
  const components = {
    albuminLow: p.albumin < 3 ? 1 : 0,
    inrElevated: p.inr > 1.5 ? 1 : 0,
    mentalStatusAltered: p.mentalStatusAltered ? 1 : 0,
    sbpLow: p.sbp <= 90 ? 1 : 0,
    ageOver65: p.age > 65 ? 1 : 0
  };
  return {
    score: Object.values(components).reduce((a, b) => a + b, 0),
    maxScore: 5, components,
    interpretation: "Prognostic score for in-hospital mortality, not an absolute risk percentage or care-setting recommendation."
  };
}
if (typeof module !== "undefined" && module.exports) module.exports = { scoreGBS, scoreAIMS65 };

if (typeof document !== "undefined") {
  const form = document.getElementById("clinical-form");
  const output = document.getElementById("results");
  const exportButton = document.getElementById("export");
  let lastReport = null;
  const get = name => form.elements.namedItem(name);
  const readRequired = name => {
    const raw = get(name).value.trim();
    if (!raw) throw new Error("Complete " + get(name).getAttribute("data-label") + ".");
    return Number(raw);
  };
  form.addEventListener("submit", event => {
    event.preventDefault();
    output.classList.remove("error");
    try {
      const input = {
        bun: readRequired("bun"),
        hemoglobin: readRequired("hemoglobin"),
        sex: get("sex").value,
        sbp: readRequired("sbp"),
        heartRate: readRequired("heartRate"),
        melena: get("melena").checked,
        syncope: get("syncope").checked,
        hepaticDisease: get("hepaticDisease").checked,
        cardiacFailure: get("cardiacFailure").checked,
        historyConfirmed: get("historyConfirmed").checked
      };
      const gbs = scoreGBS(input);
      let aims65 = null;
      const aimsFields = ["albumin", "inr", "age"];
      const provided = aimsFields.filter(name => get(name).value.trim() !== "");
      if (provided.length > 0 && provided.length !== aimsFields.length) {
        throw new Error("Enter all AIMS65 values (albumin, INR and age), or leave all three blank.");
      }
      if (provided.length === aimsFields.length) {
        if (!get("mentalStatusConfirmed").checked) {
          throw new Error("Confirm mental status assessment to calculate AIMS65.");
        }
        aims65 = scoreAIMS65({
          albumin: readRequired("albumin"), inr: readRequired("inr"),
          age: readRequired("age"), sbp: input.sbp,
          mentalStatusAltered: get("mentalStatusAltered").checked
        });
      }
      lastReport = { gbs, aims65, note: "Educational screening output. Clinical validation and assessment are required." };
      const lines = [
        "Glasgow–Blatchford Score: " + gbs.score + " / 23",
        gbs.interpretation, "",
        "GBS components: " + JSON.stringify(gbs.components),
        "",
        aims65 ? "AIMS65: " + aims65.score + " / 5" : "AIMS65: Not assessed (optional inputs omitted)",
        aims65 ? aims65.interpretation : "",
        "", "No patient identifiers have been collected or transmitted."
      ];
      output.textContent = lines.filter((line, i) => line !== "" || i !== lines.length - 1).join("\n");
      exportButton.disabled = false;
    } catch (error) {
      lastReport = null;
      exportButton.disabled = true;
      output.classList.add("error");
      output.textContent = error.message;
    }
  });
  form.addEventListener("input", () => {
    lastReport = null;
    exportButton.disabled = true;
  });
  exportButton.addEventListener("click", () => {
    if (!lastReport) return;
    const blob = new Blob([JSON.stringify(lastReport, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url; a.download = "gi-bleed-scores.json";
    document.body.appendChild(a); a.click(); a.remove();
    URL.revokeObjectURL(url);
  });
}
