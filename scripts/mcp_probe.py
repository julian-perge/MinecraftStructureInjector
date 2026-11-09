"""Exercise the installed MCP server over its actual stdio transport."""

import asyncio
import json
import sys
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def main():
    params = StdioServerParameters(command=sys.executable, args=["-m", "structurelab.server"])
    async with stdio_client(params) as (read, write), ClientSession(read, write) as session:
        await session.initialize()
        tools = await session.list_tools()
        print("Tools:", ", ".join(t.name for t in tools.tools), flush=True)
        tool = sys.argv[1] if len(sys.argv) > 1 else "lab_status"
        args = json.loads(Path(sys.argv[2]).read_text()) if len(sys.argv) > 2 else {}
        result = await session.call_tool(tool, args)
        for content in result.content:
            if content.type == "text":
                print(content.text, flush=True)
            elif content.type == "image":
                import base64

                path = Path("artifacts/mcp-retrieved.png")
                path.write_bytes(base64.b64decode(content.data))
                print("MCP image saved:", path.resolve(), flush=True)
        if result.isError:
            sys.exit(1)


asyncio.run(main())
