# MIGRATION-PLAN.md

## Goal

Modernize the personal health dashboard so that it:

1. Can be tested locally without Airtable.
2. Has useful automated tests before the Bokeh migration.
3. Can be upgraded from Bokeh 2.4.x to Bokeh 3.x incrementally.
4. Has browser-level smoke tests for the web frontend.
5. Remains simple enough for a low-maintenance personal project.

This is not intended to become an enterprise-grade application. The goal is practical reliability with minimal unnecessary architecture.

The project currently runs as a Bokeh Server app and the README documents Bokeh 2.4.3 as the current pinned Bokeh version.

---

## Current next milestone

Milestone 9 — Migrate blood-test views.

---

# Milestone 1 — Cached-data pytest foundation

Status: Done.



## Review note

Files changed: `scripts/data.py`, `tests/test_cached_data.py`, `README.md`, `MIGRATION-PLAN.md`.
Commands run: `~/venvs/tracking/bin/python -m pip install pytest`; `~/venvs/tracking/bin/python -m pytest`.
Test results: 3 passed, 16 warnings.
Remaining risks: tests currently emit existing Bokeh, pandas/date parsing, fragmentation, runtime, and attribute-assignment warnings; browser-level coverage and Bokeh upgrade work remain for later milestones.

## Accepted note

Accepted after review. Cache-backed pytest foundation is in place; next work should continue with component inventory and baseline construction tests.

## Objective

Make the project testable without Airtable by using the existing local pickle cache.

## Scope

This milestone creates the minimum test foundation. It should not upgrade Bokeh and should not change dashboard behavior.

## Expected work

- Add pytest if missing.
- Use existing pickle cache files under locals/ as the main test data source.
- Ensure tests do not require Airtable credentials.
- Ensure tests do not call Airtable.
- Add tests that skip gracefully if cache files are missing.
- Add a test that verifies cached data can be loaded.
- Add a test that verifies the current app can be constructed from cached data.
- Add a small app/data factory only if needed to avoid Airtable during tests.
- Add only small unit tests for obvious pure functions if they are easy.
- Document how to regenerate the local cache manually.
- Do not add Playwright yet.
- Do not upgrade Bokeh yet.
- Do not migrate to Panel.
- Do not do broad refactoring.

## Validation

    python -m pytest

## Done when

- python -m pytest runs.
- Cache-based tests pass when local cache files exist.
- Cache-based tests skip cleanly when local cache files are missing.
- No Airtable credentials are needed for tests.
- Dashboard behavior is unchanged.

---

# Milestone 2 — Component inventory and baseline construction tests

Status: Done.

## Component inventory

- App shell: `scripts.create_app.create_app(df, metadata, categories, relationships, bldt)` builds a Bokeh `Tabs` container.
- Active top-level tabs:
  - Comparison: `scripts.comparison.ComparisonPanel(...).compose_panel()`
  - Event Based Analysis: `scripts.event_based.EventBasedAnalysisPanel(...).compose_panel()`
  - Correlations: `scripts.correlations.panel(...)`
  - Relationships: `scripts.relationships.panel(...)`
  - BloodTests: `scripts.blood_tests.BloodTests(...).compose_panel()`
- Shared UI/helper code:
  - `scripts.ui_framework.analysis_panel.AnalysisPanel` provides shared panel composition, update dispatch, and widget registration.
  - `scripts.ui_framework.paired_analysis.PairedAnalysis` provides the shared two-variable selector/data-source base used by comparison and event-based views.
- Inactive/commented app area: `scripts.bloodtests_correlations.BloodTestsCorrelationsPanel` is migrated at module level but not currently included in `create_app.py`; manual review found it needs more work before being displayed.
- Correlations construction is isolated at panel-build level only; expensive correlation recalculation is still user-triggered by the Recalculate button and is not exercised by this smoke milestone.

## Review note

Files changed: `tests/test_component_construction.py`, `MIGRATION-PLAN.md`.
Commands run: `~/venvs/tracking/bin/python -m pytest`.
Test results: 10 passed, 56 warnings.
Remaining risks: tests still rely on local cached pickle files for component construction; existing Bokeh, pandas/date parsing, fragmentation, runtime, and attribute-assignment warnings remain; browser-level coverage and Bokeh upgrade compatibility are left for later milestones.

## Accepted note

Accepted after review. Component inventory and cache-backed construction smoke coverage are in place; next work should add the baseline browser smoke test on the current Bokeh stack.

## Objective

Map the dashboard into testable components before upgrading Bokeh.

The point of this milestone is to avoid treating the Bokeh migration as one huge opaque task. Codex should identify the main dashboard windows/tabs/components and add baseline tests for constructing them under the current Bokeh 2.4.x stack.

## Scope

Inventory and test the current app structure. Do not upgrade Bokeh.

## Expected work

- Inspect create_app.py and the modules under scripts/.
- Identify the top-level dashboard tabs/windows/pages.
- Map each top-level UI area to the module/function that creates it.
- Identify shared Bokeh/UI helper code, especially under scripts/ui_framework/.
- Add a short component inventory section to this file.
- Add construction tests for individual dashboard components where practical.
- Add tests in priority order:
  1. shared UI/helper code
  2. create_app/app shell/tab construction
  3. relationships-related views
  4. event-based/comparison views
  5. correlations views
  6. blood-test views
- Keep tests smoke-level. The goal is to verify that components construct successfully from cached data, not to prove every visual detail.
- If a component is too hard to isolate, document why and leave it covered by the full-app construction test.
- Do not upgrade Bokeh.
- Do not migrate to Panel.
- Avoid broad refactoring unless needed to create a small test seam.

## Validation

    python -m pytest

## Done when

- The main dashboard components are inventoried.
- Important components have construction tests where practical.
- The test suite gives useful coverage before any Bokeh upgrade.
- Any components that cannot be isolated are documented.
- Dashboard behavior is unchanged.

---

# Milestone 3 — Baseline browser smoke test on current Bokeh

Status: Done.

## Review note

Files changed: `tests/test_browser_smoke.py`, `MIGRATION-PLAN.md`.
Commands run: `~/venvs/tracking/bin/python -m pip install pytest-playwright`; `~/venvs/tracking/bin/python -m playwright install chromium`; `~/venvs/tracking/bin/python -m pytest tests/test_browser_smoke.py -q`; `~/venvs/tracking/bin/python -m pytest`.
Test results: 11 passed, 67 warnings.
Remaining risks: browser smoke coverage depends on local cached pickle files and a Playwright Chromium install; missing cache files or browser binaries now fail the browser smoke test and are documented in README setup instructions. Existing Bokeh, Tornado, pandas/date parsing, fragmentation, runtime, and attribute-assignment warnings remain for later milestones.

## Objective

Add a minimal browser-level smoke test before the Bokeh migration.

This gives a baseline for the current working app before dependencies are upgraded.

## Scope

Use Playwright with pytest to verify that the current Bokeh 2.4.x app can start and load in a browser using cached data.

## Expected work

- Add Python Playwright / pytest integration if missing.
- Add a test-only way to start the dashboard using cached data.
- Open the local dashboard in a browser.
- Verify the page loads.
- Verify the main app container or document title is present.
- Verify top-level tabs/pages are visible if selectors are accessible.
- Click through top-level tabs/pages if feasible.
- Capture serious browser console errors if practical.
- Keep this test smoke-level.
- Avoid screenshot/pixel-perfect testing.
- If loopback networking is not working in Codex, document the issue and make the test runnable manually by the user.

## Validation

    python -m pytest

Possible one-time setup:

    python -m playwright install

## Done when

- There is at least one browser smoke test for the current app.
- The test uses cached data, not Airtable.
- The test is useful but not brittle.
- If it cannot run automatically in the Codex environment, the reason is documented.

---

# Milestone 4 — Bokeh compatibility preparation without upgrading

Status: Done.

## Review note

Files changed: `scripts/ui_framework/bokeh_compat.py`, `scripts/ui_framework/analysis_panel.py`, `scripts/correlations.py`, `scripts/relationships.py`, `scripts/create_app.py`, `tests/test_component_construction.py`, `MIGRATION-PLAN.md`.
Commands run: `~/venvs/tracking/bin/python -m pytest`.
Test results: 11 passed, 67 warnings.
Remaining risks: Bokeh has not been upgraded yet; compatibility has only been validated under the current Bokeh 2.4.x stack. The main confirmed Bokeh 3 hotspot addressed here is `Panel` renamed to `TabPanel`; active `width`/`height` and `legend_label` usage already appears compatible. Existing Bokeh, Tornado, pandas/date parsing, fragmentation, runtime, and attribute-assignment warnings remain for later milestones.

## Accepted note

Accepted after review. Bokeh tab-panel compatibility preparation is in place; next work should perform the Bokeh 3.x dependency upgrade and fix app-shell/shared-UI breakages.

## Objective

Prepare the codebase for Bokeh 3.x while still running on Bokeh 2.4.x.

This milestone should reduce the size of the eventual dependency bump.

## Scope

Make safe compatibility-oriented changes that can be tested under the current Bokeh version.

## Expected work

- Review official Bokeh 2.x to 3.x migration documentation.
- Identify Bokeh APIs used across the codebase that are likely to break.
- Prefer small compatibility helpers where useful.
- Reduce repeated direct usage of known-breaking APIs if practical.
- Focus on shared/global issues first:
  - Panel versus TabPanel tab construction
  - plot_width / plot_height versus width / height
  - legend argument changes
  - shared layout helper changes
  - common widget callback patterns
  - shared CDSView/filter usage
- Do not upgrade Bokeh yet.
- Do not change analysis behavior.
- Keep all existing tests passing.

## Validation

    python -m pytest

## Done when

- Known Bokeh migration hotspots are documented.
- Shared compatibility changes are in place where practical.
- Tests still pass under Bokeh 2.4.x.
- The actual Bokeh upgrade is smaller and less risky.

---

# Milestone 5 — Upgrade Bokeh and fix app shell/shared UI

Status: Done.

## Review note

Files changed: `README.md`, `scripts/ui_framework/bokeh_compat.py`, `scripts/ui_framework/analysis_panel.py`, `scripts/create_app.py`, `scripts/correlations.py`, `scripts/relationships.py`, `scripts/comparison.py`, `scripts/event_based.py`, `scripts/bloodtests_correlations.py`, `tests/test_component_construction.py`, `MIGRATION-PLAN.md`.
Commands run: `~/venvs/tracking/bin/python -m pip install 'bokeh>=3,<4'`; `~/venvs/tracking/bin/python -m pytest tests/test_cached_data.py::test_app_constructs_from_cached_data tests/test_component_construction.py::test_app_shell_constructs_expected_tabs tests/test_component_construction.py::test_comparison_panel_constructs -q`; `~/venvs/tracking/bin/python -m pytest tests/test_browser_smoke.py::test_bokeh_app_loads_in_browser -q`; `~/venvs/tracking/bin/python -m pytest`; `~/venvs/tracking/bin/python -m bokeh serve main.py`.
Test results: Bokeh upgraded to 3.9.0; full pytest suite passes with 11 passed and 63 warnings; `bokeh serve main.py` starts successfully when local port binding is allowed.
Remaining risks: `bokeh serve main.py` startup was validated without opening the Airtable-backed app session; browser smoke coverage uses cached data. Existing pandas/date parsing, fragmentation, runtime, Tornado event-loop, and pandas attribute-assignment warnings remain. Page-specific visual behavior still needs review in later migration milestones.

## Accepted note

Accepted after review. Bokeh 3.9.0 app-shell startup, cached-data construction tests, and browser smoke coverage are in place; next work should migrate relationships and core tracking views.

## Objective

Upgrade Bokeh to a current 3.x version and fix only the global/app-shell/shared-UI breakages first.

## Scope

This is the dependency bump milestone, but it should not try to fix every page-specific issue at once.

## Expected work

- Upgrade Bokeh to a current 3.x version.
- Update only closely related dependencies if required.
- Remove the temporary Bokeh 2/3 tab-panel compatibility helper once Bokeh 3.x is the supported runtime.
- Fix import errors and app startup errors.
- Fix create_app.py / tab construction.
- Fix shared UI helpers.
- Fix global layout issues.
- Get pytest collection working.
- Get the app shell to construct.
- Do not deeply migrate every dashboard page in this milestone unless the fix is trivial.
- If page-specific tests fail, group failures by component and record them for later milestones.

## Validation

    python -m pytest

Also attempt:

    python -m bokeh serve main.py

## Done when

- The project imports under Bokeh 3.x.
- The test suite runs.
- Shared/app-shell tests pass.
- Remaining failures are grouped by dashboard area.
- The next page/component migration milestone is clearly identified.

---

# Milestone 6 — Migrate relationships and core tracking views

Status: Done.

## Review note

Files changed: `scripts/relationships.py`, `tests/test_component_construction.py`, `MIGRATION-PLAN.md`.
Commands run: `~/venvs/tracking/bin/python -m pytest tests/test_component_construction.py::test_relationships_panel_constructs -q`; `~/venvs/tracking/bin/python -m pytest tests/test_browser_smoke.py::test_bokeh_app_loads_in_browser -q`; `~/venvs/tracking/bin/python -m pytest tests/test_component_construction.py::test_relationships_panel_constructs tests/test_component_construction.py::test_relationship_filters_update_table_source tests/test_component_construction.py::test_relationship_remove_actions_use_selected_rows -q`; `~/venvs/tracking/bin/python -m pytest`.
Test results: relationship construction baseline passed; browser smoke passed; focused relationship tests passed with 3 passed and 6 warnings; full suite passed with 13 passed and 63 warnings.
Remaining risks: relationship coverage is still smoke-level and does not verify manual visual layout; existing Tornado event-loop, pandas/date parsing, fragmentation, runtime, and pandas attribute-assignment warnings remain for later milestones.

## Accepted note

Accepted after review. Relationship/core tracking view migration and focused callback coverage are in place; next work should migrate the event-based and comparison views.

## Objective

Fix Bokeh 3.x issues in the main relationship/tracking views.

## Scope

Focus on relationship-related dashboard components before moving to more specialized analytical pages.

## Expected work

- Migrate relationships.py.
- Migrate relationship_metadata.py only if UI-facing issues exist there.
- Fix Bokeh 3.x issues specific to these views.
- Keep fixes local where possible.
- Add or update construction tests for these views.
- Add or update browser smoke coverage if feasible.
- Do not work on blood-test or correlation pages unless required by shared code.

## Validation

    python -m pytest

## Done when

- Relationship/core tracking views construct under Bokeh 3.x.
- Related tests pass.
- Any remaining manual visual concerns are documented.

---

# Milestone 7 — Migrate event-based and comparison views

Status: Done.

## Review note

Files changed: `scripts/event_based.py`, `tests/test_component_construction.py`, `MIGRATION-PLAN.md`.
Commands run: `~/venvs/tracking/bin/python -m pytest tests/test_component_construction.py::test_comparison_panel_constructs tests/test_component_construction.py::test_event_based_panel_constructs -q`; `~/venvs/tracking/bin/python -m pytest tests/test_browser_smoke.py::test_bokeh_app_loads_in_browser -q`; `~/venvs/tracking/bin/python -m pytest tests/test_component_construction.py::test_comparison_panel_constructs tests/test_component_construction.py::test_comparison_panel_updates_filtered_and_bar_views tests/test_component_construction.py::test_event_based_panel_constructs tests/test_component_construction.py::test_event_based_panel_updates_reference_lines -q`; `~/venvs/tracking/bin/python -m pytest tests/test_component_construction.py -q`; `~/venvs/tracking/bin/python -m pytest`.
Test results: focused comparison/event-based tests passed with 4 passed and 27 warnings; component construction tests passed with 11 passed and 54 warnings; browser smoke passed with 1 passed and 9 warnings; full suite passed with 15 passed and 77 warnings.
Remaining risks: coverage is still smoke-level and does not verify manual visual layout; comparison bar-mode behavior depends on selected low-cardinality variables and is not deeply asserted; existing Tornado event-loop, pandas/date parsing, fragmentation, runtime, numpy, and pandas attribute-assignment warnings remain for later milestones.

## Accepted note

Accepted after review. Event-based and comparison view migration coverage is in place; next work should migrate the correlation views.

## Objective

Fix Bokeh 3.x issues in event-based and comparison dashboard views.

## Scope

Focus on event_based.py and comparison.py.

## Expected work

- Migrate event_based.py.
- Migrate comparison.py.
- Fix Bokeh 3.x layout, widget, callback, and plotting issues in these views.
- Add or update construction tests.
- Add or update browser smoke coverage if feasible.
- Do not work on blood-test/correlation pages unless required by shared code.

## Validation

    python -m pytest

## Done when

- Event-based and comparison views construct under Bokeh 3.x.
- Related tests pass.
- Any remaining manual visual concerns are documented.

---

# Milestone 8 — Migrate correlation views

Status: Done.

## Review note

Files changed: `scripts/bloodtests_correlations.py`, `tests/test_component_construction.py`, `MIGRATION-PLAN.md`.
Commands run: `~/venvs/tracking/bin/python -m pytest tests/test_component_construction.py::test_correlations_panel_constructs -q`; `~/venvs/tracking/bin/python -m pytest tests/test_component_construction.py::test_correlations_panel_constructs tests/test_component_construction.py::test_correlations_panel_exposes_table_and_controls tests/test_component_construction.py::test_correlations_table_filter_updates_source tests/test_component_construction.py::test_blood_tests_correlations_panel_constructs tests/test_component_construction.py::test_blood_tests_correlations_panel_updates_sources -q`; `~/venvs/tracking/bin/python -m pytest tests/test_component_construction.py -q`; `~/venvs/tracking/bin/python -m pytest`.
Test results: focused correlation tests passed with 5 passed and 30 warnings; component construction tests passed with 15 passed and 78 warnings; full suite passed with 19 passed and 101 warnings.
Remaining risks: coverage remains construction and callback smoke-level rather than manual visual review; the active correlations tab still does not exercise the expensive full recalculation in tests; `BloodTestsCorrelationsPanel` remains inactive/commented out in the app shell after manual review found the displayed view needs more work. Existing Tornado event-loop, pandas/date parsing, fragmentation, runtime, numpy, and blood-test table assignment warnings remain for later milestones.

## Accepted note

Accepted after review. Correlation view migration coverage is in place; next work should migrate the blood-test views.

## Objective

Fix Bokeh 3.x issues in correlation-related dashboard views.

## Scope

Focus on correlations.py and bloodtests_correlations.py.

## Expected work

- Migrate correlations.py.
- Migrate bloodtests_correlations.py.
- Fix Bokeh 3.x issues in plots, data sources, callbacks, selectors, and layouts.
- Add or update construction tests.
- Add or update browser smoke coverage if feasible.

## Validation

    python -m pytest

## Done when

- Correlation views construct under Bokeh 3.x.
- Related tests pass.
- Any remaining manual visual concerns are documented.

---

# Milestone 9 — Migrate blood-test views

Status: Not started.

## Objective

Fix Bokeh 3.x issues in blood-test dashboard views.

## Scope

Focus on blood_tests.py and any related blood-test UI code.

## Expected work

- Migrate blood_tests.py.
- Fix Bokeh 3.x issues in blood-test plots, layouts, widgets, and callbacks.
- Add or update construction tests.
- Add or update browser smoke coverage if feasible.

## Validation

    python -m pytest

## Done when

- Blood-test views construct under Bokeh 3.x.
- Related tests pass.
- Any remaining manual visual concerns are documented.

---

# Milestone 10 — Full app browser smoke test under Bokeh 3.x

Status: Not started.

## Objective

Verify the migrated app through the browser.

## Scope

Run the full dashboard under Bokeh 3.x using cached data and test the main frontend flow.

## Expected work

- Start the full dashboard using cached data.
- Open it in Playwright.
- Verify the main page loads.
- Verify all top-level tabs/pages are visible.
- Click through all major tabs/pages.
- Check for serious browser console errors.
- Keep the test smoke-level.
- Avoid screenshot/pixel-perfect assertions unless explicitly requested.

## Validation

    python -m pytest

## Done when

- Browser smoke tests pass under Bokeh 3.x.
- All major dashboard sections are visited at least once.
- Remaining manual visual-review items are documented.

---

# Milestone 11 — Final cleanup and run documentation

Status: Not started.

## Objective

Make the project easy to run and maintain at a lightweight personal-project level.

## Scope

Clean up only what is useful after the migration.

## Expected work

- Update README run instructions.
- Document environment activation.
- Document dependency installation.
- Document cache regeneration.
- Document test commands.
- Document browser test setup.
- Remove obsolete compatibility code only if clearly safe.
- Avoid unnecessary tooling churn.

## Validation

    python -m pytest
    python -m bokeh serve main.py

## Done when

- The project runs on the modernized stack.
- Tests pass.
- Basic browser smoke tests pass.
- The README explains how to run and test the project.

---

# Optional Milestone 12 — Panel evaluation

Status: Optional. Do not start unless explicitly requested.

## Objective

Decide whether moving the app shell from raw Bokeh Server to Panel is worthwhile.

## Scope

Evaluation only unless explicitly approved.

## Expected work

- Inspect whether the migrated Bokeh Server app is sufficient.
- Identify specific pain points Panel would solve.
- Create a tiny proof of concept only if useful.
- Do not rewrite the dashboard.
- Do not migrate analysis logic.

## Done when

There is a clear recommendation:

- keep raw Bokeh Server, or
- migrate only the app shell to Panel later.
