# Raid reconstruction research

Target: the classic Los Angeles mansion from Black Ops II / Black Ops Cold War, confirmed by the user on September 10, 2026. This is not Black Ops 7's Japanese reinterpretation.

## Sources and reference coverage

- [Activision, Season One announcement, December 10, 2020](https://www.callofduty.com/de/blog/2020/12/Season-One-Announcement-coming-December-16): primary confirmation of Hollywood Hills, the central courtyard, pool-facing bedroom, basketball half-court, garden, guest space, roundabout, and three-lane design.
- [Activision, Raid map snapshot, December 31, 2019](https://blog.activision.com/call-of-duty/2019-12/Mobile-Map-Snapshot-Raid): primary cross-check of routes and named spaces. Mobile imagery includes a winter variant; its seasonal materials are excluded from this reconstruction.
- [Gamer Guides, BO2 Raid guide](https://www.gamerguides.com/call-of-duty-black-ops-ii/guide/multiplayer-guide/maps-and-tactics/raid): original-game pool-facing facade screenshot, visually inspected. The second image is a weapon loadout screen and is excluded.
- [Steam community BO2 guide](https://steamcommunity.com/sharedfiles/filedetails/?id=3299244333): original minimap, visually inspected. Used to align building footprints, pool/hot-tub/bar, circular drive, courtyard, basketball court, and connections. The map is asymmetrical; image-search captions describing symmetry are incorrect.
- [Open3DLab, Raid (COD: BO2), Acoolrocket, April 17, 2024](https://open3dlab.com/project/b71533bc-67d1-4ba2-b2c8-36141d185be9/): community-hosted extracted scene and two useful aerial previews. Scene fidelity and coordinate scale require checking. Raw scene and textures remain ignored local research material, separate from the vanilla-block deliverable.
- [Original-game walkthrough, lookinside, November 13, 2012](https://www.youtube.com/watch?v=Z_1iE90tP_c): identified for additional route reference; not yet visually reviewed.
- [Cold War frame gallery, JCTechCorner](https://www.reddit.com/r/blackopscoldwar/comments/17iivux/frame_stills_from_raid/): identified, but gallery access was blocked by a human-verification page. Not counted as reviewed coverage.

## Working coordinate convention

Use the original minimap with the garage side at the top, basketball court at lower left, swimming pool on the left, and circular drive on the right. This avoids inconsistent compass directions across rotated guide images. Minecraft +X points right and +Z points down in that plan.

## Scale and verification

One Minecraft block represents one metre. The extracted scene reports metric units with scale length 1.0. Independent object measurements give a sports-car length of approximately 5.06 metres and a basketball-rim elevation of 2.98 metres, supporting that convention. This is a reconstruction of the game scene's scale, not a surveyed real mansion. Voxel quantization and deliberate playability changes introduce local differences of roughly a block.

The retained region is 150 × 64 × 170 blocks. The coordinate conversion is `(140-sourceY, sourceZ+16, 140-sourceX)`. The larger background city is outside the retained region. The source archive SHA-256 is `21def977026920b77110a8da19a216fa730a52eaacb593d750b62f6196110a45`.

The reference scene has now been rendered from 121 named camera angles as well as an overhead survey. These are research renders of the extracted geometry, not original-game screenshots. Some initial interior views are dark or obstructed, so they cannot alone establish complete useful visual coverage. Original-game screenshots and the minimap provide independent exterior checks.

All four refinement passes are complete, each with 121 actual Minecraft screenshots and review. An additional 121-angle regression and 13 targeted junction rechecks verified the portable export. The final build passed 56 native player walking checks (28 routes in both directions without jumping) and collision/support checks at all 29 ground camera stations. Native movement tests exercise server player collision and stepping; they are not keyboard, combat, or multiplayer simulations.

The reference review also includes 121 lit scene renders and 12 corrected interior views for the gym, laundry and art rooms. Supplemental camera lighting makes interior geometry readable; these remain research renders rather than original-game screenshots. Coverage is broad but does not establish every possible angle. See [the completed build](RAID.md) for artifacts and limitations.

## Playability priority

The user explicitly authorizes creative adjustments for accessibility and playability: use Minecraft stairs and slabs, widen obstructed openings, and adjust local geometry when a literal conversion would impede movement. Preserve the overall measured layout and landmarks while making connected routes traversable without mandatory jumping.

## Reproducing the local build

Install `.[dev,research]` in the Python environment. The downloaded scene and textures
are local reference inputs under `artifacts/raid/references/scene`; they are not
bundled into the mod, MCP wheel, or gallery. The Blender commands below deliberately
disable embedded Python scripts in the downloaded scene.

```powershell
$raidBlender = 'C:/Program Files/Blender Foundation/Blender 5.0/blender.exe'
$raidScene = 'artifacts/raid/references/scene/Raid (BO2)/Raid (BO2).blend'
& $raidBlender --background --disable-autoexec $raidScene --python scripts/sample_raid_scene.py -- artifacts/raid/reference-grid
& $raidBlender --background --disable-autoexec $raidScene --python scripts/measure_raid_materials.py -- artifacts/raid/reference-grid
.\.venv\Scripts\python.exe examples/raid.py --revision 4 --explicit-air --output artifacts/raid/final
```

The first pass intentionally uses the baseline material measurements; later passes
use the corrected texture-group measurements. Revision-specific refinements are
preserved in the generator. `--explicit-air` adds empty interior cells below each
occupied column's top for portable placement; it does not change visible geometry
in the cleared lab. Background city detail, textures, decals, and game-specific
movement mechanics are not part of the vanilla NBT.
