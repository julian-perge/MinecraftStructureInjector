# Structure Lab

NeoForge mod and local MCP server that generates NBT structures, places each revision in a dedicated superflat world, and returns screenshots rendered by Minecraft. `main` holds the newest Minecraft version, and older versions live on the protected `26.2`, `26.1.2` and `1.21.1` branches ([ADR 0001](docs/adr/0001-main-follows-the-newest-minecraft.md)).

## Every task

- Run `uv run pytest -q`, `uv run prek run --all-files` and `./gradlew build` to verify a change.
- Commit only after a working run. A change with no runtime effect needs a build or the tests, and a change to runtime behavior also needs an in-game run.
- Before any in-game run, ask the owner and wait for a yes. The request says what will run, how long it takes, whether the game window must be in front or the keyboard free, how you will stop it and where the output lands. One yes covers exactly what the request said.
- Use placeholders such as `<path to jar>` instead of local paths and personal details in commits, issues and comments, because the repo is public.
- Leave AI attribution out of commits, issues and comments.

## Read the doc that matches the task

- [Build and tooling](docs/agents/build-and-tooling.md): before changing the Gradle or Python setup or hooks, before landing a fix on a version branch, or before moving the mod to a new Minecraft version.

## Workflow

- Tasks are tracked in GitHub Issues for julian-perge/MinecraftStructureInjector, with the `gh` CLI. `/agent-skills:plan` creates one sub-issue per task. `tasks/` is git-ignored scratch.
- Specs are files at `spec/<issue>-<slug>.md`, not `SPEC.md`.
- ADRs go in `docs/adr/`. Read `GLOSSARY.md` and `docs/adr/` (those that exist) before design work.
- Start each `/agent-skills` stage with `agent-skills brief <stage> <n>`. It prints every rule of `docs/agents/workflow.md` that the stage needs, so do not read that file in a stage. Before other work in this repo, read all of `docs/agents/workflow.md`.
