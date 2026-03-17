import re
import logging
from typing import Optional, Tuple

import requests

from config import settings

logger = logging.getLogger(__name__)

_WEATHER_RE = re.compile(r"\bweather\b", re.IGNORECASE)


def is_weather_query(text: str) -> bool:
    return bool(_WEATHER_RE.search(text))


def extract_location_and_days(text: str) -> Tuple[Optional[str], int]:
    """
    Parse patterns like:
      weather today Brussels
      weather tomorrow Brussels
      weather 3 days Brussels
      weather Brussels
    Returns (location, days) where days=0 means current/today.
    """
    text = text.strip()

    # "weather tomorrow <location>"
    m = re.search(r"\bweather\s+tomorrow\s+(.*)", text, re.IGNORECASE)
    if m:
        location = m.group(1).strip() or None
        return location, 1

    # "weather today <location>"
    m = re.search(r"\bweather\s+today\s+(.*)", text, re.IGNORECASE)
    if m:
        location = m.group(1).strip() or None
        return location, 0

    # "weather <N> days <location>"
    m = re.search(r"\bweather\s+(\d+)\s+days?\s+(.*)", text, re.IGNORECASE)
    if m:
        days = int(m.group(1))
        location = m.group(2).strip() or None
        return location, days

    # "weather <location>"
    m = re.search(r"\bweather\s+(.*)", text, re.IGNORECASE)
    if m:
        location = m.group(1).strip() or None
        return location, 0

    return None, 0


def fetch_current_weather(city: str) -> dict:
    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {
        "q": city,
        "appid": settings.OPENWEATHER_API_KEY,
        "units": "metric",
    }
    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()
    return response.json()


def fetch_forecast(city: str) -> dict:
    url = "https://api.openweathermap.org/data/2.5/forecast"
    params = {
        "q": city,
        "appid": settings.OPENWEATHER_API_KEY,
        "units": "metric",
    }
    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()
    return response.json()


def summarize_current_weather(data: dict) -> str:
    city = data.get("name", "Unknown")
    temp = data.get("main", {}).get("temp", "?")
    description = (data.get("weather") or [{}])[0].get("description", "unknown conditions")
    humidity = data.get("main", {}).get("humidity", "?")
    wind = data.get("wind", {}).get("speed", "?")
    return (
        f"Current weather in {city}: {temp}°C, {description}. "
        f"Humidity: {humidity}%, Wind: {wind} m/s."
    )


def summarize_tomorrow_forecast(data: dict) -> str:
    """Pick the first forecast entry for the next day and summarise it."""
    from datetime import datetime, timedelta, timezone

    tomorrow = (datetime.now(timezone.utc) + timedelta(days=1)).strftime("%Y-%m-%d")
    entries = [e for e in data.get("list", []) if e.get("dt_txt", "").startswith(tomorrow)]
    if not entries:
        return "No forecast data available for tomorrow."

    entry = entries[len(entries) // 2]  # pick midday entry if possible
    city = data.get("city", {}).get("name", "Unknown")
    temp = entry.get("main", {}).get("temp", "?")
    description = (entry.get("weather") or [{}])[0].get("description", "unknown conditions")
    return f"Tomorrow in {city}: {temp}°C, {description}."
