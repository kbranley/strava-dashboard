"""Generate sample/demo data for testing the dashboard without a Strava connection."""

import random
from datetime import datetime, timedelta

import pandas as pd


def generate_sample_activities(weeks: int = 12) -> list[dict]:
    """Generate realistic sample running and cycling activities."""
    activities = []
    activity_id = 1
    now = datetime.now()
    start = now - timedelta(weeks=weeks)

    current = start
    while current < now:
        # ~4 runs per week
        for _ in range(random.randint(3, 5)):
            run_day = current + timedelta(
                days=random.randint(0, 6),
                hours=random.randint(6, 18),
                minutes=random.randint(0, 59),
            )
            if run_day > now:
                break

            distance = random.uniform(5000, 21000)  # 5k to half marathon
            pace_sec_per_km = random.uniform(240, 300)  # 4:00 - 5:00 /km
            moving_time = (distance / 1000) * pace_sec_per_km
            elapsed_time = moving_time * random.uniform(1.0, 1.1)

            run_names = [
                "Morning Run", "Easy Run", "Tempo Run", "Long Run",
                "Recovery Run", "Interval Session", "Park Run",
                "Marathon Training", "Hill Repeats", "Fartlek"
            ]

            activities.append({
                "id": activity_id,
                "name": random.choice(run_names),
                "type": "Run",
                "start_date": run_day.isoformat() + "Z",
                "start_date_local": run_day.isoformat() + "Z",
                "distance": distance,
                "moving_time": int(moving_time),
                "elapsed_time": int(elapsed_time),
                "total_elevation_gain": random.uniform(20, 200),
                "average_heartrate": random.uniform(140, 170),
                "max_heartrate": random.uniform(165, 195),
                "suffer_score": random.randint(30, 150),
            })
            activity_id += 1

        # ~2 rides per week
        for _ in range(random.randint(1, 3)):
            ride_day = current + timedelta(
                days=random.randint(0, 6),
                hours=random.randint(7, 16),
                minutes=random.randint(0, 59),
            )
            if ride_day > now:
                break

            distance = random.uniform(20000, 100000)  # 20-100km
            speed_kmh = random.uniform(25, 35)
            moving_time = (distance / 1000) / speed_kmh * 3600
            elapsed_time = moving_time * random.uniform(1.0, 1.15)

            ride_names = [
                "Morning Ride", "Lunch Ride", "Evening Ride",
                "Weekend Ride", "Coffee Ride", "Zwift Session",
                "Hill Climb", "Group Ride", "Recovery Spin",
                "Threshold Intervals"
            ]

            activities.append({
                "id": activity_id,
                "name": random.choice(ride_names),
                "type": "Ride",
                "start_date": ride_day.isoformat() + "Z",
                "start_date_local": ride_day.isoformat() + "Z",
                "distance": distance,
                "moving_time": int(moving_time),
                "elapsed_time": int(elapsed_time),
                "total_elevation_gain": random.uniform(100, 1200),
                "average_heartrate": random.uniform(130, 160),
                "max_heartrate": random.uniform(160, 190),
                "suffer_score": random.randint(40, 200),
                "average_watts": random.uniform(180, 280),
            })
            activity_id += 1

        current += timedelta(weeks=1)

    # Sort by date
    activities.sort(key=lambda a: a["start_date"])
    return activities
