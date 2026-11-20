"""Weather Lookup Tool using the free Open-Meteo API (no key needed).

Forecast API covers ~16 days. For trips further out we fall back to the
archive API for the same dates in a past year and label it as historical.
"""
from datetime import date, timedelta

import requests

from config import ARCHIVE_URL, CITY_COORDS, FORECAST_URL

WMO_CODES = {
    0: "Sunny", 1: "Mostly sunny", 2: "Partly cloudy", 3: "Overcast",
    45: "Fog", 48: "Fog", 51: "Light drizzle", 53: "Drizzle", 55: "Heavy drizzle",
    61: "Light rain", 63: "Rain", 65: "Heavy rain", 71: "Light snow", 73: "Snow",
    75: "Heavy snow", 80: "Rain showers", 81: "Rain showers", 82: "Violent showers",
    95: "Thunderstorm", 96: "Thunderstorm with hail", 99: "Thunderstorm with hail",
}


def _to_date(value) -> date:
    return value if isinstance(value, date) else date.fromisoformat(str(value))


def _unavailable(start: date, days: int, reason: str) -> list:
    return [{"date": (start + timedelta(d)).isoformat(), "summary": "Unavailable",
             "source": reason} for d in range(days)]


def get_weather(city: str, start_date, end_date, today: date = None) -> list:
    """Day-by-day weather for a city between two dates (inclusive)."""
    start, end = _to_date(start_date), _to_date(end_date)
    today = today or date.today()
    days = (end - start).days + 1
    coords = CITY_COORDS.get(city.strip().title())
    if not coords:
        return _unavailable(start, days, f"no coordinates for {city}")

    if end < today - timedelta(days=7):            # past trip: real archive data
        url, shift, label = ARCHIVE_URL, 0, "historical"
    elif start >= today and end <= today + timedelta(days=15):
        url, shift, label = FORECAST_URL, 0, "live forecast"
    else:                                           # too far ahead: use a past year
        n = 1
        while end - timedelta(days=365 * n) > today - timedelta(days=7):
            n += 1
        url, shift, label = ARCHIVE_URL, 365 * n, "historical (same dates, past year)"

    params = {
        "latitude": coords[0], "longitude": coords[1], "timezone": "auto",
        "daily": "weather_code,temperature_2m_max,temperature_2m_min,precipitation_sum",
        "start_date": (start - timedelta(shift)).isoformat(),
        "end_date": (end - timedelta(shift)).isoformat(),
    }
    try:
        resp = requests.get(url, params=params, timeout=15)
        resp.raise_for_status()
        daily = resp.json()["daily"]
    except (requests.RequestException, KeyError, ValueError) as exc:
        return _unavailable(start, days, f"weather API error: {exc}")

    return [{
        "date": (start + timedelta(i)).isoformat(),
        "summary": WMO_CODES.get(daily["weather_code"][i], "Unknown"),
        "temp_max_c": daily["temperature_2m_max"][i],
        "temp_min_c": daily["temperature_2m_min"][i],
        "rain_mm": daily["precipitation_sum"][i],
        "source": label,
    } for i in range(len(daily["time"]))]
