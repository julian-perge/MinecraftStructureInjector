"""MCP entry point. All tool results come from the running game or revision files."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import urllib.error
import urllib.request
import zipfile
from pathlib import Path

import nbtlib
from mcp.server.fastmcp import FastMCP, Image

from .builder import Structure
from .example import house

mcp = FastMCP("Minecraft Structure Lab")
DEFAULT_INSTANCE = Path(os.environ.get("APPDATA", "~")) / "ModrinthApp/profiles/NeoForge 26.1.2"
connection_path = Path(
    os.environ.get("STRUCTURELAB_CONNECTION", str(DEFAULT_INSTANCE / "structurelab/connection.json"))
)


def rpc(op: str, **args):
    if not connection_path.exists():
        raise RuntimeError(f"Launch Minecraft with Structure Lab installed. Connection file missing: {connection_path}")
    connection = json.loads(connection_path.read_text(encoding="utf-8"))
    if not re.fullmatch(r"http://127\.0\.0\.1:\d+/rpc", connection["url"]):
        raise ValueError("Only a localhost mod connection is allowed")
    request = urllib.request.Request(  # noqa: S310
        connection["url"],
        data=json.dumps(dict(op=op, **args)).encode(),
        headers={"Content-Type": "application/json", "Authorization": "Bearer " + connection["token"]},
    )
    try:
        with urllib.request.urlopen(request, timeout=100) as response:  # noqa: S310
            result = json.load(response)
    except urllib.error.HTTPError as exc:
        raise RuntimeError(exc.read().decode()) from exc
    if result.get("error") and "revision" not in result:
        raise RuntimeError(result["error"])
    return result


def require_revision(revision: str):
    job = rpc("job")
    if job["revision"] != revision:
        raise ValueError("Stale revision: another structure has been submitted")
    return job


@mcp.tool()
def lab_status() -> dict:
    """Get world identity, limits, connection readiness, and active job progress."""
    return rpc("status")


@mcp.tool()
def list_blocks(query: str = "") -> dict:
    """Find up to 200 block IDs and their valid properties from the live game."""
    return rpc("blocks", query=query)


@mcp.tool()
def validate_structure(path: str) -> dict:
    """Validate an existing compressed NBT structure against the game's registry and limits."""
    return rpc("validate", path=str(Path(path).resolve()))


@mcp.tool()
def submit_structure(path: str, views_path: str | None = None) -> dict:
    """Replace the active structure and automatically capture all angles. Returns a job immediately.

    Optional views JSON is a list of {id,label,position:[x,y,z],spawn,angles:[{id,yaw,pitch}]}.
    Coordinates are relative to structure origin; position is feet height, eye_height defaults to 1.62.
    Embedded view pads are extracted automatically. Poll job_status until complete or failed.
    """
    args = {"path": str(Path(path).resolve())}
    if views_path:
        args["views"] = json.loads(Path(views_path).read_text(encoding="utf-8"))
    return rpc("submit", **args)


@mcp.tool()
def job_status(revision: str) -> dict:
    """Read progress for this exact revision; rejects stale job IDs."""
    return require_revision(revision)


@mcp.tool()
def recapture_views(revision: str, views_path: str | None = None) -> dict:
    """Capture the placed build without replacing blocks. Returns a new revision and capture set.

    Optional sidecar defines the replacement set of viewpoints; omitted reuses all current views.
    After success, old screenshots are deleted using the normal retention policy.
    """
    require_revision(revision)
    args = {"revision": revision}
    if views_path:
        args["views"] = json.loads(Path(views_path).read_text(encoding="utf-8"))
    return rpc("recapture", **args)


@mcp.tool()
def cancel_job(revision: str) -> dict:
    """Request cancellation of the current revision."""
    require_revision(revision)
    return rpc("cancel")


@mcp.tool()
def list_captures(revision: str, offset: int = 0, limit: int = 20) -> dict:
    """List labeled screenshot metadata without returning all image bytes."""
    if offset < 0 or not 1 <= limit <= 100:
        raise ValueError("offset >= 0; limit between 1 and 100")
    job = require_revision(revision)
    return {
        "revision": revision,
        "state": job["state"],
        "total": len(job["captures"]),
        "captures": job["captures"][offset : offset + limit],
    }


@mcp.tool()
def get_capture(revision: str, view_id: str, angle_id: str) -> Image:
    """Return a real 1920x1080 Minecraft screenshot as MCP image content."""
    job = require_revision(revision)
    item = next((c for c in job["captures"] if c["id"] == view_id and c["angle"] == angle_id), None)
    if item is None:
        raise ValueError("This viewpoint has no completed capture")
    return Image(path=str(Path(job["directory"]) / item["file"]))


@mcp.tool()
def inspect_blocks(positions: list[list[int]]) -> dict:
    """Read authoritative block states at relative positions, for placement and cleanup verification."""
    if len(positions) > 1000:
        raise ValueError("At most 1000 positions")
    return rpc("inspect", positions=positions)


@mcp.tool()
def generate_structure(
    output_path: str, size: list[int], operations: list[dict], views: list[dict] | None = None
) -> dict:
    """Generate NBT from set/fill/room operations; no Python code execution required.

    set: {op:'set',pos:[x,y,z],block:'minecraft:stone',properties:{}}
    fill: {op:'fill',start:[x,y,z],end:[x,y,z],block:'minecraft:stone'}
    room: {op:'room',start:[x,y,z],end:[x,y,z],wall:'oak_planks',floor:'stone',roof:'oak_planks'}
    A views list uses the submit_structure schema. Use the Python Structure library for typed block entities.
    """
    if len(size) != 3 or size[0] * size[1] * size[2] > 16_000_000:
        raise ValueError("Volume limit is 16,000,000 positions")
    result = Structure(tuple(size))
    for operation in operations:
        op = dict(operation)
        name = op.pop("op")
        if name == "set":
            result.set(**op)
        elif name == "fill":
            result.fill(**op)
        elif name == "room":
            result.room(**op)
        else:
            raise ValueError(f"Unknown operation: {name}")
    result.views = views or []
    return result.save(output_path)


@mcp.tool()
def generate_example_house(output_path: str, revision: int = 1) -> dict:
    """Generate the furnished house fixture. Revision 2 removes the gold sentinel and changes bedroom carpet."""
    if revision not in (1, 2):
        raise ValueError("Example revisions are 1 and 2")
    return house(output_path, revision)


@mcp.tool()
def export_structure(revision: str, output_path: str, namespace: str = "lab_export", name: str = "house") -> dict:
    """Export a verified revision as clean NBT plus a vanilla 26.1.2 datapack ZIP. No lab blocks survive."""
    job = require_revision(revision)
    if job["state"] != "complete":
        raise ValueError("Only fully captured revisions can be exported")
    if not re.fullmatch(r"[a-z0-9_]+", namespace) or not re.fullmatch(r"[a-z0-9_]+", name):
        raise ValueError("Use lowercase letters, digits, and underscores for namespace/name")
    source = Path(job["directory"]) / "structure.nbt"
    data = nbtlib.load(source)
    dependencies = sorted({str(s["Name"]).split(":")[0] for s in data["palette"]} - {"minecraft"})
    if "structurelab" in dependencies:
        raise ValueError("Export contains Structure Lab blocks")
    output = Path(output_path).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, output)
    pack = output.with_suffix(".zip")
    with zipfile.ZipFile(pack, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr(
            "pack.mcmeta",
            json.dumps(
                {
                    "pack": {
                        "description": "Structure Lab clean export for Minecraft 26.1.2",
                        "min_format": [101, 1],
                        "max_format": [101, 1],
                    }
                }
            ),
        )
        z.write(output, f"data/{namespace}/structure/{name}.nbt")
    return {
        "nbt": str(output),
        "datapack": str(pack),
        "dependencies": dependencies,
        "place_command": f"/place template {namespace}:{name} ~ ~ ~",
        "revision": revision,
    }


def main():
    global connection_path  # noqa: PLW0603
    parser = argparse.ArgumentParser()
    parser.add_argument("--connection", type=Path, default=connection_path)
    args = parser.parse_args()
    connection_path = args.connection.resolve()
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
