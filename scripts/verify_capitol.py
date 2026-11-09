"""Check the completed Capitol against exported NBT and authoritative live blocks."""

import asyncio
import hashlib
import json
import sys
import zipfile
from pathlib import Path

import nbtlib
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def main():
    folder = Path(sys.argv[1] if len(sys.argv) > 1 else "artifacts/capitol/iteration-3")
    template = folder / "nebraska_state_capitol.nbt"
    data = nbtlib.load(template)
    assert list(map(int, data["size"])) == [185, 130, 185]
    assert len(data["blocks"]) == 429341 and not data["entities"]
    assert all(str(p["Name"]).startswith("minecraft:") for p in data["palette"])
    with zipfile.ZipFile(template.with_suffix(".zip")) as pack:
        assert pack.read("data/nebraska/structure/state_capitol.nbt") == template.read_bytes()
    records = {tuple(map(int, b["pos"])): data["palette"][int(b["state"])] for b in data["blocks"]}
    positions = [
        (78, 30, 92),
        (92, 95, 92),
        (91, 123, 92),
        (92, 125, 92),
        (141, 12, 34),
        (141, 12, 30),
        (90, 48, 91),
        (92, 10, 92),
    ]
    # Both sides of chunk seams, foundation, roof, and explicit interior air.
    for x in range(15, 185, 16):
        for z in (31, 32, 79, 80, 95, 96, 143, 144):
            for dx in (0, 1):
                pos = (min(x + dx, 184), 2, z)
                positions.append(pos)
    params = StdioServerParameters(command=sys.executable, args=["-m", "structurelab.server"])
    async with stdio_client(params) as (read, write), ClientSession(read, write) as session:
        await session.initialize()

        async def call(name, args=None):
            result = await session.call_tool(name, args or {})
            assert not result.isError, str(result.content)
            return json.loads(next(c.text for c in result.content if c.type == "text"))

        status = await call("lab_status")
        job = status["job"]
        assert job["state"] == "complete" and job["captured"] == 16
        assert job["processed"] == 0 and job["work_total"] == 0  # camera-only recapture
        for start in range(0, len(positions), 50):
            actual = await call("inspect_blocks", {"positions": positions[start : start + 50]})
            for key, state in actual.items():
                pos = tuple(json.loads(key))
                expected = records[pos]
                assert "{" + str(expected["Name"]) + "}" in state, (pos, state, expected)
                for k, v in expected.get("Properties", {}).items():
                    assert f"{k}={v}" in state, (pos, k, v, state)
        previous = json.loads((folder / "placement-manifest.json").read_text())
        assert previous["sha256"] == job["sha256"] and previous["processed"] == 288
        assert not Path(previous["directory"]).exists()  # normal successful retention
    result = {
        "passed": True,
        "live_positions_checked": len(positions),
        "vanilla_palette": True,
        "datapack_payload_matches_nbt": True,
        "recapture_preserved_input_sha256": True,
        "recapture_placement_units": 0,
        "previous_runtime_revision_removed": True,
        "final_revision": job["revision"],
        "nbt_sha256": hashlib.sha256(template.read_bytes()).hexdigest(),
        "jar_sha256": hashlib.sha256(Path("build/libs/structurelab-26.2-0.2.0.jar").read_bytes()).hexdigest(),
    }
    (folder / "verification.json").write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
