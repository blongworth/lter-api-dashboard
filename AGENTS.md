# AGENTS.md

Guidance for AI coding agents working in this repository.

## Project

Streamlit dashboard for exploring NES-LTER cruises: underway observations, CTD
sensor profiles, CTD bottle chemistry, nutrients, and chlorophyll. Data comes
from the public NES-LTER API (`https://nes-lter-api.whoi.edu/api`, no
credentials) and, for bathymetry masking, the public GEBCO OPeNDAP service.
See `README.md` for the user-facing overview of views and endpoints.

## Setup and running

```bash
uv sync
uv run streamlit run main.py
```

`requirements.txt` is kept in sync for non-uv installs (`pip install -r
requirements.txt`). If you add/remove a dependency, update both
`pyproject.toml` and `requirements.txt`.

## Checks

Run these before considering a change done:

```bash
uv run pytest
uv run ruff check .
```

There is no type checker configured. There is no browser/UI test harness —
after any UI-affecting change, actually run the app (`uv run streamlit run
main.py`) and click through the affected view; don't rely on pytest/ruff
alone to confirm UI behavior. The `developing-with-streamlit` skill is
installed under `.claude/skills` / `.agents/skills` — use it for any Streamlit
work (widgets, layout, caching, theming).

## Structure

```text
main.py                 Streamlit entry point: sidebar controls, routing to views
dashboard/config.py     API base URLs, DatasetSpec/DATASET_SPECS, column groupings
dashboard/data.py       Cached API loaders (st.cache_data) and type normalization
dashboard/analysis.py   Bathymetry lookup, interpolation, and masking for sections
dashboard/views.py      Streamlit rendering for each view (track, sections, profiles, data, metadata)
tests/                  Pure-function regression tests for data.py and analysis.py
```

Keep this layering: `data.py` fetches/caches/normalizes, `analysis.py` does
numeric transforms, `views.py` renders, `main.py` wires sidebar state to
views. Don't put Streamlit calls (`st.*`) in `data.py` or `analysis.py` other
than caching decorators — those two modules should stay pure/testable.

## Conventions

- Polars (`pl`), not pandas, for all dataframe work.
- New datasets are added as a `DatasetSpec` entry in
  `dashboard/config.py::DATASET_SPECS`, not hardcoded in views.
- Expensive/network calls (`dashboard/data.py` loaders, GEBCO fetches in
  `dashboard/analysis.py`) must go through `st.cache_data`/`st.cache_resource`
  with bounded ttl/maxsize — this is a deliberate pattern, don't remove
  caching or fetch uncached data in a hot render path.
- Tests target pure functions only (`tests/test_data.py`,
  `tests/test_analysis.py`); there's no Streamlit app-testing setup, so new
  logic that can be extracted into a plain function should be, for
  testability.
- Follow existing formatting (ruff-enforced); run `uv run ruff check .` (and
  `ruff format` if reformatting) rather than hand-matching style.

## Out of scope / be careful

- Don't add API credentials or auth — the NES-LTER API and GEBCO service are
  both public and unauthenticated by design.
- Don't remove the bounded caching around GEBCO/OPeNDAP calls — they're slow
  and only needed for section-view bathymetry masking.
