"""Intervals.icu Dashboard — track your running and cycling stats."""

import os

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

from src.data_processing import (
    activities_to_dataframe,
    filter_by_type,
    format_pace,
    get_personal_bests,
    monthly_summary,
    weekly_summary,
)
from src.sample_data import generate_sample_activities
from src.intervals_client import IntervalsClient

# --- Page config ---
st.set_page_config(
    page_title="Intervals.icu Dashboard",
    page_icon="🏃",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("🏃‍♂️🚴 Intervals.icu Dashboard")


# --- Data loading ---
@st.cache_data(ttl=300)
def load_intervals_data(athlete_id, api_key, weeks):
    """Load activities from Intervals.icu API (cached for 5 min)."""
    client = IntervalsClient(athlete_id, api_key)
    activities = client.get_recent_activities(weeks=weeks)
    return activities


def load_data(weeks: int) -> list[dict]:
    """Load data from Intervals.icu or generate sample data."""
    athlete_id = os.getenv("INTERVALS_ATHLETE_ID")
    api_key = os.getenv("INTERVALS_API_KEY")

    if athlete_id and api_key:
        return load_intervals_data(athlete_id, api_key, weeks)
    else:
        return generate_sample_activities(weeks=weeks)


# --- Sidebar ---
with st.sidebar:
    st.header("⚙️ Settings")

    use_demo = not all(
        [
            os.getenv("INTERVALS_ATHLETE_ID"),
            os.getenv("INTERVALS_API_KEY"),
        ]
    )

    if use_demo:
        st.info("📊 Using sample data. Set Intervals.icu env vars to use real data.")

    weeks = st.slider("Weeks of data", min_value=4, max_value=52, value=12)

    activity_type = st.selectbox(
        "Activity type",
        ["All", "Run", "Ride"],
        index=0,
    )

    unit = st.radio("Distance unit", ["km", "miles"], index=0)

    st.markdown("---")
    st.markdown("Built with ❤️ and [Streamlit](https://streamlit.io)")

# --- Load and process data ---
raw_activities = load_data(weeks)
df = activities_to_dataframe(raw_activities)

if df.empty:
    st.warning("No activities found. Try increasing the date range.")
    st.stop()

# Filter by type
if activity_type != "All":
    df_filtered = filter_by_type(df, activity_type)
else:
    df_filtered = df.copy()

if df_filtered.empty:
    st.warning(f"No {activity_type} activities found in the selected period.")
    st.stop()

# Distance column based on unit preference
dist_col = "distance_km" if unit == "km" else "distance_miles"
dist_label = "km" if unit == "km" else "mi"

# --- Key metrics ---
st.markdown("---")
col1, col2, col3, col4, col5 = st.columns(5)

total_dist = df_filtered[dist_col].sum()
total_time_hrs = df_filtered["moving_time_min"].sum() / 60
total_activities = len(df_filtered)
total_elevation = df_filtered["total_elevation_gain"].sum()
avg_per_week = total_dist / max(weeks, 1)

col1.metric("Total Distance", f"{total_dist:.1f} {dist_label}")
col2.metric("Total Time", f"{total_time_hrs:.1f} hrs")
col3.metric("Activities", f"{total_activities}")
col4.metric("Elevation Gain", f"{total_elevation:,.0f} m")
col5.metric(f"Avg/{dist_label} per Week", f"{avg_per_week:.1f} {dist_label}")

# --- Weekly mileage chart ---
st.markdown("---")
st.subheader("📈 Weekly Mileage")

weekly = weekly_summary(df_filtered)
if not weekly.empty:
    weekly_dist_col = f"total_distance_{unit}"
    fig_weekly = px.bar(
        weekly,
        x="week_start",
        y=weekly_dist_col,
        labels={
            "week_start": "Week",
            weekly_dist_col: f"Distance ({dist_label})",
        },
        color_discrete_sequence=["#FC4C02"],  # Strava orange
    )
    fig_weekly.update_layout(
        xaxis_title="",
        yaxis_title=f"Distance ({dist_label})",
        showlegend=False,
        height=400,
    )
    st.plotly_chart(fig_weekly, width="stretch")

# --- Two column charts ---
chart_col1, chart_col2 = st.columns(2)

# Pace/Speed trend
with chart_col1:
    st.subheader("⏱️ Pace / Speed Trend")

    runs = filter_by_type(df_filtered, "Run") if activity_type in ["All", "Run"] else pd.DataFrame()
    rides = filter_by_type(df_filtered, "Ride") if activity_type in ["All", "Ride"] else pd.DataFrame()

    if not runs.empty:
        runs_sorted = runs.sort_values("start_date_local")
        fig_pace = px.scatter(
            runs_sorted,
            x="start_date_local",
            y="pace_min_per_km",
            trendline="lowess",
            labels={"start_date_local": "", "pace_min_per_km": "Pace (min/km)"},
            color_discrete_sequence=["#FC4C02"],
            hover_data=["name", "distance_km"],
        )
        fig_pace.update_yaxes(autorange="reversed")  # Lower pace = faster
        fig_pace.update_layout(height=350, showlegend=False)
        st.plotly_chart(fig_pace, width="stretch")
    elif not rides.empty:
        rides_sorted = rides.sort_values("start_date_local")
        fig_speed = px.scatter(
            rides_sorted,
            x="start_date_local",
            y="speed_kmh",
            trendline="lowess",
            labels={"start_date_local": "", "speed_kmh": "Avg Speed (km/h)"},
            color_discrete_sequence=["#1DB954"],
            hover_data=["name", "distance_km"],
        )
        fig_speed.update_layout(height=350, showlegend=False)
        st.plotly_chart(fig_speed, width="stretch")
    else:
        st.info("No run or ride data to show pace/speed trends.")

# Activity breakdown
with chart_col2:
    st.subheader("🏅 Activity Breakdown")

    type_counts = df.groupby("type").agg(
        count=("id", "count"),
        distance=("distance_km", "sum"),
    ).reset_index()

    fig_pie = px.pie(
        type_counts,
        values="count",
        names="type",
        color_discrete_sequence=["#FC4C02", "#1DB954", "#4A90D9", "#F5A623"],
        hole=0.4,
    )
    fig_pie.update_layout(height=350)
    st.plotly_chart(fig_pie, width="stretch")

# --- Monthly summary ---
st.markdown("---")
st.subheader("📅 Monthly Summary")

monthly = monthly_summary(df_filtered)
if not monthly.empty:
    monthly_dist_col = f"total_distance_{unit}"
    fig_monthly = px.bar(
        monthly,
        x="month",
        y=monthly_dist_col,
        labels={"month": "Month", monthly_dist_col: f"Distance ({dist_label})"},
        color_discrete_sequence=["#FC4C02"],
    )
    fig_monthly.update_layout(height=350, xaxis_title="", showlegend=False)
    st.plotly_chart(fig_monthly, width="stretch")

# --- Personal bests ---
st.markdown("---")
st.subheader("🏆 Personal Bests")

pbs = get_personal_bests(df, activity_type)
if pbs:
    pb_cols = st.columns(len(pbs))
    for i, (key, pb) in enumerate(pbs.items()):
        label = key.replace("_", " ").title()
        pb_cols[i].metric(
            label=label,
            value=pb["value"],
            help=f"{pb['name']} — {pb['date']}",
        )
else:
    st.info("Not enough data for personal bests yet.")

# --- Recent activities table ---
st.markdown("---")
st.subheader("📋 Recent Activities")

display_cols = [
    "name", "type", "start_date_local", dist_col,
    "moving_time_min", "total_elevation_gain", "pace_min_per_km", "speed_kmh",
]
display_df = df_filtered[display_cols].copy().sort_values(
    "start_date_local", ascending=False
).head(20)

display_df = display_df.rename(columns={
    "name": "Name",
    "type": "Type",
    "start_date_local": "Date",
    dist_col: f"Distance ({dist_label})",
    "moving_time_min": "Time (min)",
    "total_elevation_gain": "Elevation (m)",
    "pace_min_per_km": "Pace (min/km)",
    "speed_kmh": "Speed (km/h)",
})

display_df["Date"] = display_df["Date"].dt.strftime("%d %b %Y %H:%M")
display_df[f"Distance ({dist_label})"] = display_df[f"Distance ({dist_label})"].round(1)
display_df["Time (min)"] = display_df["Time (min)"].round(0).astype(int)
display_df["Elevation (m)"] = display_df["Elevation (m)"].round(0).astype(int)
display_df["Pace (min/km)"] = display_df["Pace (min/km)"].apply(format_pace)
display_df["Speed (km/h)"] = display_df["Speed (km/h)"].round(1)

st.dataframe(display_df, width="stretch", hide_index=True)
