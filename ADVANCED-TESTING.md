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

Milestone 2 — Core analysis function tests.

---

# Milestone 1 — Dashboard rationale and analytical assumptions inventory

Status: Done.

## Dashboard rationale

The dashboard is an exploratory personal health-tracking tool. Its main purpose is to help compare daily observations, interventions, symptoms, wearable measurements, and blood-test markers so that possible relationships can be noticed and inspected. It can support pattern-finding and hypothesis generation, but it should not be treated as proving medical or causal conclusions.

The daily tracking dataframe represents one row per calendar day. Columns represent measurements, symptoms, behaviors, interventions, and computed enrichments. The analysis assumes this daily index is the shared time base for comparison, filtering, event-based views, and correlations. Missing values are meaningful: they usually mean a value was not recorded, was outside a valid acquisition window, or was invalidated by preprocessing.

Interventions are variables that may plausibly precede or affect other tracked values. Measurements and symptoms are observed outcomes or context variables. Relationships metadata records user decisions about which pairs are ignored or blacklisted, so correlation displays can hide known-unhelpful or analytically inappropriate pairs. Blood tests are separate, sparse date-indexed tables used for marker inspection rather than daily time-series correlation in the active dashboard.

The comparison view is intended for focused pairwise inspection: raw values, optional smoothing, simple shift inspection, scatter/linear fit summaries, cross-correlation, and categorical bar comparisons. The event-based view treats non-default values in one variable as events and inspects average behavior in another variable around those events and before/after windows. The correlations view performs a broad scan across variable pairs, including one-day lag alternatives and smoothed accumulation-style checks, then ranks and filters results for inspection. Blood-test views present biomarker values in date-indexed tables with range-based coloring based on metadata.

Because the project is personal and exploratory, later tests should verify that these computations remain internally consistent and interpretable. Tests should not encode claims that a relationship is causal, clinically significant, or stable across time.

## Analytical assumptions inventory

- Daily data is expected to be date-indexed, sorted, and conceptually consecutive after loading from Airtable. Cache-backed tests should verify that cached data remains date-like and sorted; deterministic tests can cover helper behavior independent of the index.
- Airtable loading inserts missing days before caching, converts enum and bool fields to numeric forms where metadata says they are analyzable, replaces Airtable special NaN dictionaries with plain NaN, applies custom preprocessing, drops string or ignored columns, applies defaults, and then masks dates outside each variable's valid record window.
- Defaults are applied only after preprocessing and before valid-window masking. A non-NaN metadata default means missing values become that default; a NaN default leaves missing values as NaN. Tests should treat this as an important contract because it changes the difference between "not recorded" and "recorded absence".
- Valid acquisition windows are inclusive/exclusive as currently implemented by label slicing: values up to `Start of valid records` are set to NaN, and values from `End of valid records` onward are set to NaN. This boundary behavior is worth making explicit in a future deterministic or cache-backed test before changing it.
- Fitbit-specific preprocessing assumes `Steps < 500` means the device was likely not worn that day, and all Fitbit-category values for that row should become NaN. This is a domain assumption, not a general data-cleaning rule.
- Enrichment currently adds `Week day`, `Weekend`, and `Month` columns to the measurements category and metadata. These are computed from the dataframe index and should remain deterministic. The metadata rows inserted by enrichment are minimal and do not include every field used by all analysis code.
- Analysis helpers assume numeric numpy arrays or dataframe columns. String fields are excluded during loading and correlation scanning. Enum and bool fields are represented numerically before analysis, so later tests should distinguish numeric encoding correctness from interpretation of category labels.
- `both_valid` returns paired values only where neither input is NaN. It assumes numpy-style arrays and preserves the original paired order.
- `data_aquisition_overlap` finds the span between the first and last non-NaN observations in each input and returns the overlapping start/end indices. `data_aquisition_overlap_non_nans` then removes pairwise NaNs inside that overlap. The returned end index is used as a Python slice stop, so boundary behavior should be tested carefully.
- `filter_data` supports `Gauss`, `PastGauss`, and `FutureGauss`. It computes a kernel for display and a weighted moving average that ignores NaNs via masked arrays. The past/future names describe asymmetric kernel direction around each output point and should be pinned with small-array tests.
- `cross_corr` uses the overlapping acquisition window, shortens even-length windows by one to keep a symmetric lag axis, centers each filtered series by its mean, normalizes by vector magnitude, and returns `None` when there is no positive overlap. Tests should cover the odd-length lag axis and NaN/empty behavior.
- Pairwise comparison uses only positions where both selected processed variables are valid for scatter/regression. It reports linear regression only when more than 10 paired points are available in `update_plots`; cross-correlation is only shown when the selected overlapping processed window has no NaNs.
- Categorical-style bar comparison is triggered when one selected variable has fewer than 13 distinct values and the "Show bars" toggle is active. It uses group means, SEM, and pairwise t-tests as exploratory summaries.
- Event-triggered averages treat non-NaN values in the event vector as weighted events. The output is a mean window over the response vector divided by the mean event value, with response NaNs ignored.
- Event-triggered change treats non-default, non-NaN event values as events. For each event it compares the mean response before and after the event over a fixed window, then runs a Wilcoxon signed-rank test on the resulting pairs. The current helper assumes at least one valid before/after pair; empty results are a risk to document and later test.
- Correlation scanning excludes metadata units marked `string`, requires more than 20 pairwise observations and non-zero variance for no-shift and one-day shifted regressions, then chooses the available shift with the lowest p-value. The labels `Var1 -> Var2`, `Var2 -> Var1`, and `==` are exploratory lag labels, not causality claims.
- Accumulation analysis in correlations uses past Gaussian smoothing with sigmas `[2, 4, 8, 16, 32, 64, 128, 256]`, requires at least 5 overlapping values and non-negligible variance, and records the best p-value across both directions and sigmas.
- Correlation table filtering is controlled by maximum p-value, optional selected-variable filtering, and relationship ignore/blacklist filtering. Relationship metadata blacklists pairs where both variables are interventions by default, and ignore/blacklist changes are symmetric.
- Blood-test data is a dictionary of named views, each a date-indexed dataframe loaded from selected Airtable fields and cached separately. The active view expects a `Minerals` table by default.
- Blood-test range coloring depends on metadata rows for marker names and the columns `Normal value min`, `Normal value max`, `Optimal value min`, and `Optimal value max`. Missing metadata yields `NA`; missing or partial ranges have several branch-specific interpretations that should be deterministic if later tested.
- Category metadata is central to analysis decisions: it determines UI variable choices, string/ignored field exclusion, Fitbit invalidation, intervention pair blacklisting, and enrichment placement. Cache-backed tests should verify that categories and metadata remain consistent with dataframe columns.

## Unclear or risky assumptions

- The valid-window boundary semantics may be surprising: start dates are masked through the start label and end dates are masked from the end label onward. This may or may not be the intended inclusivity.
- `data_aquisition_overlap_non_nans` slices with `start:end`, so the final non-NaN overlap point is excluded. Existing analysis may rely on this accidentally.
- `event_triggered_change` fails when no valid event windows exist because it unpacks an empty result list. The UI likely avoids this only when real selected data has enough events.
- `event_weighted_average` divides by `nanmean(a)`, so event vectors with mean zero or all-NaN values can produce unstable results.
- Correlation p-value minimization across no-shift and shifted variants, plus many pair scans, is exploratory and multiple-comparison-prone. Tests should verify mechanics, not statistical validity of discovered relationships.
- Relationship metadata is persisted to `relationship_metadata` in the repository root. Tests should avoid mutating the real file unless a temporary path or explicit seam is approved later.
- Enrichment metadata rows omit some fields expected by other parts of the metadata table. This is acceptable only if downstream code does not require those fields for enriched columns.
- Blood-test `color_mapper(metadata, col_name, cell_value)` passes its arguments to `classify_range(metadata, marker, col)` in a way that makes the call-site naming easy to misread. Later tests should encode the observed intended argument order.

## Future test classification

Deterministic unit tests in Milestone 2 should cover small-array or small-dataframe behavior for:

- `both_valid`
- `data_aquisition_overlap`
- `data_aquisition_overlap_non_nans`
- `cross_corr`
- `filter_data`
- `event_weighted_average`
- `event_triggered_change`
- `convert_to_dataframe`
- `enrich_data`
- Fitbit invalidation in `special_preprocessing_rules`
- Blood-test range helpers if they are added to Milestone 2 by approval later

Cache-backed contract tests in Milestone 3 should cover:

- cached daily dataframe index is date-like, sorted, and compatible with daily analysis
- cached metadata has required fields for analyzed columns
- category mappings reference existing dataframe columns
- analyzed columns are numeric-consumable after loading and enrichment
- selected cached columns can pass through filtering, overlap, cross-correlation, and event helpers when enough valid data exists
- blood-test cache is a dictionary of date-indexed dataframes with expected view/table shape
- relationship metadata references variables consistently and can filter correlation pairs without missing-index failures

## Review note

Files changed: `ADVANCED-TESTING.md`.
Commands run: `~/venvs/tracking/bin/python -m pytest`.
Test results: 20 passed, 103 warnings.
Remaining risks: this milestone documents current analytical intent and assumptions only; it does not add tests, fix risky edge cases, or validate statistical interpretation. Existing warnings remain from Tornado event loop handling, dataframe fragmentation, ambiguous date parsing, empty-slice means, and masked-array division.

## Accepted note

Accepted after review. Dashboard rationale and analytical assumptions are now documented; next work should add deterministic tests for core analysis helpers.

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
