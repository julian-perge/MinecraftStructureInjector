"""Drive one Capitol iteration over real MCP and retain a compact review contact sheet."""

import argparse
import asyncio
import base64
import json
import sys
import time
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from PIL import Image, ImageDraw, ImageFont


def sheet(folder, job):
    captures = job["captures"]
    w, h = 480, 304
    canvas = Image.new("RGB", (w * 3, h * ((len(captures) + 2) // 3)), "#101820")
    draw = ImageDraw.Draw(canvas)
    try:
        font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 17)
    except OSError:
        font = ImageFont.load_default(size=17)
    for i, c in enumerate(captures):
        path = folder / c["file"]
        if not path.exists():
            continue
        with Image.open(path) as img:
            assert img.size == (1920, 1080)
            thumb = img.resize((480, 270))
        x, y = (i % 3) * w, (i // 3) * h
        canvas.paste(thumb, (x, y))
        draw.text((x + 9, y + 277), c["id"] + " / " + c["angle"], fill="white", font=font)
    canvas.save(folder / "review-contact-sheet.jpg", quality=90)


async def main(args):
    folder = Path(args.folder).resolve()
    folder.mkdir(parents=True, exist_ok=True)
    params = StdioServerParameters(command=sys.executable, args=["-m", "structurelab.server"])
    async with stdio_client(params) as (read, write), ClientSession(read, write) as session:
        await session.initialize()

        async def call(tool_name, **kwargs):
            result = await session.call_tool(tool_name, kwargs)
            if result.isError:
                raise RuntimeError(str(result.content))
            return json.loads(next(c.text for c in result.content if c.type == "text"))

        status = await call("lab_status")
        assert status["lab_world"]
        if args.recapture:
            job = await call(
                "recapture_views", revision=status["job"]["revision"], views_path=str(folder / "capitol.views.json")
            )
        else:
            valid = await call("validate_structure", path=str(folder / "capitol.nbt"))
            print("VALID:", valid, flush=True)
            job = await call(
                "submit_structure", path=str(folder / "capitol.nbt"), views_path=str(folder / "capitol.views.json")
            )
        revision = job["revision"]
        last = None
        started = time.monotonic()
        while job["state"] not in ("complete", "failed", "cancelled"):
            if time.monotonic() - started > 900:
                raise TimeoutError("Capitol batch exceeded 15 minutes")
            await asyncio.sleep(2)
            job = await call("job_status", revision=revision)
            progress = (job["state"], job.get("processed"), job["captured"])
            if progress != last:
                print("PROGRESS", revision, progress, "work_total", job.get("work_total"), flush=True)
                last = progress
        (folder / "manifest.json").write_text(json.dumps(job, indent=2))
        for capture in job["captures"]:
            result = await session.call_tool(
                "get_capture", {"revision": revision, "view_id": capture["id"], "angle_id": capture["angle"]}
            )
            img = next(c for c in result.content if c.type == "image")
            (folder / capture["file"]).write_bytes(base64.b64decode(img.data))
        sheet(folder, job)
        print("CAPTURES", len(job["captures"]), "ELAPSED", round(time.monotonic() - started, 1), flush=True)
        (folder / "timing.json").write_text(
            json.dumps(
                {
                    "seconds": round(time.monotonic() - started, 1),
                    "recapture": args.recapture,
                    "revision": revision,
                },
                indent=2,
            )
        )
        if job["state"] != "complete":
            raise RuntimeError(job["error"])
        exported = await call(
            "export_structure",
            revision=revision,
            output_path=str(folder / "nebraska_state_capitol.nbt"),
            namespace="nebraska",
            name="state_capitol",
        )
        assert not exported["dependencies"]
        (folder / "export.json").write_text(json.dumps(exported, indent=2))
        print("PASS", json.dumps(exported), flush=True)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("folder")
    p.add_argument("--recapture", action="store_true")
    asyncio.run(main(p.parse_args()))
