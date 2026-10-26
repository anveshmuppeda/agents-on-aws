"""
Basic tools for the local Strands agent demo.

These are intentionally simple so the focus stays on
the agent loop, not on tool implementation complexity.
"""

import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from strands import tool


# ---------------------------------------------------------------------------
# Weather Tool
# Note: This returns mocked data so the guide runs without any API keys.
# In a real agent you'd call OpenWeatherMap, Open-Meteo, etc.
# ---------------------------------------------------------------------------

MOCK_WEATHER: dict[str, dict] = {
    "austin": {"temp": "92°F / 33°C", "condition": "Sunny", "humidity": "45%"},
    "new york": {"temp": "75°F / 24°C", "condition": "Partly Cloudy", "humidity": "60%"},
    "seattle": {"temp": "58°F / 14°C", "condition": "Overcast", "humidity": "78%"},
    "london": {"temp": "61°F / 16°C", "condition": "Light Rain", "humidity": "82%"},
    "tokyo": {"temp": "79°F / 26°C", "condition": "Clear", "humidity": "55%"},
    "sydney": {"temp": "68°F / 20°C", "condition": "Sunny", "humidity": "50%"},
    "paris": {"temp": "64°F / 18°C", "condition": "Cloudy", "humidity": "70%"},
}


@tool
def get_weather(location: str) -> str:
    """
    Get the current weather for a city or location.

    Args:
        location: The city name, e.g. "Austin, TX" or "London"

    Returns:
        Weather information as a human-readable string.
    """
    key = location.lower().split(",")[0].strip()

    # Try exact match, then partial match
    weather = MOCK_WEATHER.get(key)
    if weather is None:
        for city, data in MOCK_WEATHER.items():
            if city in key or key in city:
                weather = data
                break

    if weather is None:
        return (
            f"Weather data for '{location}' is not available in this demo. "
            f"Available cities: {', '.join(MOCK_WEATHER.keys())}."
        )

    return (
        f"Current weather in {location}:\n"
        f"  Temperature: {weather['temp']}\n"
        f"  Condition:   {weather['condition']}\n"
        f"  Humidity:    {weather['humidity']}"
    )


# ---------------------------------------------------------------------------
# Time Tool
# Returns the real current time — no mock needed.
# ---------------------------------------------------------------------------

TIMEZONE_ALIASES: dict[str, str] = {
    "utc": "UTC",
    "est": "America/New_York",
    "cst": "America/Chicago",
    "mst": "America/Denver",
    "pst": "America/Los_Angeles",
    "london": "Europe/London",
    "paris": "Europe/Paris",
    "tokyo": "Asia/Tokyo",
    "sydney": "Australia/Sydney",
    "austin": "America/Chicago",
    "new york": "America/New_York",
    "seattle": "America/Los_Angeles",
    "berlin": "Europe/Berlin",
    "dubai": "Asia/Dubai",
    "singapore": "Asia/Singapore",
}


@tool
def get_current_time(timezone: str) -> str:
    """
    Get the current date and time in a given timezone or city.

    Args:
        timezone: A timezone name (e.g. "UTC", "America/New_York") or
                  a city/alias (e.g. "Tokyo", "London", "PST").

    Returns:
        Current date and time as a human-readable string.
    """
    key = timezone.lower().strip()

    # Resolve alias
    tz_name = TIMEZONE_ALIASES.get(key, timezone)

    try:
        tz = ZoneInfo(tz_name)
    except ZoneInfoNotFoundError:
        # Try to find a partial match in aliases
        for alias, tz_resolved in TIMEZONE_ALIASES.items():
            if alias in key or key in alias:
                tz = ZoneInfo(tz_resolved)
                tz_name = tz_resolved
                break
        else:
            return (
                f"Unknown timezone '{timezone}'. "
                f"Try a standard timezone like 'America/New_York', 'Europe/London', "
                f"or a city like 'Tokyo', 'London', 'Austin'."
            )

    now = datetime.datetime.now(tz)
    return (
        f"Current time in {timezone} ({tz_name}):\n"
        f"  Date: {now.strftime('%A, %B %d, %Y')}\n"
        f"  Time: {now.strftime('%I:%M %p')}"
    )
