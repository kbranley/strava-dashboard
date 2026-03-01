"""Process and transform activity data for visualization.

Supports both Intervals.icu and sample data formats.
"""

from datetime import datetime

import pandas as pd


def activities_to_dataframe(activities: list[dict]) -> pd.DataFrame:
    """Convert raw activities to a clean DataFrame.

    Handles both Intervals.icu and sample/Strava-style field names.
    """
    if not activities:
        return pd.DataFrame()

    df = pd.DataFrame(activities)

    # Normalize Intervals.icu field names to common format
    col_map = {
        "start_date_local": "start_date_local",
        "moving_time": "moving_time",
        "elapsed_time": "elapsed_time",
        "total_elevation_gain": "total_elevation_gain",
    }
    # Intervals.icu uses "icu_distance" (meters) or "distance"
    if "icu_distance" in df.columns and "distance" not in df.columns:
        df["distance"] = df["icu_distance"]
    # Intervals.icu uses "icu_moving_time" (seconds)
    if "icu_moving_time" in df.columns and "moving_time" not in df.columns:
        df["moving_time"] = df["icu_moving_time"]
    # Intervals.icu uses "elapsed_time" or "icu_elapsed_time"
    if "icu_elapsed_time" in df.columns and "elapsed_time" not in df.columns:
        df["elapsed_time"] = df["icu_elapsed_time"]
    # Intervals.icu elevation
    if "icu_total_elevation_gain" in df.columns and "total_elevation_gain" not in df.columns:
        df["total_elevation_gain"] = df["icu_total_elevation_gain"]
    # Intervals.icu power
    if "icu_average_watts" in df.columns and "average_watts" not in df.columns:
        df["average_watts"] = df["icu_average_watts"]
    if "icu_weighted_avg_watts" in df.columns and "weighted_avg_watts" not in df.columns:
        df["weighted_avg_watts"] = df["icu_weighted_avg_watts"]

    # Ensure required columns exist with defaults
    for col in ["distance", "moving_time", "elapsed_time", "total_elevation_gain"]:
        if col not in df.columns:
            df[col] = 0

    # Parse dates
    if "start_date_local" in df.columns:
        df["start_date_local"] = pd.to_datetime(df["start_date_local"])
    elif "start_date" in df.columns:
        df["start_date_local"] = pd.to_datetime(df["start_date"])

    if "start_date" not in df.columns:
        df["start_date"] = df["start_date_local"]
    else:
        df["start_date"] = pd.to_datetime(df["start_date"])

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
    """Filter activities by type (Run, Ride, etc.).

    Groups related types together:
    - "Ride" includes "Ride" and "VirtualRide"
    - "Run" includes "Run" and "VirtualRun"
    """
    type_groups = {
        "Ride": ["Ride", "VirtualRide"],
        "Run": ["Run", "VirtualRun"],
    }
    types = type_groups.get(activity_type, [activity_type])
    return df[df["type"].isin(types)].copy()


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


def get_personal_bests(df: pd.DataFrame, activity_type: str = "All") -> dict:
    """Extract personal bests from activities, filtered by activity type."""
    pbs = {}

    show_run = activity_type in ("All", "Run")
    show_ride = activity_type in ("All", "Ride")

    runs = filter_by_type(df, "Run") if show_run else pd.DataFrame()
    rides = filter_by_type(df, "Ride") if show_ride else pd.DataFrame()

    if not runs.empty:
        # Fastest pace (lowest min/km)
        valid_pace = runs.dropna(subset=["pace_min_per_km"])
        if not valid_pace.empty:
            fastest_run = valid_pace.loc[valid_pace["pace_min_per_km"].idxmin()]
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
        # Most climbing
        if "total_elevation_gain" in runs.columns:
            runs_with_elev = runs.dropna(subset=["total_elevation_gain"])
            runs_with_elev = runs_with_elev[runs_with_elev["total_elevation_gain"] > 0]
            if not runs_with_elev.empty:
                most_climbing = runs_with_elev.loc[runs_with_elev["total_elevation_gain"].idxmax()]
                pbs["most_climbing"] = {
                    "value": f"{most_climbing['total_elevation_gain']:.0f} m",
                    "date": most_climbing["start_date_local"].strftime("%d %b %Y"),
                    "name": most_climbing.get("name", ""),
                }
        # Longest time (biggest single effort)
        longest_time = runs.loc[runs["moving_time_min"].idxmax()]
        hrs = int(longest_time["moving_time_min"] // 60)
        mins = int(longest_time["moving_time_min"] % 60)
        time_str = f"{hrs}h {mins}m" if hrs > 0 else f"{mins}m"
        pbs["longest_effort"] = {
            "value": time_str,
            "date": longest_time["start_date_local"].strftime("%d %b %Y"),
            "name": longest_time.get("name", ""),
        }
        # Best estimated 5K pace (fastest pace on runs >= 5 km)
        if not valid_pace.empty:
            runs_5k = valid_pace[valid_pace["distance_km"] >= 5.0]
            if not runs_5k.empty:
                best_5k = runs_5k.loc[runs_5k["pace_min_per_km"].idxmin()]
                pbs["best_5k_pace"] = {
                    "value": format_pace(best_5k["pace_min_per_km"]),
                    "date": best_5k["start_date_local"].strftime("%d %b %Y"),
                    "name": best_5k.get("name", ""),
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
        # Most climbing
        if "total_elevation_gain" in rides.columns:
            rides_with_elev = rides.dropna(subset=["total_elevation_gain"])
            rides_with_elev = rides_with_elev[rides_with_elev["total_elevation_gain"] > 0]
            if not rides_with_elev.empty:
                most_climbing = rides_with_elev.loc[rides_with_elev["total_elevation_gain"].idxmax()]
                pbs["most_climbing"] = {
                    "value": f"{most_climbing['total_elevation_gain']:.0f} m",
                    "date": most_climbing["start_date_local"].strftime("%d %b %Y"),
                    "name": most_climbing.get("name", ""),
                }
        # Top speed
        if "max_speed" in rides.columns:
            rides_with_speed = rides.dropna(subset=["max_speed"])
            rides_with_speed = rides_with_speed[rides_with_speed["max_speed"] > 0]
            if not rides_with_speed.empty:
                top_speed = rides_with_speed.loc[rides_with_speed["max_speed"].idxmax()]
                # max_speed from API is in m/s, convert to km/h
                top_speed_kmh = top_speed["max_speed"] * 3.6
                pbs["top_speed"] = {
                    "value": f"{top_speed_kmh:.1f} km/h",
                    "date": top_speed["start_date_local"].strftime("%d %b %Y"),
                    "name": top_speed.get("name", ""),
                }
        # Power-based PBs (if power data available)
        if "average_watts" in rides.columns:
            rides_with_power = rides.dropna(subset=["average_watts"])
            rides_with_power = rides_with_power[rides_with_power["average_watts"] > 0]
            if not rides_with_power.empty:
                best_power = rides_with_power.loc[rides_with_power["average_watts"].idxmax()]
                pbs["best_avg_power"] = {
                    "value": f"{best_power['average_watts']:.0f} W",
                    "date": best_power["start_date_local"].strftime("%d %b %Y"),
                    "name": best_power.get("name", ""),
                }

    return pbs
