import httpx

from app.config import settings

WEATHER_URL = "https://api.weatherapi.com/v1/current.json"


async def get_weather(city: str) -> str:
    """Get the current weather for a city."""
    params = {"key": settings.WEATHER_API_KEY, "q": city}
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(WEATHER_URL, params=params)
        resp.raise_for_status()
        data = resp.json()
    current = data["current"]
    location = data["location"]
    return (
        f"{location['name']}, {location['country']}: {current['temp_c']} C, "
        f"{current['condition']['text']}, humidity {current['humidity']}%, "
        f"wind {current['wind_kph']} km/h"
    )
