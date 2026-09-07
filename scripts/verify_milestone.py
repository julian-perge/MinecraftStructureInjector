"""Integration test: a real MCP client drives generation, validation, placement and captures."""
import asyncio
import base64
import json
from pathlib import Path
import sys
import time
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def main():
    version=int(sys.argv[1]) if len(sys.argv)>1 else 1
    evidence=Path(f"artifacts/evidence/v{version}").resolve();evidence.mkdir(parents=True,exist_ok=True)
    params=StdioServerParameters(command=sys.executable,args=["-m","structurelab.server"])
    async with stdio_client(params) as (read,write):
        async with ClientSession(read,write) as session:
            await session.initialize()
            async def call(name,**args):
                r=await session.call_tool(name,args)
                if r.isError:raise RuntimeError(str(r.content))
                return json.loads(next(c.text for c in r.content if c.type=="text"))
            status=await call("lab_status");assert status["lab_world"]
            fixture=await call("generate_example_house",output_path=str(evidence/"input.nbt"),revision=version)
            print("Generated:",fixture,flush=True)
            valid=await call("validate_structure",path=fixture["path"]);assert valid["valid"]
            job=await call("submit_structure",**fixture)
            revision=job["revision"];start=time.monotonic();last=None
            while job["state"] not in ("complete","failed","cancelled"):
                if time.monotonic()-start>150:raise TimeoutError("Capture batch did not finish")
                await asyncio.sleep(2)
                job=await call("job_status",revision=revision)
                progress=(job["state"],job["captured"])
                if progress!=last:print("Job:",revision,*progress,flush=True);last=progress
            (evidence/"manifest.json").write_text(json.dumps(job,indent=2))
            assert job["state"]=="complete",job
            assert job["captured"]==5,job
            captures=await call("list_captures",revision=revision)
            for c in captures["captures"]:
                r=await session.call_tool("get_capture",dict(revision=revision,view_id=c["id"],angle_id=c["angle"]))
                assert not r.isError
                image=next(v for v in r.content if v.type=="image")
                (evidence/c["file"]).write_bytes(base64.b64decode(image.data))
            states=await call("inspect_blocks",positions=[[18,2,15],[10,1,5],[13,1,7],[10,1,11]])
            (evidence/"states.json").write_text(json.dumps(states,indent=2))
            assert "gold_block" in states["[18,2,15]"] if version==1 else "air" in states["[18,2,15]"]
            assert ("blue_carpet" if version==1 else "red_carpet") in states["[10,1,5]"]
            assert "air" in states["[13,1,7]"]
            exported=await call("export_structure",revision=revision,output_path=str(evidence/"house.nbt"))
            (evidence/"export.json").write_text(json.dumps(exported,indent=2))
            print("PASS:",json.dumps({"revision":revision,"captures":5,"export":exported,"states":states}),flush=True)


asyncio.run(main())
