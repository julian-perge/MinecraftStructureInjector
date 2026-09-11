# Background Minecraft testing (1.21.1)

This local branch targets Minecraft Java 1.21.1, NeoForge 21.1.250, and Java 21. Historical GitHub releases target 26.2; they are not the JAR to install for this branch.

The launcher uses a separate game directory under `artifacts`. It disables NeoForge's early splash window, creates the GLFW window invisible and unfocused, prevents mouse capture, and checks those conditions on every rendered frame. It renders with the real Minecraft client and GPU. No desktop clicks, keyboard input, or Modrinth instance changes are involved. The approach is adapted from Planetary Sable's hidden client tests.

From the repository root in PowerShell:

```powershell
$env:JAVA_HOME = 'C:\Program Files\Java\jdk-21.0.11'
.\gradlew.bat build --console=plain
.\.venv\Scripts\python.exe scripts/launch_hidden.py --scenario smoke
.\.venv\Scripts\python.exe scripts/launch_hidden.py --scenario lab --directory artifacts/my-lab
$env:STRUCTURELAB_CONNECTION = (Resolve-Path artifacts/my-lab/structurelab/connection.json).Path
.\.venv\Scripts\python.exe -c "from structurelab.server import lab_status; print(lab_status())"
```

Set `STRUCTURELAB_JAVA_HOME` if Java 21 is installed elsewhere. Install the Python environment with `py -m venv .venv` and `.\.venv\Scripts\python.exe -m pip install -e ".[dev]"` when needed.

The smoke scenario exits after verifying a rendered title-screen image. The lab scenario creates or reopens its own Structure Lab world and stays running for MCP requests. The launcher waits for `HIDDEN_LAB_READY` before returning; then verify `lab_status` reports `lab_world: true`. Each launch records its process ID and frozen Java launch arguments in its game directory. The connection file is private.

To test the packaged JAR rather than loose development classes, add `--jar build/libs/structurelab-1.21.1-0.3.0-dev.jar`. The launcher copies it into the isolated `mods` folder and removes the development mod directories from the launch command. This still uses Gradle's Minecraft runtime and assets.

Capture any generated `<name>.nbt` and `<name>.views.json` pair through actual MCP:

```powershell
.\.venv\Scripts\python.exe scripts/capture_build.py artifacts/my-build --name my_build
```

The script saves labeled 1920×1080 captures, paginated contact sheets, a manifest, timing, clean NBT, and a Minecraft 1.21.1 datapack. Review the actual images before editing and submitting the next iteration. Generation alone is not a review pass.

Stop the isolated client gracefully:

```powershell
.\.venv\Scripts\python.exe -c "from structurelab.server import rpc; rpc('shutdown')"
```

The shutdown operation is rejected by ordinary interactive clients. Do not delete or replace an active game directory. Failed runs retain their logs for diagnosis.

For an ordinary launcher installation, copy `build/libs/structurelab-1.21.1-0.3.0-dev.jar` into an offline Minecraft 1.21.1 / NeoForge 21.1.250 instance's `mods` folder, then start it normally and select the Structure Lab world preset. Hidden behavior is opt-in and does not change ordinary launches.

For MCP, use this checkout's Python environment and pass `--connection` followed by the absolute path to the intended instance's connection file. The transport remains stdio MCP → authenticated localhost HTTP; no RCON setup is required.

Example local stdio configuration (replace the paths if your checkout differs):

```json
{
  "mcpServers": {
    "structurelab": {
      "command": "D:\\MinecraftMods\\MinecraftStructureInjector\\.venv\\Scripts\\python.exe",
      "args": ["-m", "structurelab.server", "--connection", "D:\\MinecraftMods\\MinecraftStructureInjector\\artifacts\\my-lab\\structurelab\\connection.json"]
    }
  }
}
```

`inspect_player_clearance` tests static player-sized collision and support.
`test_walking_route` additionally exercises the server player's native movement,
gravity displacement and stair collision with no jumps. It is available only in an
isolated hidden lab after capture completes, accepts up to 512 closely spaced feet
positions, and restores player position/mode afterwards. It does not simulate
keyboard input, combat, or multiplayer gameplay.
