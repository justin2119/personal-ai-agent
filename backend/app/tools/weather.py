import logging

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

WEATHER_URL = "https://api.weatherapi.com/v1/current.json"


def _weather_error(city: str) -> str:
    return (
        f"Erreur lors de la récupération de la météo pour {city} "
        "(clé API invalide ou service indisponible)."
    )


async def get_weather(city: str) -> str:
    """Get the current weather for a city.

    Never raises: on a missing API key, an HTTP error (e.g. 401), a network
    failure, or an unexpected response, returns a user-friendly error string.
    """
    api_key = settings.WEATHER_API_KEY
    if not api_key:
        logger.warning("WEATHER_API_KEY is not set; weather lookup skipped")
        return _weather_error(city)

    params = {"key": api_key, "q": city}
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(WEATHER_URL, params=params)
        if resp.status_code != 200:
            # Do not log the full URL: it contains the API key.
            logger.warning(
                "WeatherAPI returned HTTP %s for city %r", resp.status_code, city
            )
            return _weather_error(city)
        data = resp.json()
        current = data["current"]
        location = data["location"]
        return (
            f"{location['name']}, {location['country']}: {current['temp_c']} C, "
            f"{current['condition']['text']}, humidity {current['humidity']}%, "
            f"wind {current['wind_kph']} km/h"
        )
    except httpx.HTTPError as exc:
        logger.warning("WeatherAPI request failed for city %r: %s", city, type(exc).__name__)
        return _weather_error(city)
    except Exception as exc:  # malformed JSON, missing fields, etc.
        logger.warning("WeatherAPI unexpected response for city %r: %s", city, type(exc).__name__)
        return _weather_error(city)
