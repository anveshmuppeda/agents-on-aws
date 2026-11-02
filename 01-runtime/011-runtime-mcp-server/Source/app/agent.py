"""
011 — MCP Server on AgentCore Runtime
=======================================

A single MCP server that combines two sets of tools:

1. Travel Tools (custom, mock data)
   - get_weather        → weather for 7 cities
   - get_current_time   → real-time timezone lookup
   - convert_currency   → mock exchange rates
   - get_server_info    → server metadata

2. AWS Documentation Tools (official awslabs package, live docs.aws.amazon.com)
   - search_documentation → search AWS docs via official search API
   - read_documentation   → fetch any docs page as markdown
   - read_sections        → fetch specific sections of a page
   - search_table         → filter large tables (quotas, pricing)
   - recommend            → get related page recommendations

Why one server instead of two:
  One Runtime = one deployment, one ARN, one set of costs.
  Any agent connecting here gets 9 tools covering travel + AWS knowledge.
  No reason to separate them — MCP servers are composable by design.

Key technical notes:
  - Uses MCPServer from mcp 2.x (NOT FastMCP from mcp 1.x)
  - AWS Docs tools imported from awslabs.aws-documentation-mcp-server
    and registered via mcp.add_tool(fn) — no rewriting needed
  - json_response=True: returns plain JSON for InvokeAgentRuntime compatibility
  - No AWS credentials needed — AWS Docs tools only call public docs.aws.amazon.com
  - No BedrockAgentCoreApp — MCP servers don't use the agent SDK
"""

import os
from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from mcp.server.mcpserver import MCPServer

# ---------------------------------------------------------------------------
# Import the official AWS Documentation MCP server
# All 5 tools are already registered on this object by the package at import.
# We copy them into our combined server below.
# ---------------------------------------------------------------------------

from awslabs.aws_documentation_mcp_server.server_aws import mcp as _docs_mcp

# ---------------------------------------------------------------------------
# Create the combined MCP server
# ---------------------------------------------------------------------------

mcp = MCPServer(
    name="travel-tools-and-aws-docs",
    instructions=(
        "A combined MCP server with two capability sets:\n\n"
        "TRAVEL TOOLS (mock data):\n"
        "  get_weather, get_current_time, convert_currency, get_server_info\n\n"
        "AWS DOCUMENTATION TOOLS (live docs.aws.amazon.com):\n"
        "  search_documentation, read_documentation, read_sections, "
        "search_table, recommend"
    ),
)

# ---------------------------------------------------------------------------
# Travel Tools — custom, mock data
# ---------------------------------------------------------------------------

MOCK_WEATHER = {
    "austin":     {"temp": "92°F / 33°C", "condition": "Sunny",         "humidity": "45%"},
    "new york":   {"temp": "75°F / 24°C", "condition": "Partly Cloudy", "humidity": "60%"},
    "seattle":    {"temp": "58°F / 14°C", "condition": "Overcast",      "humidity": "78%"},
    "london":     {"temp": "61°F / 16°C", "condition": "Light Rain",    "humidity": "82%"},
    "tokyo":      {"temp": "79°F / 26°C", "condition": "Clear",         "humidity": "55%"},
    "sydney":     {"temp": "68°F / 20°C", "condition": "Sunny",         "humidity": "50%"},
    "paris":      {"temp": "64°F / 18°C", "condition": "Cloudy",        "humidity": "70%"},
}

TIMEZONE_ALIASES = {
    "london": "Europe/London", "tokyo": "Asia/Tokyo", "paris": "Europe/Paris",
    "sydney": "Australia/Sydney", "seattle": "America/Los_Angeles",
    "new york": "America/New_York", "austin": "America/Chicago", "utc": "UTC",
}


@mcp.tool()
def get_weather(location: str) -> str:
    """Get the current weather for a city. Returns temperature, condition, humidity."""
    key = location.lower().split(",")[0].strip()
    weather = MOCK_WEATHER.get(key)
    if weather is None:
        return f"Weather not available for '{location}'. Known cities: {', '.join(MOCK_WEATHER.keys())}"
    return (
        f"Weather in {location}:\n"
        f"  Temperature: {weather['temp']}\n"
        f"  Condition:   {weather['condition']}\n"
        f"  Humidity:    {weather['humidity']}"
    )


@mcp.tool()
def get_current_time(timezone: str) -> str:
    """Get the current date and time for a timezone or city name."""
    tz_name = TIMEZONE_ALIASES.get(timezone.lower().strip(), timezone)
    try:
        tz = ZoneInfo(tz_name)
    except ZoneInfoNotFoundError:
        return f"Unknown timezone '{timezone}'. Try 'Tokyo', 'London', 'America/New_York'."
    now = datetime.now(tz)
    return f"Time in {timezone}: {now.strftime('%A, %B %d, %Y at %I:%M %p')} ({tz_name})"


@mcp.tool()
def convert_currency(amount: float, from_currency: str, to_currency: str) -> str:
    """Convert an amount between currencies using mock exchange rates."""
    rates_to_usd = {
        "USD": 1.0, "EUR": 1.09, "GBP": 1.27, "JPY": 0.0067,
        "AUD": 0.65, "CAD": 0.74, "CHF": 1.12, "CNY": 0.14,
    }
    from_c = from_currency.upper()
    to_c   = to_currency.upper()
    if from_c not in rates_to_usd:
        return f"Unknown currency '{from_currency}'. Supported: {', '.join(rates_to_usd)}"
    if to_c not in rates_to_usd:
        return f"Unknown currency '{to_currency}'. Supported: {', '.join(rates_to_usd)}"
    result = (amount * rates_to_usd[from_c]) / rates_to_usd[to_c]
    return (
        f"Currency conversion (mock rates):\n"
        f"  {amount:.2f} {from_c} = {result:.2f} {to_c}\n"
        f"  Rate: 1 {from_c} = {rates_to_usd[from_c] / rates_to_usd[to_c]:.4f} {to_c}"
    )


@mcp.tool()
def get_server_info() -> str:
    """Return information about this MCP server and all available tools."""
    return (
        f"Combined MCP Server on AgentCore Runtime\n"
        f"Server time: {datetime.utcnow().isoformat()}Z\n\n"
        f"TRAVEL TOOLS (mock data):\n"
        f"  get_weather, get_current_time, convert_currency\n\n"
        f"AWS DOCUMENTATION TOOLS (live docs.aws.amazon.com):\n"
        f"  search_documentation, read_documentation, read_sections, "
        f"search_table, recommend"
    )


# ---------------------------------------------------------------------------
# AWS Documentation Tools — import from official awslabs package
# Copy all 5 tool functions from the docs server into this combined server.
# No rewriting needed — just transfer the registered fn objects.
# ---------------------------------------------------------------------------

for _tool_name, _tool_binding in _docs_mcp._tool_manager._tools.items():
    mcp.add_tool(_tool_binding.fn, name=_tool_name)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import anyio

    async def serve():
        await mcp.run_streamable_http_async(
            host="0.0.0.0",
            port=8000,
            stateless_http=True,  # required for AgentCore
            json_response=True,   # required for InvokeAgentRuntime compatibility
        )

    anyio.run(serve)
# Updated: combined travel + aws-docs tools, switched to MCPServer mcp2.x
