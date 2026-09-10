from __future__ import annotations

import polars as pl
import streamlit as st

from dashboard.config import DATASET_SPECS
from dashboard.data import (
    cruises_in_date_range,
    load_casts,
    load_cruises,
    load_dataset,
    load_datasets,
    load_underway,
)
from dashboard.views import (
    latest_click,
    render_data,
    render_metadata,
    render_metrics,
    render_profile,
    render_section,
    render_sidebar_data_summary,
    render_track,
)

st.set_page_config(page_title="NES-LTER API dashboard", layout="wide")
st.title("NES-LTER API dashboard")
st.caption(
    "Explore cruise tracks, depth sections, and single-station profiles from the NES-LTER API."
)

try:
    cruise_df = load_cruises()
except RuntimeError as exc:
    st.error(str(exc))
    st.stop()

with st.sidebar:
    st.header("Data selection")
    selection_mode = st.segmented_control(
        "Select by", ["Cruises", "Date range"], default="Cruises"
    )
    cruise_names = cruise_df["name"].to_list()
    if selection_mode == "Cruises":
        default = [name for name in ["EN617"] if name in cruise_names] or cruise_names[
            -1:
        ]
        selected = st.multiselect(
            "Cruises", cruise_names, default=default, key="selected_cruises"
        )
    else:
        min_dt = cruise_df["start_time"].drop_nulls().min()
        max_dt = cruise_df["end_time"].drop_nulls().max()
        date_range = st.date_input(
            "Date range",
            value=(min_dt.date(), max_dt.date()),
            key="selected_date_range",
        )
        if len(date_range) != 2:
            st.stop()
        selected = cruises_in_date_range(cruise_df, *date_range)
        st.caption(f"{len(selected)} cruise(s) overlap this range.")

view = st.segmented_control(
    "View", ["Explore", "Data", "Metadata"], default="Explore", key="view"
)

with st.sidebar:
    if view == "Explore":
        st.subheader("Cruise track")
        map_source = st.selectbox(
            "Map data source",
            ["Underway", "CTD", "Bottles"],
            key="map_source",
            help="Choose the endpoint used for map locations and the track.",
        )
        st.subheader("Sections")
        section_datasets = tuple(
            st.multiselect(
                "Section data sources",
                ["CTD casts", *DATASET_SPECS],
                default=["CTD bottles"],
                key="section_datasets",
            )
        )
        st.subheader("Profiles")
        profile_dataset = st.selectbox(
            "Profile dataset",
            list(DATASET_SPECS),
            index=list(DATASET_SPECS).index("CTD bottles"),
            key="profile_dataset",
        )
        profile_source = st.segmented_control(
            "Profile source",
            ["CTD", "Bottles", "Both"],
            default="CTD",
            key="profile_source",
        )
    elif view == "Data":
        data_source = st.selectbox(
            "Data source",
            ["Underway", "CTD casts", *DATASET_SPECS],
            key="data_source",
        )
    else:
        metadata_dataset = st.selectbox(
            "Dataset documentation",
            list(DATASET_SPECS),
            key="metadata_dataset",
        )

    st.caption(f"{len(selected)} cruise(s) selected")
    with st.expander("Active selection"):
        st.write(f"**View:** {view}")
        if view == "Explore":
            st.write(f"**Map:** {map_source}")
            st.write(f"**Sections:** {', '.join(section_datasets) or 'None'}")
            st.write(f"**Profiles:** {profile_dataset} · {profile_source}")
        elif view == "Data":
            st.write(f"**Source:** {data_source}")

if not selected:
    st.info("Select at least one cruise to begin.")
    st.stop()

selected_tuple = tuple(selected)
summary = cruise_df.filter(pl.col("name").is_in(selected))

context = " · ".join(selected_tuple)
if view == "Explore":
    context += (
        f" · Map: {map_source} · Sections: {', '.join(section_datasets) or 'None'}"
    )
    context += f" · Profiles: {profile_dataset}"
elif view == "Data":
    context += f" · {data_source}"
st.caption(context)

if view == "Metadata":
    render_metadata(selected_tuple, metadata_dataset)
elif view == "Explore":
    casts_df = load_casts(selected_tuple)
    underway_df = load_underway(selected_tuple)
    bottle_df = load_dataset(selected_tuple, "CTD bottles")
    section_df = (
        load_datasets(selected_tuple, section_datasets)
        if section_datasets
        else pl.DataFrame()
    )
    profile_df = (
        bottle_df
        if profile_dataset == "CTD bottles"
        else load_dataset(selected_tuple, profile_dataset)
    )
    section_label = ", ".join(section_datasets) or "Sections"
    render_sidebar_data_summary(
        [
            ("Underway", underway_df.height),
            ("CTD casts", casts_df.height),
            (section_label, section_df.height),
            (profile_dataset, profile_df.height),
        ]
    )
    render_metrics(summary, casts_df, section_df, section_label)
    map_click = render_track(
        casts_df, bottle_df, underway_df, "", map_source, selected_tuple
    )
    if section_datasets:
        section_click = render_section(section_df, section_label, selected)
    else:
        section_click = None
        st.info("Select at least one section data source in the sidebar.")
    render_profile(
        profile_df,
        profile_dataset,
        selected,
        casts_df,
        bottle_df,
        profile_source,
        focus_cast=latest_click({"map": map_click, "section": section_click}),
    )
else:
    casts_df = load_casts(selected_tuple)
    underway_df = load_underway(selected_tuple)
    data_df = (
        load_underway(selected_tuple)
        if data_source == "Underway"
        else load_casts(selected_tuple)
        if data_source == "CTD casts"
        else load_dataset(selected_tuple, data_source)
    )
    bottle_df = (
        data_df
        if data_source == "CTD bottles"
        else load_dataset(selected_tuple, "CTD bottles")
    )
    render_sidebar_data_summary(
        [(data_source, data_df.height), ("CTD bottles", bottle_df.height)]
    )
    render_metrics(summary, casts_df, data_df, data_source)
    render_data(casts_df, data_df, bottle_df, underway_df, data_source, selected_tuple)

with st.expander("Selected cruises"):
    st.dataframe(
        summary, hide_index=True, width="stretch", key="selected_cruises_table"
    )
