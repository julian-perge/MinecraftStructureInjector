# Classic Raid — Minecraft 1.21.1

A vanilla-block recreation of the classic Black Ops II / Cold War Los Angeles mansion, on a one-block-per-metre grid. The structure occupies **150 × 64 × 170 blocks** and contains 496,949 block records including interior air. Source scale is supported by measured scene objects; local stairs, slabs, openings and furniture are adapted for Minecraft playability.

## Local artifacts

- [Vanilla NBT](../artifacts/local-release/raid.nbt)
- [Datapack](../artifacts/local-release/raid-datapack.zip)
- [Structure Lab mod JAR](../artifacts/local-release/structurelab-1.21.1-0.3.0-dev.jar)
- [MCP wheel](../artifacts/local-release/structurelab_mcp-0.3.0.dev0-py3-none-any.whl)
- [Installation and placement instructions](../artifacts/local-release/README.md)
- [Background testing](BACKGROUND_TESTING.md)
- [121-angle gallery](../gallery/raid/index.html) and [review history](../gallery/raid/README.md)
- [Reference research and reproduction](RAID_RESEARCH.md)

These artifacts are local and ignored by Git. Nothing was pushed or published.

## Verification

Four generate/capture/review passes produced 121 views each. A further 121-view regression and 13-view junction recheck followed the final accessibility corrections. All 28 selected connecting routes passed in both directions using native server player movement without jumping (56/56). All 29 ground camera stations have clear player collision boxes and floor support.

The packaged JAR passed an isolated hidden-client smoke test at 1920 × 1080 with no focus or cursor capture. The Java build and six Python tests passed. Export checks confirmed vanilla dependencies, Minecraft 1.21.1 NBT version 3955 and datapack format 48. File hashes are recorded in [verification.json](../artifacts/local-release/verification.json).

Testing used NeoForge 1.21.1; a separate unmodded client was not tested. Route checks do not establish combat balance, every possible movement path, or multiplayer behavior. The build supplies the map, not a Call of Duty game mode. Small geometry and decoration are necessarily stylized on the metre grid.
