"""Real MCP regression: a rejected camera must preserve the last successful artifacts/world."""

import asyncio
import json
import os
import sys
import time
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def main():
    params = StdioServerParameters(command=sys.executable, args=["-m", "structurelab.server"], env=dict(os.environ))
    async with stdio_client(params) as (read, write), ClientSession(read, write) as session:
        await session.initialize()

        async def call(name, **args):
            result = await session.call_tool(name, args)
            assert not result.isError, result.content
            return json.loads(next(c.text for c in result.content if c.type == "text"))

        status = await call("lab_status")
        previous = status["job"]
        assert previous["state"] == "complete"
        positions = [[18, 2, 15], [10, 1, 5]]
        before = await call("inspect_blocks", positions=positions)
        path = Path("artifacts/evidence/invalid.views.json").resolve()
        path.write_text(json.dumps([{"id": "invalid", "position": [0, 1, -5], "yaw": 0, "pitch": 0, "eye_height": -1}]))
        job = await call(
            "submit_structure", path=str(Path("artifacts/evidence/v1/input.nbt").resolve()), views_path=str(path)
        )
        deadline = time.monotonic() + 20
        while job["state"] not in ("failed", "complete", "cancelled"):
            assert time.monotonic() < deadline
            await asyncio.sleep(0.2)
            job = await call("job_status", revision=job["revision"])
        assert job["state"] == "failed" and "Eye height" in job["error"], job
        assert before == await call("inspect_blocks", positions=positions)
        for capture in previous["captures"]:
            assert (Path(previous["directory"]) / capture["file"]).exists()
        Path("artifacts/evidence/failure.json").write_text(json.dumps(job, indent=2))
        print("PASS: rejected camera remains pollable; prior world and captures preserved")


asyncio.run(main())
