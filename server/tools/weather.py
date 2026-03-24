"""Weather tool — standalone, unrelated to QSC product domain."""

import requests

from server.app import mcp


@mcp.tool()
def get_weather(location: str):
    """Retrieve current weather data for a location. Provide a city name (e.g. 'Berlin', 'London') or 'latitude,longitude' (e.g. '52.52,13.41'). Uses the Open-Meteo public API."""
    location = location.strip()
    # Check if input is lat,long
    if "," in location and len(location.split(",")) == 2:
        try:
            lat, lon = location.split(",")
            lat, lon = float(lat.strip()), float(lon.strip())
        except ValueError:
            lat, lon = _geocode_location(location)
    else:
        lat, lon = _geocode_location(location)

    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": "temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m,precipitation",
        "timezone": "auto",
    }
    response = requests.get(url, params=params)
    response.raise_for_status()
    return response.json()


def _geocode_location(location: str) -> tuple[float, float]:
    """Resolve city name to latitude and longitude using Open-Meteo Geocoding API."""
    url = "https://geocoding-api.open-meteo.com/v1/search"
    params = {"name": location, "count": 1}
    response = requests.get(url, params=params)
    response.raise_for_status()
    data = response.json()
    results = data.get("results", [])
    if not results:
        raise ValueError(f"Location not found: {location}")
    return results[0]["latitude"], results[0]["longitude"]
