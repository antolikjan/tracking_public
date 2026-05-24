# ADVANCED-TESTING.md

## Goal

Add focused automated tests for the non-UI data analysis parts of the project.

The goal is to improve confidence that the dashboard's computed data, filters, event analysis, correlations, enrichment, and cache assumptions remain correct while keeping the project low-maintenance.

This plan should:

1. Test analysis behavior without Airtable credentials.
2. Prefer existing cached pickle data where useful.
3. Use small inline arrays/dataframes only for exact mathematical expectations.
4. Make core analytical assumptions explicit before encoding them in tests.
5. Avoid browser, Bokeh layout, and visual assertions.
6. Avoid committing private cache files or derived private fixtures.
7. Keep tests practical and readable.

---

## Current next milestone

Milestone 1 — Dashboard rationale and analytical assumptions inventory.

---

# Milestone 1 — Dashboard rationale and analytical assumptions inventory

Status: Not started.

## Objective

Document the dashboard's high-level analytical rationale before adding deeper tests.

The purpose is to ground later tests in what the dashboard is meant to help analyze, not just in the current implementation details.

## Scope

First summarize the purpose, motivation, and intended analytical logic of the dashboard independent of code structure. Then inspect the non-UI data and analysis code and document the assumptions that should guide later tests. Do not add or change tests in this milestone.

## Expected work

- Summarize the dashboard's high-level analytical purpose:
  - what kinds of health-tracking questions it is meant to help answer
  - what the daily tracking data represents conceptually
  - what role interventions, measurements, symptoms, relationships, and blood tests play
  - how comparisons, event-based analysis, correlations, and blood-test views fit into the overall reasoning
  - what kinds of conclusions the dashboard can support versus what should remain exploratory
- Use that high-level rationale as the frame for reviewing implementation-specific assumptions.
- Review the analysis-related code paths in:
  - `scripts.data`
  - `scripts.data_enrichment`
  - `scripts.comparison`
  - `scripts.event_based`
  - `scripts.correlations`
  - `scripts.blood_tests`
  - relationship metadata code only where it affects analysis decisions
- Summarize assumptions around:
  - date-indexed daily tracking data
  - missing values and default values
  - valid acquisition windows
  - numeric versus string/enum/bool fields
  - filtering and smoothing semantics
  - cross-correlation semantics
  - event-triggered averages and before/after event comparisons
  - correlation ranking, lag direction, p-values, and minimum sample sizes
  - blood-test table shape and date handling
  - category and metadata consistency
- Identify any assumptions that are unclear, surprising, or risky.
- Propose which assumptions should become deterministic unit tests and which should become cache-backed contract tests.
- Do not edit production code.
- Do not add tests yet.
- Let the user approve or modify the rationale and assumptions before Milestone 2 starts.

## Validation

No code validation required for this documentation-only milestone.

Optional sanity command:

    python -m pytest

## Done when

- The dashboard rationale is documented in this file.
- The analytical assumptions are documented in this file and grounded in that rationale.
- Unclear or risky assumptions are called out explicitly.
- The user has approved or modified the rationale and assumptions.
- Later testing milestones can refer back to the approved rationale and assumptions.

---

# Milestone 2 — Core analysis function tests

Status: Not started.

## Objective

Add direct tests for the pure or near-pure data analysis helpers, using the approved analytical assumptions from Milestone 1 as the source of truth.

## Scope

Focus on functions whose correctness can be asserted without Bokeh models, Airtable, or private data values.

## Expected work

- Add tests for `scripts.data` helpers:
  - `both_valid`
  - `data_aquisition_overlap`
  - `data_aquisition_overlap_non_nans`
  - `cross_corr`
  - `filter_data`
  - `event_weighted_average`
  - `event_triggered_change`
  - `convert_to_dataframe`
- Add tests for `scripts.data_enrichment.enrich_data`.
- Add tests for `special_preprocessing_rules` where a small dataframe can express the expected Fitbit invalidation behavior.
- Use small inline numpy arrays/dataframes for exact expected outputs.
- Cover NaN handling explicitly.
- Cover edge cases that are likely to affect analysis correctness.
- Do not require local cache files for these tests.
- Do not call Airtable.
- Do not test Bokeh layout or rendered UI.
- Do not refactor production code unless a tiny test seam is clearly needed and approved.

## Validation

    python -m pytest tests/test_analysis_helpers.py -q
    python -m pytest

## Done when

- Core analysis helper behavior is covered by deterministic tests.
- Tests run without Airtable credentials and without local cache files.
- Failures identify the specific analysis helper that regressed.
- Existing dashboard behavior is unchanged.

---

# Milestone 3 — Cache-backed analysis contract tests

Status: Not started.

## Objective

Add lightweight tests that the cached real data remains compatible with the approved analytical assumptions from Milestone 1.

## Scope

Use local pickle cache files to validate data shape and high-value analytical invariants without asserting private health values.

## Expected work

- Reuse the existing cache-loading test helpers or consolidate them only if it keeps tests simpler.
- Add cache-backed tests for dataframe and metadata contracts used by analysis code:
  - dataframe index is date-like and sorted
  - metadata contains required fields for analyzed columns
  - category mappings reference columns that exist in the dataframe
  - numeric analysis columns can be converted or consumed as numeric arrays
- Add sanity tests that selected cached columns can pass through:
  - filtering
  - overlap detection
  - cross-correlation when enough valid data exists
  - event-based analysis helpers when enough valid event data exists
- Add blood-test cache structure checks focused on analysis readiness, not exact values.
- Skip gracefully when optional local cache files are missing.
- Avoid asserting exact personal measurements.
- Avoid committing cache files or generated fixtures.
- Do not add browser tests or Bokeh UI interaction tests.
- Do not broaden into warning cleanup unless it blocks these tests.

## Validation

    python -m pytest tests/test_analysis_helpers.py tests/test_cached_analysis_contracts.py -q
    python -m pytest

## Done when

- Cached data contract failures produce clear messages.
- The tests catch broken cache shape or analysis-incompatible data before UI tests fail.
- No Airtable credentials are required.
- No private health data is committed.
- Existing dashboard behavior is unchanged.
