# 🏃‍♂️🚴 Strava Dashboard

A personal running & cycling dashboard built with Python and Streamlit. Pulls data from the Strava API to visualize your training stats.

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-1.30+-FF4B4B?style=flat-square&logo=streamlit&logoColor=white)

## Features

- 📊 **Weekly & monthly mileage** charts
- ⏱️ **Pace & speed trends** with trendlines
- 🏆 **Personal bests** — fastest pace, longest run/ride
- 🏅 **Activity breakdown** by type
- 📋 **Recent activities** table
- 🎛️ **Filters** — activity type, date range, km/miles
- 🎲 **Demo mode** — works with sample data, no Strava account needed

## Quick Start

### 1. Clone & install

```bash
git clone https://github.com/kbranley/strava-dashboard.git
cd strava-dashboard
python -m venv .venv
.venv\Scripts\activate   # Windows
pip install -r requirements.txt
```

### 2. Run with demo data

```bash
streamlit run app.py
```

That's it! The dashboard will open with sample data so you can explore.

### 3. Connect your Strava (optional)

1. Go to [Strava API Settings](https://www.strava.com/settings/api)
2. Create an application (use `http://localhost` for the callback URL)
3. Copy your Client ID, Client Secret
4. Get a refresh token by following the [Strava OAuth flow](https://developers.strava.com/docs/getting-started/)
5. Create a `.env` file:

```bash
cp .env.example .env
# Edit .env with your credentials
```

6. Restart the dashboard — it will now pull your real data!

## Project Structure

```
strava-dashboard/
├── app.py                  # Streamlit dashboard
├── src/
│   ├── strava_client.py    # Strava API client
│   ├── data_processing.py  # Data transforms & aggregations
│   └── sample_data.py      # Demo data generator
├── requirements.txt
├── .env.example
└── .gitignore
```

## Tech Stack

- **[Streamlit](https://streamlit.io)** — dashboard framework
- **[Plotly](https://plotly.com)** — interactive charts
- **[Pandas](https://pandas.pydata.org)** — data processing
- **[Strava API v3](https://developers.strava.com)** — activity data

## License

MIT
