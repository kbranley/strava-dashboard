"""Strava API client for fetching athlete data and activities."""

import time
from datetime import datetime, timedelta

import requests


class StravaClient:
    """Client to interact with the Strava V3 API."""

    BASE_URL = "https://www.strava.com/api/v3"
    AUTH_URL = "https://www.strava.com/oauth/token"

    def __init__(self, client_id: str, client_secret: str, refresh_token: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.refresh_token = refresh_token
        self.access_token: str | None = None
        self.token_expires_at: int = 0

    def _ensure_token(self) -> None:
        """Refresh access token if expired."""
        if self.access_token and time.time() < self.token_expires_at:
            return

        response = requests.post(
            self.AUTH_URL,
            data={
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "refresh_token": self.refresh_token,
                "grant_type": "refresh_token",
            },
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()

        self.access_token = data["access_token"]
        self.refresh_token = data["refresh_token"]
        self.token_expires_at = data["expires_at"]

    def _get(self, endpoint: str, params: dict | None = None) -> dict | list:
        """Make an authenticated GET request to the Strava API."""
        self._ensure_token()
        response = requests.get(
            f"{self.BASE_URL}{endpoint}",
            headers={"Authorization": f"Bearer {self.access_token}"},
            params=params or {},
            timeout=10,
        )
        response.raise_for_status()
        return response.json()

    def get_athlete(self) -> dict:
        """Get the authenticated athlete's profile."""
        return self._get("/athlete")

    def get_athlete_stats(self, athlete_id: int) -> dict:
        """Get the athlete's stats (totals and recent)."""
        return self._get(f"/athletes/{athlete_id}/stats")

    def get_activities(
        self,
        per_page: int = 100,
        page: int = 1,
        after: datetime | None = None,
        before: datetime | None = None,
    ) -> list[dict]:
        """Get a page of the athlete's activities."""
        params = {"per_page": per_page, "page": page}
        if after:
            params["after"] = int(after.timestamp())
        if before:
            params["before"] = int(before.timestamp())
        return self._get("/athlete/activities", params=params)

    def get_all_activities(
        self,
        after: datetime | None = None,
        before: datetime | None = None,
    ) -> list[dict]:
        """Fetch all activities, paginating automatically."""
        all_activities = []
        page = 1
        while True:
            activities = self.get_activities(
                per_page=200, page=page, after=after, before=before
            )
            if not activities:
                break
            all_activities.extend(activities)
            page += 1
        return all_activities

    def get_recent_activities(self, weeks: int = 12) -> list[dict]:
        """Get activities from the last N weeks."""
        after = datetime.now() - timedelta(weeks=weeks)
        return self.get_all_activities(after=after)
