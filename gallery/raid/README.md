# Classic Raid gallery

[Open the searchable 121-view gallery](index.html). All gallery images are actual Minecraft 1.21.1 captures, reduced to JPEG for storage. The 13 affected views use the final junction recheck; remaining views use the full final regression.

The classic Los Angeles mansion occupies 150 × 64 × 170 blocks at one block per metre, with Minecraft stairs, slabs and openings adapted for movement. [Artifacts and installation](../../docs/RAID.md) · [Research](../../docs/RAID_RESEARCH.md).

## Four review passes

1. [Baseline](pass-1/review.md): measured scene layout and initial material conversion.
2. [Materials and cameras](pass-2/review.md): corrected floor, court and trim colors; improved camera placement and stairs.
3. [Movement and interiors](pass-3/review.md): connected routes, lighting and court details.
4. [Furniture and landings](pass-4/review.md): vanilla furnishings and stair junction refinement.

Each pass has seven contact sheets containing 121 views in its folder. [Final regression sheets](final-review/review-01.jpg) and [junction recheck](final-review/junction-recheck.jpg) document subsequent corrections. The initial fourth pass and first final regression each exposed a movement issue; both were corrected before exporting the qualified NBT.

Final verification: **56/56** native walking directions across 28 routes without jumping, and **29/29** clear, supported ground camera stations. [Machine-readable evidence](verification/verification.json). These are native collision/movement tests, not keyboard or multiplayer gameplay tests.

Reference textures and extracted source assets are not included in this gallery. Everything remains local; no GitHub push was made.
