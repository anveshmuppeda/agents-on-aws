"""
Test client for the guide-023 MCP server.

Run with the server started:
    Terminal 1: python3 Source/app/agent.py
    Terminal 2: python3 Source/test_mcp_client.py
"""

import asyncio
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client


MCP_URL = "http://localhost:8000/mcp"


async def main():
    print("\n" + "="*60)
    print("  Guide 023: MCP Client Test")
    print("="*60)

    async with streamablehttp_client(MCP_URL, timeout=30) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # ── List available tools ──
            print("\n[1] Listing available tools:")
            tools = await session.list_tools()
            for tool in tools.tools:
                print(f"  ✓ {tool.name}: {tool.description}")

            # ── Call get_weather ──
            print("\n[2] Calling get_weather('Tokyo'):")
            result = await session.call_tool("get_weather", {"location": "Tokyo"})
            print(f"  Result: {result.content[0].text}")

            # ── Call get_current_time ──
            print("\n[3] Calling get_current_time('London'):")
            result = await session.call_tool("get_current_time", {"timezone": "London"})
            print(f"  Result: {result.content[0].text}")

            # ── Call convert_currency ──
            print("\n[4] Calling convert_currency(100, 'USD', 'EUR'):")
            result = await session.call_tool("convert_currency", {
                "amount": 100.0,
                "from_currency": "USD",
                "to_currency": "EUR",
            })
            print(f"  Result: {result.content[0].text}")

            # ── Call get_server_info ──
            print("\n[5] Calling get_server_info():")
            result = await session.call_tool("get_server_info", {})
            print(f"  Result: {result.content[0].text}")

    print("\n" + "="*60)
    print("  All MCP tool calls succeeded!")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())
