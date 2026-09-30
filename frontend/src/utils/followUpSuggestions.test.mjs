
import test from "node:test";
import assert from "node:assert/strict";

import { buildFollowUpSuggestions } from "./followUpSuggestions.mjs";

test("returns profit-related follow-ups", () => {
  const suggestions = buildFollowUpSuggestions(
    {},
    "Show profit by category"
  );

  assert.equal(suggestions.length, 3);

  assert.ok(
    suggestions.includes("Which category has the highest profit?")
  );

  assert.ok(
    suggestions.includes("Which region has the lowest profit?")
  );
});

test("returns sales-related follow-ups", () => {
  const suggestions = buildFollowUpSuggestions(
    {},
    "Show sales by product"
  );

  assert.equal(suggestions.length, 3);

  assert.ok(
    suggestions.includes("Which category has the highest sales?")
  );

  assert.ok(
    suggestions.includes("Show the monthly sales trend")
  );
});

test("uses category context from the question", () => {
  const suggestions = buildFollowUpSuggestions(
    {},
    "Show products"
  );

  assert.ok(
    suggestions.includes("Which products have the highest profit?")
  );

  assert.equal(suggestions.length, 3);
});

test("uses region context from the question", () => {
  const suggestions = buildFollowUpSuggestions(
    {},
    "Show sales by region"
  );

  assert.ok(
    suggestions.includes("Which region has the highest sales?")
  );

  assert.equal(suggestions.length, 3);
});

test("uses the default suggestions for a general question", () => {
  const suggestions = buildFollowUpSuggestions(
    {},
    "Give me an overview"
  );

  assert.deepEqual(suggestions, [
    "Which category has the highest profit?",
    "Which region has the highest sales?",
    "Show the monthly sales trend",
  ]);
});

test("excludes the current question even when punctuation differs", () => {
  const suggestions = buildFollowUpSuggestions(
    {},
    "Which category has the highest profit?!"
  );

  assert.ok(
    !suggestions.some(
      (suggestion) =>
        suggestion
          .trim()
          .toLowerCase()
          .replace(/[?!.\s]+$/, "") ===
        "which category has the highest profit"
    )
  );

  assert.equal(suggestions.length, 3);
});

test("uses governed query metadata to determine context", () => {
  const result = {
    evidence: {
      governed_query: {
        measures: ["profit"],
        dimensions: ["category"],
      },
    },
  };

  const suggestions = buildFollowUpSuggestions(
    result,
    "Show performance"
  );

  assert.ok(
    suggestions.includes("Which region has the lowest profit?")
  );

  assert.equal(suggestions.length, 3);
});

test("returns unique suggestions", () => {
  const suggestions = buildFollowUpSuggestions(
    {},
    "Give me an overview"
  );

  assert.equal(suggestions.length, new Set(suggestions).size);
});