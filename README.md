# NES-LTER API dashboard

Streamlit dashboard for exploring NES-LTER cruises, underway observations, CTD sensor profiles, CTD bottle chemistry, nutrients, and chlorophyll.

## Run

```bash
uv sync
uv run streamlit run main.py
```

The app is also compatible with the requirements file:

```bash
pip install -r requirements.txt
streamlit run main.py
```

The default cruise is `EN617`. The API is public; no credentials are required.

## Views

**Explore** stacks the three plots on one page, each with its own sidebar controls:

1. **Cruise track** — underway data by default, optional shallowest-bottle markers, and an Esri ocean basemap.
2. **Sections** — depth sections by latitude, longitude, or cast, from CTD bottles, continuous CTD casts, nutrients, and/or chlorophyll, with optional local interpolation and GEBCO bathymetry masking.
3. **Profiles** — single-cast or station profiles. For CTD data, choose bottle chemistry, cast sensor data, or both. Profile tables and endpoint templates appear below each plot.

The three are linked: clicking a point on the map or in the section plot selects that cast in the profile plot below. Cast and bottle points identify themselves directly; underway points carry no cast id, so the nearest cast is used. The profile selectors stay available for picking a cast by hand.

The other two views are:

- **Data** — loaded endpoint tables with their API sources.
- **Metadata** — optional CTD metadata, cruise documentation, dataset readmes, and underway column definitions.

CTD cast profiles use `ctd/cast/{cruise}/{cast}.csv`; bottle profiles use `ctd/bottles/{cruise}.csv`. Depth is taken from each selected endpoint's `depsm` field.

## Structure

```text
main.py                 Streamlit entry point and routing
dashboard/config.py     Endpoint and dataset specifications
dashboard/data.py       Cached API loaders and type normalization
dashboard/analysis.py   Bathymetry, interpolation, and masking
dashboard/views.py      Streamlit view rendering
tests/                  Pure-function regression tests
```

## Checks

```bash
uv run pytest
uv run ruff check .
```

Bathymetry is retrieved from the public GEBCO OPeNDAP service only when needed by a section plot. API responses and expensive transformations use bounded Streamlit caches.
