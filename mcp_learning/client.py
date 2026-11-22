import asyncio
import json
import sys
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def main():
    server_path = Path(__file__).with_name("server.py")
    server = StdioServerParameters(command=sys.executable, args=[str(server_path)])

    async with stdio_client(server) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            tools = await session.list_tools()

            for tool in tools.tools:
                print(f"Tool: {tool.name}")
                print(f"Description: {tool.description}")
                print("Input schema:", json.dumps(tool.inputSchema, indent=2))

            result = await session.call_tool("multiply", {"x": 4, "y": 6})
            print("Tool error:", result.isError)
            for item in result.content:
                if item.type == "text":
                    print("Result:", item.text)


if __name__ == "__main__":
    asyncio.run(main())
