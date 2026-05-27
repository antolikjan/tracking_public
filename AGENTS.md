# AGENTS.md

## Project context

This repository is a personal Python dashboard for analyzing and visualizing health-tracking data.

Current architecture:
- Production data source: Airtable
- Local cached data: pickle files under locals/
- Web frontend: Bokeh Server
- Data handling: pandas
- Analysis: numpy/scipy

The current goal is to modernize the project enough that it runs on a current Python/Bokeh stack and has basic automated tests.

This is a low-maintenance personal project. Prefer practical, minimal changes over enterprise-style architecture.

## Hard constraints

- Keep the project Python-based.
- Keep the frontend web-based.
- Do not migrate to Panel unless explicitly requested.
- Do not rewrite the app unless there is no smaller safe option.
- Preserve existing dashboard behavior and analysis.
- Tests must not require Airtable credentials.
- Prefer using existing cached pickle data for tests.
- Do not commit private health-data cache files.
- Do not add elaborate synthetic fixture systems unless explicitly requested.
- Do not change dependency-management strategy unless needed for the current milestone.

## Local environment

Use the existing virtual environment:

    source ~/venvs/tracking/bin/activate

Prefer commands like:

    python -m pytest
    python -m pip install ...
    python -m bokeh serve main.py

If shell activation is unreliable, use the venv Python directly:

    ~/venvs/tracking/bin/python -m pytest
    ~/venvs/tracking/bin/python -m pip install ...
    ~/venvs/tracking/bin/python -m bokeh serve main.py

Do not create a new virtual environment unless explicitly asked.

## Research

Internet access may be used when helpful, especially for:
- Bokeh migration documentation
- pytest documentation
- Playwright documentation
- dependency/version compatibility

Prefer official documentation and release notes.