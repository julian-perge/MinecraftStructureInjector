# Build and tooling

- `uv sync` creates `.venv` on Python 3.15 with the `dev` group, and `uv run pytest -q` runs the unit tests, which need no game.
- `uv run prek install --allow-missing-config` once in a clone makes each commit run the hooks in `prek.toml` on the staged files, and `uv run prek run --all-files` runs them on every tracked file. The flag is there because the `26.2` and `1.21.1` branches have no `prek.toml`.
- `./gradlew build` compiles the mod and writes `build/libs/structurelab-<Minecraft version>-<mod version>.jar`.

## Where a Minecraft version is set

| File | What to change |
| --- | --- |
| `build.gradle` | `archivesName`, `neoForge { version }` and the Jade `compileOnly` version |
| `src/main/resources/META-INF/neoforge.mods.toml` | The NeoForge and Minecraft `versionRange` |
| `python/structurelab/builder.py` | `DATA_VERSION` |
| `python/structurelab/server.py` | `DEFAULT_INSTANCE`, the `export_structure` docstring, and the description, `min_format` and `max_format` in `pack.mcmeta` |
| `src/main/java/dev/structurelab/LabSession.java` | The `minecraft` field of `status` |
| `tests/test_builder.py` | The expected `DataVersion` |
| `scripts/verify_capitol.py` | The jar name |
| `README.md` | The Minecraft and NeoForge versions, the DataVersion, the datapack format and the jar name |

`DATA_VERSION` is `world_version`, and the datapack format is `pack_version.data_major` and `data_minor`, in the `version.json` of that Minecraft's client jar. `unzip -p ~/.gradle/caches/neoformruntime/artifacts/minecraft_<version>_client.jar version.json` prints it.

## Fixing a version branch

Each older version takes only fixes. A fix lands on the branch where it was tested and is cherry-picked to the others with `git cherry-pick -x`.

## Moving to a new Minecraft version

`main` follows the newest Minecraft version, and older versions live on protected version branches ([ADR 0001](../adr/0001-main-follows-the-newest-minecraft.md)). Finish each step before the next:

1. Land the work the old version still needs on `main`.
2. Cut `port-<new version>` from `main` and port in slices, checking each slice in a dev client.
3. Take the NeoForge and Jade targets from the NeoForge primers and changelog for every version crossed, and update every file in the table above. Also read the data fixes added since the old version in `DataFixers`, because `LabPlacement` loads templates without vanilla's data fixer, so a renamed NBT key places air with no error.
4. When the port runs, cut `<old version>` from `main` and push it. The "Version branches" ruleset (pattern `refs/heads/[0-9]*.*`) blocks deleting and force-pushing it from the first push, and `gh api repos/julian-perge/MinecraftStructureInjector/rules/branches/<old version> --jq '[.[].type]'` lists `deletion` and `non_fast_forward` when it applies. Then fast-forward `main` to the port branch, so history stays linear. If the ruleset is ever missing, this recreates it:

   ```
   gh api repos/julian-perge/MinecraftStructureInjector/rulesets -X POST --input - <<'EOF'
   {"name":"Version branches","target":"branch","enforcement":"active",
    "conditions":{"ref_name":{"include":["refs/heads/[0-9]*.*"],"exclude":[]}},
    "rules":[{"type":"deletion"},{"type":"non_fast_forward"}]}
   EOF
   ```
5. Update the README (the versions and a link to the version branch) and note the new branch on open issues.
