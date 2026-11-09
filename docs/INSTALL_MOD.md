# Install Structure Lab for Minecraft

## Requirements

- Minecraft **Java Edition 26.1.2**.
- NeoForge **26.1.2.106 or newer for Minecraft 26.1.2**. Tested with **26.1.2.106**.
- Java **25** for the game. Modrinth can manage the game runtime.
- A local graphical Minecraft client. This version targets singleplayer and was tested in a NeoForge dev client on macOS. Windows and Modrinth have not been tested on 26.1.2.

Fabric, Forge, Bedrock Edition, and a headless dedicated server are not supported by this release. No other content mods are required.

## Install with Modrinth

1. Open Modrinth. Use an existing **NeoForge 26.1.2** instance, or select **Create instance → Custom setup → NeoForge → Game version 26.1.2**.
2. Stop that instance before installing or updating the mod.
3. Build the JAR from the `26.1.2` branch of this repository with `.\gradlew.bat build`, or `./gradlew build` outside Windows. It writes **`build/libs/structurelab-26.1.2-0.2.0.jar`**. There is no 26.1.2 release, and the [v0.2.0 release](https://github.com/ewitulsk/MinecraftStructureInjector/releases/tag/v0.2.0) is the 26.2 build.
4. Open the instance and select **Content → Upload files**. Choose that JAR. Alternatively, copy it into the instance's `mods` directory.
5. Confirm Structure Lab is enabled and launch the instance. When updating, remove any older Structure Lab JAR with a different filename so only one version is installed.

Do not install GitHub's source ZIP, the MCP wheel, or a `-sources.jar` as a Minecraft mod.

## Create a lab world

1. Select **Singleplayer → Create New World**.
2. Give it a recognizable name, such as **Structure Lab**.
3. In the **World** tab, cycle **World Type** until it reads **Structure Lab**.
4. Create the world and accept Minecraft's custom-world experimental prompt if shown.

The preset creates a superflat world with the lab dimension type. A normal Superflat world does not enable the lab. Placement and block inspection are restricted to lab worlds.

The build origin is `(0, -60, 0)`, above the grass layer. The lab freezes simulation and fixes time/weather. During a capture batch, it moves the local player in spectator mode, captures every configured angle, then returns to the first spawn angle.

## Connect an AI agent

Follow **[Install the MCP server](INSTALL_MCP.md)** next. The mod writes this file when Minecraft starts:

```text
<your Modrinth instance folder>/structurelab/connection.json
```

Find the instance folder through Modrinth's **Files** tab or its open-folder action. A typical Windows path is:

```text
%APPDATA%\ModrinthApp\profiles\NeoForge 26.1.2\structurelab\connection.json
```

Use the actual instance folder, which may differ from its display name. Do not upload or share `connection.json`; it contains the bridge's local authorization token.

## Capturing reliably

- Keep the world open and Minecraft rendering. Avoid moving the player, opening menus, or minimizing the game during a batch.
- Windowed mode is supported: the mod temporarily requests a 1920×1080 window, then restores the previous dimensions.
- In fullscreen, set the game's resolution to **1920×1080**. A different framebuffer size produces a clear error.
- The mod waits for chunks, lighting, section rendering, and camera position/orientation before capturing. A view times out after 60 seconds if it cannot become ready.
- Use camera positions in open space, with some clearance from walls; a camera on a block boundary can produce clipped geometry.

## Current limits

This release handles one structure at a time, with at most **16,000,000 positions** in its bounding volume. Width and length may each be up to 1024; height at the default origin may be up to 380. The combined old/new cleanup box is limited to 32,000,000 positions.

At most 1,000,000 explicit block records are accepted. The schema permits 1024 angles; the largest tested batch has 16 angles for the 429,341-record Capitol. The full limits, entity templates, multi-palette structures, redstone simulation, and shader compatibility are not qualified by this release.

## Troubleshooting

| Symptom | Check |
| --- | --- |
| Structure Lab does not appear in World Type | Confirm the exact game/loader versions and that the JAR is enabled; restart Minecraft after installing it. |
| `lab_world` is false | Open a world created with the **Structure Lab** preset. A regular superflat save is insufficient. |
| No connection file | Ensure the mod loaded, then check the actual instance folder and Minecraft's `logs/latest.log`. |
| Screenshot timeout | Close menus, keep Minecraft rendering, and move the camera away from solid blocks. |
| Framebuffer size error | Use windowed mode or set fullscreen to 1920×1080. |
| A request reports an active job | Wait for completion or cancel that revision before submitting another. |

To use a finished build elsewhere, call MCP `export_structure`. Its clean NBT/datapack removes Structure Lab view pads, so a vanilla-only build can be loaded without this mod.
