# Minecraft Structure Lab

**Local development branch: Minecraft 1.21.1 / NeoForge 21.1.250 / Java 21.** See [background testing and local installation](docs/BACKGROUND_TESTING.md) and the [Raid research notes](docs/RAID_RESEARCH.md). The release descriptions below document historical 26.2 builds. This branch has not been pushed or released.

A NeoForge mod and local MCP server for generating NBT structures, placing each revision into a dedicated superflat world, and returning labeled screenshots rendered by Minecraft.

The local 1.21.1 build includes [Classic Raid](docs/RAID.md), with [121 camera views](gallery/raid/index.html), four review passes and verified connecting walking routes.

Browse the [build galleries](gallery/README.md), starting with the [Nebraska State Capitol](gallery/nebraska-capitol/README.md): three iterations, 16 final views, and an unmodded Minecraft check.

Version 0.2.0 extends the generate → validate → replace → capture → revise → export loop to large builds. The Nebraska State Capitol example occupies 185 × 130 × 185 blocks and was refined through three real Minecraft capture reviews. It uses one real client camera sequentially. No extra renderer, RCON server, or manual camera cycling is needed.

## Install

For this local Minecraft 1.21.1 branch, follow [local installation and background testing](docs/BACKGROUND_TESTING.md). The [published releases](https://github.com/ewitulsk/MinecraftStructureInjector/releases/latest) describe historical Minecraft 26.2 builds.

- **[Install the Minecraft mod](docs/INSTALL_MOD.md)** — Modrinth setup, supported versions, and creating the Structure Lab world.
- **[Install the MCP server](docs/INSTALL_MCP.md)** — Python setup, Codex registration, generic MCP configuration, and a first capture.

The current tested setup is Windows, Minecraft Java **1.21.1**, NeoForge **21.1.250**, Java **21**, and Python **3.11+**. The linked historical 26.2 releases require their matching Minecraft, NeoForge and Java versions. Minecraft and MCP run on the same machine. The JAR alone does not install the MCP server.

![Nebraska State Capitol captured automatically in Minecraft](docs/images/capitol-aerial.jpg)

[Get the Capitol model, references, placement instructions, and review history](docs/NEBRASKA_CAPITOL.md).

The mod exposes a local HTTP bridge; the external Python process exposes MCP over stdio. Codex or another MCP client starts that process automatically. The bridge creates an ephemeral localhost port and bearer token in `<instance>/structurelab/connection.json`. Keep the connection file private.

## MCP workflow

| Tool | Purpose |
| --- | --- |
| `lab_status` | Read world readiness, origin, resource limits, and active job. |
| `list_blocks` | Query live registry IDs and legal properties. |
| `generate_structure` | Build an NBT using JSON `set`, `fill`, and `room` operations. |
| `generate_example_house` | Generate the furnished example, revision 1 or 2. |
| `validate_structure` | Validate NBT coordinates, palette, registry IDs, properties, and limits. |
| `submit_structure` | Import a file with optional views JSON; replace and capture automatically. |
| `recapture_views` | Capture the current completed structure again, optionally with revised cameras, without clearing or placing blocks. |
| `job_status` / `cancel_job` | Poll or cancel a specific revision. |
| `list_captures` / `get_capture` | List labels and return individual MCP image content. |
| `inspect_blocks` | Read authoritative placed block states. |
| `inspect_player_clearance` | Check player-sized collision and floor support at relative feet positions. |
| `test_walking_route` | Exercise native player movement without jumping in the hidden lab. |
| `export_structure` | Copy the clean NBT and package a vanilla 1.21.1 datapack ZIP. |

Example calls, using absolute paths:

```text
generate_example_house(output_path="D:/builds/house.nbt", revision=1)
validate_structure(path="D:/builds/house.nbt")
submit_structure(path="D:/builds/house.nbt", views_path="D:/builds/house.views.json")
job_status(revision="<returned UUID>")
list_captures(revision="<returned UUID>")
get_capture(revision="<returned UUID>", view_id="bedroom", angle_id="beds")
export_structure(revision="<returned UUID>", output_path="D:/exports/house.nbt")
```

Wait for completion before exporting or submitting another revision. Overlapping submissions are rejected. Old revision IDs are rejected once a new job becomes current.

## Authoring NBT and views

The Python library supports sparse blocks, explicit air, block states, and typed block-entity NBT:

```python
from structurelab import Structure

s = Structure((12, 8, 12))
s.room((0, 0, 0), (11, 6, 11), wall="oak_planks", floor="stone_bricks")
s.set((5, 1, 0), "air")
s.set((5, 2, 0), "air")
position = (5.5, 1, -6)
s.view("spawn", position, [
    {"id": "front", **s.look_at(position, (5.5, 3, 5))}
], spawn=True, label="Front entrance")
s.save("D:/builds/my-house.nbt")
```

Views may be a sidecar JSON list, or embedded `structurelab:view_pad` blocks. `Structure.view(..., pad=(x,y,z))` writes a pad with block-entity metadata. Each pad has a unique ID, label, feet position relative to the structure origin, and ordered angles:

```json
[
  {
    "id": "bedroom",
    "label": "Bedroom",
    "position": [11.5, 1, 6.5],
    "eye_height": 1.62,
    "spawn": false,
    "angles": [
      {"id": "beds", "yaw": -90, "pitch": 10, "fov": 70},
      {"id": "window", "yaw": 0, "pitch": 0, "fov": 70}
    ]
  }
]
```

Minecraft yaw 0 faces +Z, yaw -90 faces +X; positive pitch looks down. FOV defaults to 70 and must be 30–110. Eye height defaults to 1.62 and must be 0–4. Optional `render_distance` is an integer from 4 to 24 chunks on a view; a batch temporarily raises the client distance to the largest requested value and restores the previous setting afterward. IDs must use letters, digits, underscores or hyphens, at most 64 characters. Angle IDs are unique within their view.

For direct NBT authoring, a pad stores the JSON object as the string `nbt.view.json`. If the JSON omits `position`, the camera uses the block center in X/Z and its Y coordinate as feet height. Optional `nbt.view.replacement` is a vanilla palette-style compound with `Name` and optional `Properties`. The default replacement is air. Pad metadata is extracted before placement; pad block entities and unused pad palette entries are stripped from the export. A pad replacement does not preserve a separate block entity.

Mark one view `spawn: true`. Its first angle is captured first and the player returns there after the batch. With no views, an exterior view is generated. With views but no spawn flag, the first view is the return point. An in-game pad configuration screen is not part of this milestone.

## Replacement and capture behavior

- One structure at fixed origin `(0, -60, 0)` above the flat grass layer.
- Each submission is copied into an immutable revision directory before reading. No partial-file watcher races.
- The old/new bounding box is cleared one chunk column per server tick, skipping empty sections. Non-player entities in that box are removed. The template is placed one chunk at a time with native block-entity loading and suppressed incidental placement side effects. Jobs report `clearing` / `placing`, `processed`, and `work_total`.
- Placement temporarily disables pause-on-focus-loss before beginning the chunk batches; capture restores the earlier setting.
- The lab freezes simulation and fixes daylight/weather. This is visual inspection; redstone and mob simulation validation are deferred.
- Before each screenshot, the mod waits for the player/camera position and angles, nearby chunks, lighting work, and section rendering to settle. A view has a 60-second readiness timeout.
- Captures use Minecraft's actual framebuffer at **1920×1080 PNG**, with HUD and view bobbing hidden. A windowed client is resized during the batch and restored afterward. Fullscreen must already be 1920×1080 or the batch reports an error.
- Files use `<view-id>__<angle-id>.png`. The manifest includes revision UUID, input SHA-256, labels, position, yaw, pitch, FOV and image dimensions.
- The previous successful revision remains on disk while a replacement is processed. After a successful replacement, its old revision directory and screenshots are removed. Failed revisions are retained for diagnosis and currently need manual cleanup. Explicit exports and the test evidence folders are never automatically deleted.
- A placement recovery ledger persists the affected bounding box across world reloads. The next submission clears it. This is recovery on the next submission, not transactional rollback to the previous build.

Instance data lives under `structurelab/revisions/<UUID>/`; `structurelab/latest.json` points to the last success. Job polling is in memory: after restarting Minecraft, submit again to make a revision available through MCP.

## Current limits

Limits are explicit resource budgets, not claims that every maximum-size combination has been qualified.

- Width and length: at most 1024 each. Height: at most the world permits; the default lab origin permits **380** blocks through Y=319.
- Bounding volume: **16,000,000 positions**, even for sparse NBT. Combined old/new cleanup bounding volume: **32,000,000 positions**. At most **1,000,000 explicit block records**, 64 MiB compressed input, and a 256 MiB NBT accounting budget. Very different shapes may require a fresh lab world.
- Up to 1024 angle definitions are accepted. Tested examples include the five-angle house and the 429,341-record Capitol with 16 angles at 1920×1080. Raid additionally qualified 121 angles and a 496,949-record portable export on 1.21.1. The full 1024-angle limit and maximum volume have not been performance-qualified.
- One palette; entity templates and multi-palette structures are rejected. Block entities are supported, but arbitrary mod-specific block-entity behavior is not comprehensively validated.
- No disk quota, automatic failed-job pruning, dedicated-server/RCON workflow, or shader compatibility guarantee yet.
- Export removes Structure Lab pads. Builds using other mods retain those dependencies; `export_structure` reports their namespaces. The example exports with no non-vanilla dependencies.

## Vanilla datapack export

`export_structure` writes the requested `.nbt` and a neighboring `.zip` with:

```text
pack.mcmeta
data/lab_export/structure/house.nbt
```

Copy the ZIP into a target world's `datapacks` folder, run `/reload`, then:

```text
/place template lab_export:house 0 -60 0
```

Namespace and name can be changed in the export call. The exported format on this branch targets Minecraft Java **1.21.1**, DataVersion **3955**, datapack format **48**.

## Building the mod and MCP server

Run these commands from the repository root in PowerShell. Set the Java path to your Java 21 installation:

```powershell
$env:JAVA_HOME = 'C:\Program Files\Java\jdk-21.0.11'
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev,research]"
.\gradlew.bat build --console=plain
.\.venv\Scripts\python.exe -m pytest -q
```

The mod output is `build/libs/structurelab-1.21.1-0.3.0-dev.jar`. Copy it into a stopped Minecraft 1.21.1 / NeoForge 21.1.250 instance's `mods` folder, launch, and create a world with the Structure Lab preset. The editable Python installation provides the MCP server. See [local installation and MCP configuration](docs/BACKGROUND_TESTING.md) for ordinary and background launches.

## Structure building and testing process

The working loop is **research → generate NBT and cameras → validate → place and capture in Minecraft → review images and movement → revise → export**. A successful generation or screenshot batch alone does not establish that a build looks right or is playable.

### 1. Research and author the structure

Establish the layout, scale, landmarks, materials and connecting paths from overhead imagery and multiple ground-level references. Record sources and uncertain measurements. For Raid, the [research notes](docs/RAID_RESEARCH.md) explain the original BO2 scene, metre-scale checks, reference renders, and Blender preprocessing commands. Downloaded reference assets and the sampled grid are local inputs, not bundled dependencies; a fresh checkout needs those inputs before running the Raid generator.

Use the Python `Structure` builder or MCP generation tools to create a vanilla block palette and named cameras. Include an exterior overview, entrances, key interiors, and views along important routes. Camera positions are feet coordinates relative to the structure origin; each position can have multiple labeled angles. Adapt stairs, slabs, headroom and openings for Minecraft movement. Include explicit air where portable placement must clear interior space.

For Raid, after preparing `artifacts/raid/reference-grid`, generate into a fresh evidence folder:

```powershell
.\.venv\Scripts\python.exe examples/raid.py --revision 4 --explicit-air --output artifacts/raid/new-review
```

This produces `raid.nbt`, `raid.views.json`, material/build metadata and `route-repairs.json`. Revision options 1–4 select the refinement stages; revision 4 includes the latest accessibility fixes. The retained review history documents earlier results, which may precede subsequent fixes to that stage's generator.

### 2. Start an isolated background client

The launcher follows the approach used by Planetary Sable: a separate game directory, an invisible and unfocused GLFW window, no mouse capture, and actual GPU rendering. Hidden behavior is opt-in; ordinary Minecraft launches remain interactive.

```powershell
.\.venv\Scripts\python.exe scripts/launch_hidden.py --scenario smoke --jar build/libs/structurelab-1.21.1-0.3.0-dev.jar
.\.venv\Scripts\python.exe scripts/launch_hidden.py --scenario lab --jar build/libs/structurelab-1.21.1-0.3.0-dev.jar --directory artifacts/my-lab
$env:STRUCTURELAB_CONNECTION = (Resolve-Path artifacts/my-lab/structurelab/connection.json).Path
.\.venv\Scripts\python.exe -c "from structurelab.server import lab_status; print(lab_status())"
```

The smoke scenario verifies a rendered frame and exits. The lab scenario waits for readiness, creates or reopens its own lab world, and stays running. Confirm `lab_world: true` before submission. `--jar` tests the packaged mod instead of loose development classes, while still using Gradle's Minecraft runtime and assets. Logs and launch information stay in the isolated directory. Keep its connection file private.

### 3. Validate, submit and capture

```powershell
.\.venv\Scripts\python.exe scripts/capture_build.py artifacts/raid/new-review --name raid
```

This script initializes a real MCP stdio session, validates the NBT against the live game, submits it, waits for automatic replacement and camera capture, retrieves the images, and exports the result. It replaces the active lab structure. For another build, supply a folder containing matching `<name>.nbt` and `<name>.views.json` files and change `--name`.

Evidence includes labeled 1920×1080 PNGs, `manifest.json`, timing, review contact sheets, and clean NBT/datapack exports. Inspect every contact sheet and open individual images where details are unclear. Check scale, silhouettes, materials, lighting, camera obstruction, interior furnishings and route entrances. Write the findings and intended corrections in that iteration's `review.md` before generating the next version.

For camera-only changes, add `--recapture` to the capture command. It captures the currently loaded completed structure without replacing blocks; ensure that structure is the intended one. Preserve evidence before another capture or submission overwrites it.

### 4. Test movement and refine

Static clearance and walking tests complement visual inspection. `inspect_player_clearance` checks a player-sized collision box and supporting floor. `test_walking_route` invokes native server player movement and stair collision without jumping, then restores player state. Walking tests require the isolated hidden lab and a completed capture job.

For the currently loaded Raid revision:

```powershell
.\.venv\Scripts\python.exe scripts/walk_routes.py artifacts/raid/new-review
```

The script reads that folder's route definitions, tests each in both directions, and saves `native-walking.json`. Check every result and the printed passing count; the script does not currently exit nonzero merely because a route failed. The loaded structure must match the route file. Fix failed landings, blocked headroom or discontinuities in the generator, regenerate, recapture the affected views, and rerun movement checks. Run a full visual regression when changes affect broader geometry.

These checks establish selected collision and traversal behavior, not keyboard input, multiplayer combat balance, redstone behavior, or every possible route.

### 5. Export and retain review evidence

Export only the completed, reviewed revision. Check the reported dependency namespaces; a vanilla deliverable should have none. Keep the clean NBT, datapack, camera sidecar, manifest and verification results together. Place the exported datapack using `/place template` as described above; the structure-block editor is not the intended loader for large builds.

Store compact galleries under `gallery/<build-name>/` so other builds can coexist. The mod prunes the previous successful revision after successful replacement, but copied evidence and failed jobs remain until explicitly cleaned up. Keep review sheets and final evidence when removing redundant captures.

Stop the isolated client after testing:

```powershell
.\.venv\Scripts\python.exe -c "from structurelab.server import rpc; rpc('shutdown')"
```

### Raid results and retained evidence

The final classic Los Angeles Raid reconstruction is **150 × 64 × 170 blocks**, on a **one-block-per-metre grid**, with **496,949 block records** including interior air. Minecraft stairs, slabs, openings and furniture deliberately adapt the source geometry for playability.

| Stage | Review and changes |
| --- | --- |
| [Pass 1](gallery/raid/pass-1/review.md) | 121 captures; baseline layout and material conversion exposed color and camera issues. |
| [Pass 2](gallery/raid/pass-2/review.md) | 121 captures; corrected materials, camera placement and initial stairs. |
| [Pass 3](gallery/raid/pass-3/review.md) | 121 captures; lighting, court detail and connecting routes; movement checks exposed stair junction failures. |
| [Pass 4](gallery/raid/pass-4/review.md) | 121 captures; furnishings, interior cameras and landing refinements. |
| Final qualification | 121-view regression, followed by 13 targeted junction rechecks and corrected stair transitions. |

The qualified build passed **56/56 native walking checks** across 28 routes in both directions without jumping, plus clear/support checks at **29/29 ground camera stations**. The packaged JAR passed the hidden-client smoke check, the Gradle build passed, and six Python tests passed. Testing used NeoForge 1.21.1; a separate unmodded client was not tested for Raid.

Browse the [121-angle gallery](gallery/raid/index.html), [verification data](gallery/raid/verification/verification.json), and [build/download instructions](docs/RAID.md). The local `scripts/package_raid.py` and `scripts/raid_gallery.py` assemble this specific retained Raid run; they expect its `final` and `qualified` evidence folders and are not generic build commands. Generated release files live under ignored `artifacts/local-release/`. Nothing is published automatically.

## Earlier milestone verification

The [Capitol case study](docs/NEBRASKA_CAPITOL.md) documents three large-build iterations. Generate it with `python examples/nebraska_capitol.py --revision 3 --output artifacts/capitol/iteration-3/capitol.nbt`, then run `python scripts/capture_capitol.py artifacts/capitol/iteration-3` with the lab open. Add `--recapture` to exercise camera-only recapture of the current build. These commands replace the active lab structure or its capture set.

With the lab world open, these scripts use real MCP initialization and stdio tool calls:

```powershell
.\.venv\Scripts\python.exe scripts/mcp_probe.py
.\.venv\Scripts\python.exe scripts/verify_milestone.py 1
.\.venv\Scripts\python.exe scripts/verify_failure.py
.\.venv\Scripts\python.exe scripts/verify_milestone.py 2
```

The integration scripts intentionally replace the current lab structure. They generate a furnished house, obtain five images through MCP, inspect block states, and export NBT/datapacks. Revision 2 shrinks the bounds, removes the gold sentinel, and changes blue carpet to red.

Local integration runs save evidence under `artifacts/evidence/v1` and `v2`. These generated files are ignored by Git. The original milestone verification also saved vanilla evidence locally. The vanilla test uses a separate **Structure Lab Vanilla Verification** instance created and launched through Modrinth, with no mods installed. Its log confirms vanilla loaded `lab_export:house`; `vanilla/exterior.png` shows the placed export.

The original local run recorded the installed JAR hash and completed checks in `artifacts/evidence/verification.json`. A portable summary is in [milestone verification](docs/VERIFICATION.md). The failure test verifies that an invalid eye height produces a pollable failed job while preserving the previous world and successful images. Visual review also caught a camera on a wall boundary; the example's kitchen viewpoint was moved into open space and recaptured successfully.

## License

[MIT](LICENSE). This project is not affiliated with Mojang or Microsoft.
