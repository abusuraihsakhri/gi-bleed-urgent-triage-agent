"use strict";
const test = require("node:test");
const assert = require("node:assert/strict");
const {scoreGBS, scoreAIMS65} = require("./app.js");
const normal = {bun: 4, hemoglobin: 15, sbp: 130, heartRate: 75,
  sex: "male", melena: false, syncope: false, hepaticDisease: false,
  cardiacFailure: false, historyConfirmed: true};

test("GBS zero and one satisfy the screening cutoff only", () => {
  assert.equal(scoreGBS(normal).score, 0);
  assert.equal(scoreGBS(normal).meetsVeryLowRiskCriterion, true);
  assert.equal(scoreGBS({...normal, melena: true}).score, 1);
  assert.equal(scoreGBS({...normal, syncope: true}).meetsVeryLowRiskCriterion, false);
});
test("GBS maximum and published numeric boundaries", () => {
  assert.equal(scoreGBS({...normal, bun: 30, hemoglobin: 8, sbp: 80,
    heartRate: 110, melena: true, syncope: true, hepaticDisease: true,
    cardiacFailure: true}).score, 23);
  assert.equal(scoreGBS({...normal, bun: 25}).components.bun, 4);
  assert.equal(scoreGBS({...normal, bun: 25.01}).components.bun, 6);
  assert.equal(scoreGBS({...normal, hemoglobin: 12.95}).components.hemoglobin, 1);
  assert.equal(scoreGBS({...normal, hemoglobin: 13}).components.hemoglobin, 0);
  assert.equal(scoreGBS({...normal, heartRate: 100}).components.heartRate, 1);
});
test("No absent-feature assumptions and invalid numerics", () => {
  assert.throws(() => scoreGBS({...normal, historyConfirmed: false}));
  assert.throws(() => scoreGBS({...normal, bun: NaN}));
  assert.throws(() => scoreGBS({...normal, sex: "other"}));
});
test("AIMS65 age, blood pressure and INR boundaries", () => {
  const base = {albumin: 4, inr: 1.5, sbp: 91, age: 65, mentalStatusAltered: false};
  assert.equal(scoreAIMS65(base).score, 0);
  assert.equal(scoreAIMS65({...base, age: 66}).score, 1);
  assert.equal(scoreAIMS65({...base, sbp: 90}).score, 1);
  assert.equal(scoreAIMS65({...base, inr: 1.51}).score, 1);
  assert.equal(scoreAIMS65({...base, albumin: 2.9, inr: 2,
    sbp: 80, age: 70, mentalStatusAltered: true}).score, 5);
});
