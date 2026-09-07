# Structure Lab v0.1.0 — milestone 1

Generate Minecraft NBT structures through MCP, replace them in a dedicated superflat world, and automatically inspect labeled screenshots rendered by Minecraft.

## Downloads

- **`structurelab-26.2-0.1.0.jar`** — install this into a Minecraft Java 26.2 NeoForge instance.
- **`structurelab_mcp-0.1.0-py3-none-any.whl`** — the separate local MCP server and Python NBT authoring library.
- **`SHA256SUMS.txt`** — checksums for both artifacts.

## Installation

1. In Modrinth, create or select a **NeoForge 26.2** instance and stop it.
2. Use **Content → Upload files** to install the JAR, then launch Minecraft.
3. Create a world using **World Type: Structure Lab**.
4. Install Python 3.11+ and the MCP wheel in a virtual environment.
5. Register the Python stdio server with your MCP client, pointing `--connection` at `<instance>/structurelab/connection.json`.

Full instructions:

- [Install the mod](https://github.com/ewitulsk/MinecraftStructureInjector/blob/v0.1.0/docs/INSTALL_MOD.md)
- [Install and configure MCP](https://github.com/ewitulsk/MinecraftStructureInjector/blob/v0.1.0/docs/INSTALL_MCP.md)
- [Tool reference and authoring examples](https://github.com/ewitulsk/MinecraftStructureInjector/blob/v0.1.0/README.md)

## Included

- Structure Lab superflat preset, local authenticated bridge, and MCP stdio server.
- JSON operations and a Python library for NBT generation, plus file import.
- Named view-pad metadata and sidecar camera definitions.
- Automatic sequential 1080p screenshots with labels, coordinates, angles, and revision identity.
- Replacement cleanup, previous-success screenshot retention until a new success, and clean NBT/datapack export.
- Furnished example house and scripts exercising real MCP tool calls.

## Compatibility and limits

Requires Minecraft **Java 26.2**, Java **25** for the game, NeoForge **26.2.0.77+ for 26.2**, and Python **3.11+** for MCP. Tested on Windows with NeoForge **26.2.0.79** and Python **3.13**. The MCP process and graphical Minecraft client run on the same machine.

This is the first milestone. One active structure is supported, with a **2,000,000-position** bounding-volume cap and **4,000,000-position** cleanup-box cap. Horizontal dimensions may reach 1024, but height at the default origin is limited to 380. Up to 1024 angles are accepted by the schema; five-angle batches were tested. Large-scale performance, entity templates, multi-palette structures, RCON/dedicated-server operation, ad hoc recapture, simulation validation, and automatic failed-job pruning are deferred.

The build and five Python tests passed. The live MCP integration verified generation, replacement, five 1080p captures, invalid-input handling, and export. A separate unmodded 26.2 instance loaded the exported datapack successfully. [Verification details](https://github.com/ewitulsk/MinecraftStructureInjector/blob/v0.1.0/docs/VERIFICATION.md).
