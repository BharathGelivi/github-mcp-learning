"""Run a standalone smoke test against the GitHub Learning MCP server."""

import asyncio
import sys
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def main() -> None:
    server_path = Path(__file__).resolve().with_name("server.py")
    server = StdioServerParameters(command=sys.executable, args=[str(server_path)])

    async with stdio_client(server) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            tools = await session.list_tools()
            for tool in tools.tools:
                print(f"{tool.name}: {tool.description}")

            result = await session.call_tool(
                "get_repository", {"owner": "octocat", "repo": "Hello-World"}
            )
            for item in result.content:
                if item.type == "text":
                    print(item.text)
            if result.isError:
                raise SystemExit(1)


if __name__ == "__main__":
    asyncio.run(main())
