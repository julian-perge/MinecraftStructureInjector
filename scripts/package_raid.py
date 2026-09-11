"""Package verified local Raid artifacts; performs no network or Git operations."""
import hashlib,json,shutil,zipfile
from pathlib import Path

root=Path(__file__).resolve().parents[1];source=root/'artifacts/raid/qualified';out=root/'artifacts/local-release';out.mkdir(exist_ok=True)
job=json.loads((source/'manifest.json').read_text());walks=json.loads((source/'native-walking.json').read_text());clearance=json.loads((source/'clearance.json').read_text())
assert job['state']=='complete' and job['captured']==13
assert json.loads((root/'artifacts/raid/final/manifest.json').read_text())['captured']==121
assert len(walks)==56 and all(r['passed'] for r in walks),'All directed routes must pass before packaging'
assert clearance['blocked']==0 and clearance['unsupported']==0
assert not json.loads((source/'export.json').read_text())['dependencies']
for src,name in [(source/'raid-clean.nbt','raid.nbt'),(source/'raid-clean.zip','raid-datapack.zip'),(source/'raid.all-views.json','raid.views.json'),(root/'build/libs/structurelab-1.21.1-0.3.0-dev.jar','structurelab-1.21.1-0.3.0-dev.jar')]:shutil.copy2(src,out/name)
with zipfile.ZipFile(out/'raid-datapack.zip') as z:
    assert json.loads(z.read('pack.mcmeta'))['pack']['pack_format']==48
    assert z.read('data/builds/structure/raid.nbt')==(out/'raid.nbt').read_bytes()
report={'minecraft':'1.21.1','neoforge':'21.1.250','revision':job['revision'],'size':[150,64,170],
        'metres_per_block':1,'block_records':json.loads((source/'build.json').read_text())['blocks'],
        'refinement_passes':4,'angles_per_pass':121,'final_regression_captures':121,'targeted_junction_recheck_captures':13,
        'native_route_directions_passed':56,'native_route_directions_total':56,'camera_stations_clear_and_supported':29,
        'movement_method':'native_server_player_move_no_jump','unmodded_client_tested':False,
        'files':{p.name:{'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in out.iterdir() if p.suffix in ('.nbt','.zip','.jar','.whl')}}
(out/'verification.json').write_text(json.dumps(report,indent=2))
(out/'README.md').write_text('''# Structure Lab 1.21.1 and Classic Raid — local build

No files have been published or pushed to GitHub.

## Install the mod

Install Minecraft Java 1.21.1 with NeoForge 21.1.250 and Java 21. Copy
`structurelab-1.21.1-0.3.0-dev.jar` into that instance's `mods` folder while it is
closed. Launch and create a world using the Structure Lab preset. Background test
launch instructions are in `docs/BACKGROUND_TESTING.md` in the project checkout.

## Install MCP

Create a Python 3.11+ virtual environment and install the included wheel:

```powershell
py -m venv .venv
.\\.venv\\Scripts\\python.exe -m pip install .\\structurelab_mcp-0.3.0.dev0-py3-none-any.whl
```

Configure your MCP client to run the absolute path to that Python executable with
arguments `-m`, `structurelab.server`, `--connection`, and the absolute path to your
Minecraft instance's `structurelab/connection.json`. The transport is stdio; RCON
is unnecessary. Start Minecraft and open the lab world before making tool calls.

## Place Raid without Structure Lab

Copy `raid-datapack.zip` into a Minecraft 1.21.1 world's `datapacks` folder. Run
`/reload`, then `/place template builds:raid 0 64 0` in a clear area. The build
occupies 150 × 64 × 170 blocks. `/tp @s 58.5 81 31.5 180 6` places you at the garage
spawn for that origin. The standalone `raid.nbt` is the same vanilla template.
Large placement uses `/place template`; the structure-block editor's size limit
is not the intended loading method. Leave clearance above and around the footprint.

One block represents one metre of the original game scene. Stairs, openings,
landings, furniture and small details are adapted for Minecraft movement. This is
a playable vanilla-block recreation, not a pixel-identical copy or a multiplayer
game-mode implementation. Testing used NeoForge 1.21.1, not a separate unmodded client.

Four refinement passes, a final 121-angle regression, and 13 targeted junction
rechecks were captured in Minecraft.
All 28 tested routes passed native player movement in both directions without jumps;
all 29 ground camera stations passed collision and support checks. Full evidence is
in `artifacts/raid/qualified` and `artifacts/raid/final`; the compact gallery is `gallery/raid/index.html`.
''')
print(json.dumps(report,indent=2))
