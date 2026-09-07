# Install the Structure Lab MCP server

The MCP server is a local Python process, separate from the Minecraft JAR. Your MCP client launches it over **stdio**. It then connects to the mod's authenticated localhost HTTP bridge. RCON is not needed.

## 1. Install the mod and Python

Complete [mod installation](INSTALL_MOD.md), launch Minecraft, and open a Structure Lab world. Install **Python 3.11 or later**; the tested version is Python 3.13.

Find the instance's `structurelab/connection.json`. Minecraft and the MCP process must run on the same machine and have access to the same files.

## 2. Install the release wheel

Download **`structurelab_mcp-0.2.0-py3-none-any.whl`** from the [v0.2.0 release](https://github.com/ewitulsk/MinecraftStructureInjector/releases/tag/v0.2.0). The package is distributed as a release asset; these instructions do not assume it is published to PyPI.

In PowerShell, change the wheel path if your downloads directory differs:

```powershell
py -3.13 -m venv "$HOME\structurelab-mcp\.venv"
& "$HOME\structurelab-mcp\.venv\Scripts\python.exe" -m pip install "$HOME\Downloads\structurelab_mcp-0.2.0-py3-none-any.whl"
& "$HOME\structurelab-mcp\.venv\Scripts\python.exe" -m structurelab.server --help
```

If you installed a different supported Python version, replace `-3.13` with that version. No environment activation is required. Pip installs the MCP SDK, NBT library, and image dependencies.

### Alternative: install from source

```powershell
git clone https://github.com/ewitulsk/MinecraftStructureInjector.git
cd MinecraftStructureInjector
py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
```

For this alternative, use the repository's `.venv\Scripts\python.exe` path in the configuration below. Building the Java mod is not required to install MCP from source.

## 3. Register with Codex

Use the **Codex CLI** to add the server. Replace the connection path if your instance is named differently:

```powershell
codex mcp add structurelab -- "$HOME\structurelab-mcp\.venv\Scripts\python.exe" -m structurelab.server --connection "$env:APPDATA\ModrinthApp\profiles\NeoForge 26.2\structurelab\connection.json"
codex mcp get structurelab
```

Start a fresh Codex session if the new tools do not appear in the current one. The client starts MCP when it connects; you do not need to keep a separate terminal running the server. If replacing an existing registration, inspect it first with `codex mcp get structurelab`, then remove/re-add it if its paths differ.

### Other MCP clients

Add a local stdio server using your client's MCP settings. Many clients accept this shape; adapt it to the client's configuration format and replace **both paths** with absolute paths on your machine:

```json
{
  "mcpServers": {
    "structurelab": {
      "command": "C:\\Users\\YOUR_NAME\\structurelab-mcp\\.venv\\Scripts\\python.exe",
      "args": [
        "-m",
        "structurelab.server",
        "--connection",
        "C:\\Users\\YOUR_NAME\\AppData\\Roaming\\ModrinthApp\\profiles\\NeoForge 26.2\\structurelab\\connection.json"
      ]
    }
  }
}
```

JSON clients generally do not expand `$HOME` or `%APPDATA%`; use literal absolute paths. Do not add extra embedded quotes around the command or individual arguments. `STRUCTURELAB_CONNECTION` can be used instead of `--connection`.

The HTTP bridge URL is **not an MCP HTTP endpoint**. Configure the Python command above, not the URL from `connection.json`. Do not copy the bearer token into your MCP client configuration; the server reads the current connection file automatically after Minecraft restarts.

## 4. Test a first build

Ask the connected agent:

> Check `lab_status`. Generate the example house into an absolute path in my build folder, validate it, then submit it with its returned views file. Poll the returned revision until complete. Retrieve the bedroom/beds and kitchen/counter captures so I can inspect them, then export the clean NBT and datapack to my export folder.

Expected sequence:

1. `lab_status` reports `connected: true` and `lab_world: true`.
2. `generate_example_house` returns `path` and `views_path`.
3. `validate_structure` reports `valid: true`.
4. `submit_structure` returns a revision UUID immediately.
5. `job_status` advances through validation, placement, and capture to `complete` with five captures.
6. `get_capture` returns an actual Minecraft PNG as MCP image content.
7. `export_structure` writes a clean `.nbt` and neighboring datapack `.zip`.

Keep Minecraft rendering and avoid input during the batch. Tools accept local absolute filesystem paths, not file uploads or web URLs. Export only after the revision completes.

For repeatable tests from a source checkout:

```powershell
$env:STRUCTURELAB_CONNECTION = "$env:APPDATA\ModrinthApp\profiles\NeoForge 26.2\structurelab\connection.json"
.\.venv\Scripts\python.exe scripts/mcp_probe.py
.\.venv\Scripts\python.exe scripts/verify_milestone.py 1
.\.venv\Scripts\python.exe scripts/verify_failure.py
.\.venv\Scripts\python.exe scripts/verify_milestone.py 2
```

These integration scripts replace the active lab structure. Ordinary unit tests use `.\.venv\Scripts\python.exe -m pytest -q` and do not connect to Minecraft.

## Troubleshooting

- **`No module named structurelab`:** use the virtual environment's Python executable, and install the wheel into that same environment.
- **Connection file missing:** launch Minecraft with the mod installed, then verify the instance path. A default profile name is only a convenience; `--connection` is the reliable override.
- **Connection refused:** Minecraft may be closed, or the file may belong to another instance. The bridge port changes on launch; keep pointing MCP at the file rather than a saved port.
- **No lab world:** create/open the Structure Lab preset world. The main menu and ordinary worlds cannot accept structure placement.
- **Stale revision:** a new submission became current. Use its UUID. After restarting Minecraft, submit again; job polling is currently in memory.
- **Images unavailable in the agent UI:** the client must support MCP image content. `list_captures` also returns filenames and labels for the files in the instance's revision directory.

See the [README](../README.md) for view-pad metadata, the full tool list, retention behavior, and milestone limits.
