"""Process and transform Strava activity data for visualization."""

from datetime import datetime

import pandas as pd


def activities_to_dataframe(activities: list[dict]) -> pd.DataFrame:
    """Convert raw Strava activities to a clean DataFrame."""
    if not activities:
        return pd.DataFrame()

    df = pd.DataFrame(activities)

    # Parse dates
    df["start_date"] = pd.to_datetime(df["start_date"])
    df["start_date_local"] = pd.to_datetime(df["start_date_local"])

    # Convert units
    df["distance_km"] = df["distance"] / 1000
    df["distance_miles"] = df["distance"] / 1609.34
    df["elapsed_time_min"] = df["elapsed_time"] / 60
    df["moving_time_min"] = df["moving_time"] / 60
    df["elevation_gain_ft"] = df["total_elevation_gain"] * 3.28084

    # Pace (min/km) for runs
    df["pace_min_per_km"] = df.apply(
        lambda row: (row["moving_time"] / 60) / row["distance_km"]
        if row["distance_km"] > 0
        else None,
        axis=1,
    )

    # Speed (km/h) for rides
    df["speed_kmh"] = df.apply(
        lambda row: row["distance_km"] / (row["moving_time"] / 3600)
        if row["moving_time"] > 0
        else None,
        axis=1,
    )

    # Week and month groupings
    df["week"] = df["start_date_local"].dt.isocalendar().week.astype(int)
    df["year"] = df["start_date_local"].dt.year
    df["month"] = df["start_date_local"].dt.to_period("M").astype(str)
    df["week_start"] = df["start_date_local"].dt.to_period("W").apply(
        lambda r: r.start_time
    )
    df["day_of_week"] = df["start_date_local"].dt.day_name()

    return df


def filter_by_type(df: pd.DataFrame, activity_type: str) -> pd.DataFrame:
    """Filter activities by type (Run, Ride, etc.)."""
    return df[df["type"] == activity_type].copy()


def weekly_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate activities by week."""
    if df.empty:
        return pd.DataFrame()

    weekly = (
        df.groupby("week_start")
        .agg(
            total_distance_km=("distance_km", "sum"),
            total_distance_miles=("distance_miles", "sum"),
            total_moving_time_min=("moving_time_min", "sum"),
            total_elevation_m=("total_elevation_gain", "sum"),
            activity_count=("id", "count"),
            avg_pace=("pace_min_per_km", "mean"),
            avg_speed_kmh=("speed_kmh", "mean"),
        )
        .reset_index()
        .sort_values("week_start")
    )
    return weekly


def monthly_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate activities by month."""
    if df.empty:
        return pd.DataFrame()

    monthly = (
        df.groupby("month")
        .agg(
            total_distance_km=("distance_km", "sum"),
            total_distance_miles=("distance_miles", "sum"),
            total_moving_time_min=("moving_time_min", "sum"),
            total_elevation_m=("total_elevation_gain", "sum"),
            activity_count=("id", "count"),
            avg_pace=("pace_min_per_km", "mean"),
            avg_speed_kmh=("speed_kmh", "mean"),
        )
        .reset_index()
        .sort_values("month")
    )
    return monthly


def format_pace(pace_decimal: float) -> str:
    """Convert decimal pace (e.g. 4.5) to mm:ss format (e.g. 4:30)."""
    if pace_decimal is None or pd.isna(pace_decimal):
        return "--:--"
    minutes = int(pace_decimal)
    seconds = int((pace_decimal - minutes) * 60)
    return f"{minutes}:{seconds:02d}"


def get_personal_bests(df: pd.DataFrame) -> dict:
    """Extract personal bests from activities."""
    pbs = {}

    runs = filter_by_type(df, "Run")
    rides = filter_by_type(df, "Ride")

    if not runs.empty:
        # Fastest pace (lowest min/km)
        fastest_run = runs.loc[runs["pace_min_per_km"].idxmin()]
        pbs["fastest_pace"] = {
            "value": format_pace(fastest_run["pace_min_per_km"]),
            "date": fastest_run["start_date_local"].strftime("%d %b %Y"),
            "name": fastest_run.get("name", ""),
        }
        # Longest run
        longest_run = runs.loc[runs["distance_km"].idxmax()]
        pbs["longest_run"] = {
            "value": f"{longest_run['distance_km']:.1f} km",
            "date": longest_run["start_date_local"].strftime("%d %b %Y"),
            "name": longest_run.get("name", ""),
        }

    if not rides.empty:
        # Fastest ride (highest avg speed)
        fastest_ride = rides.loc[rides["speed_kmh"].idxmax()]
        pbs["fastest_ride"] = {
            "value": f"{fastest_ride['speed_kmh']:.1f} km/h",
            "date": fastest_ride["start_date_local"].strftime("%d %b %Y"),
            "name": fastest_ride.get("name", ""),
        }
        # Longest ride
        longest_ride = rides.loc[rides["distance_km"].idxmax()]
        pbs["longest_ride"] = {
            "value": f"{longest_ride['distance_km']:.1f} km",
            "date": longest_ride["start_date_local"].strftime("%d %b %Y"),
            "name": longest_ride.get("name", ""),
        }

    return pbs
