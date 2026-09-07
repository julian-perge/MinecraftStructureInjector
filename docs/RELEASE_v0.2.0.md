# Structure Lab v0.2.0 — Nebraska State Capitol and large-build capture

A 185 × 130 × 185 vanilla-block Nebraska State Capitol, refined through three NBT → Minecraft screenshot → review iterations. The final model contains 253,376 non-air blocks, with 16 labeled views covering its exterior, gardens, public rooms, tower, and crown.

## Downloads

- `nebraska_state_capitol.nbt` — standalone Java 26.2 structure template.
- `nebraska_state_capitol.zip` — vanilla datapack containing `nebraska:state_capitol`.
- `nebraska_state_capitol.views.json` — camera definitions for Structure Lab.
- `nebraska_state_capitol_review.zip` — all three iterations' Minecraft PNGs, contact sheets, manifests, and verification evidence.
- `structurelab-26.2-0.2.0.jar` — updated NeoForge mod.
- `structurelab_mcp-0.2.0-py3-none-any.whl` — updated local MCP server and authoring library.
- `SHA256SUMS.txt` — artifact checksums.

The exported Capitol needs no mods. Install the datapack into a Java 26.2 world's `datapacks` folder, run `/reload`, load a clear 185 × 185 site, and place `nebraska:state_capitol` with `/place template`. [Exact commands, scale notes, references, and review history](https://github.com/ewitulsk/MinecraftStructureInjector/blob/v0.2.0/docs/NEBRASKA_CAPITOL.md).

## Lab changes

- Chunk-batched clearing and placement with progress reporting and recovery bounds.
- Streaming gzip NBT authoring with deterministic output and typed block-entity support.
- `recapture_views` creates a new screenshot set without replacing the structure.
- Per-view render-distance requests, restored after capture.
- Pause-on-focus-loss handling before placement; failed jobs stop pending placement work.
- A 16-million-position volume budget, one million explicit records, and a 32-million-position cleanup union.

The final Capitol placement and 16-view capture completed in about 54 seconds on the test machine. A camera-only recapture completed in 38 seconds with zero placement units. Verification compared 184 live block positions against the exported template, confirmed an all-vanilla palette and identical datapack payload, and checked removal of the previous successful runtime revision. A separate unmodded Minecraft 26.2 client loaded the exported datapack successfully and produced an additional exterior screenshot. The Java build and six Python tests passed. Maximum-volume and 1024-angle workloads remain unqualified.

## Install or update the tools

Requires Minecraft Java 26.2, NeoForge 26.2.0.77+ for that game version, Java 25, and Python 3.11+. Tested with NeoForge 26.2.0.79 and Python 3.13 on Windows. Stop Minecraft before replacing the JAR; keep only one enabled Structure Lab version. Upgrade the wheel in the Python environment used by your MCP client.

- [Install the mod](https://github.com/ewitulsk/MinecraftStructureInjector/blob/v0.2.0/docs/INSTALL_MOD.md)
- [Install and configure MCP](https://github.com/ewitulsk/MinecraftStructureInjector/blob/v0.2.0/docs/INSTALL_MCP.md)
- [Tool reference](https://github.com/ewitulsk/MinecraftStructureInjector/blob/v0.2.0/README.md)

The model interprets the supplied tour and floor plan at block resolution. Office details, murals, mosaics, and sculpture are simplified rather than exact reproductions. The lab still requires a graphical singleplayer client; entity templates, multiple palettes, simulation validation, dedicated-server/RCON operation, disk quotas, and automatic failed-revision pruning are not implemented.
