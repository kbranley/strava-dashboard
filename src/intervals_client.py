"""Intervals.icu API client for fetching athlete data and activities."""

from datetime import datetime, timedelta

import requests


class IntervalsClient:
    """Client to interact with the Intervals.icu API.

    API docs: https://intervals.icu/api/v1/docs
    Auth: Basic auth with API key (username = "API_KEY", password = your key)
    """

    BASE_URL = "https://intervals.icu/api/v1"

    def __init__(self, athlete_id: str, api_key: str):
        self.athlete_id = athlete_id
        self.api_key = api_key
        self.session = requests.Session()
        self.session.auth = ("API_KEY", api_key)
        self.session.headers.update({"Accept": "application/json"})

    def _get(self, endpoint: str, params: dict | None = None) -> dict | list:
        """Make an authenticated GET request to the Intervals.icu API."""
        url = f"{self.BASE_URL}/athlete/{self.athlete_id}{endpoint}"
        response = self.session.get(url, params=params or {}, timeout=15)
        response.raise_for_status()
        return response.json()

    def get_athlete(self) -> dict:
        """Get the authenticated athlete's profile."""
        return self._get("")

    def get_activities(
        self,
        oldest: datetime | None = None,
        newest: datetime | None = None,
    ) -> list[dict]:
        """Get activities within a date range.

        Intervals.icu uses date strings in YYYY-MM-DD format.
        """
        params = {}
        if oldest:
            params["oldest"] = oldest.strftime("%Y-%m-%d")
        if newest:
            params["newest"] = newest.strftime("%Y-%m-%d")
        return self._get("/activities", params=params)

    def get_recent_activities(self, weeks: int = 12) -> list[dict]:
        """Get activities from the last N weeks."""
        oldest = datetime.now() - timedelta(weeks=weeks)
        newest = datetime.now()
        return self.get_activities(oldest=oldest, newest=newest)

    def get_activity(self, activity_id: str) -> dict:
        """Get a single activity with full details."""
        url = f"{self.BASE_URL}/activity/{activity_id}"
        response = self.session.get(url, timeout=15)
        response.raise_for_status()
        return response.json()

    def get_wellness(
        self,
        oldest: datetime | None = None,
        newest: datetime | None = None,
    ) -> list[dict]:
        """Get wellness data (weight, sleep, HRV, etc.)."""
        params = {}
        if oldest:
            params["oldest"] = oldest.strftime("%Y-%m-%d")
        if newest:
            params["newest"] = newest.strftime("%Y-%m-%d")
        return self._get("/wellness", params=params)

    def get_fitness(
        self,
        oldest: datetime | None = None,
        newest: datetime | None = None,
    ) -> list[dict]:
        """Get fitness/fatigue (CTL/ATL/TSB) data."""
        params = {}
        if oldest:
            params["oldest"] = oldest.strftime("%Y-%m-%d")
        if newest:
            params["newest"] = newest.strftime("%Y-%m-%d")
        return self._get("/fitness", params=params)
