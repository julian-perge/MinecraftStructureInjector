# Pass 1 — in-game visual review

Reviewed all 121 Minecraft captures across review-01.jpg through review-07.jpg.
The measured mansion geometry preserves the pool, circle drive, cantilevers and
three-lane arrangement, but this is a baseline rather than a finished playable map.

Corrections for pass 2:

- Restore dark granite floors and the blue basketball surface using measured materials.
- Replace excessive iron trim and yellow rock faces with closer vanilla materials.
- Reduce broad ceiling illumination caused by overly general light material matching.
- Fix garden, garden_steps and circle_south cameras: native player collision queries
  found those three obstructed. Other nearby walls also need more camera clearance.
- Convert broad one-block floor transitions to real Minecraft stairs. The user
  explicitly prioritizes playable, accessible routes over literal voxel geometry.
- Lower the overhead camera to reduce fog obscuring the footprint.

Remaining work after these corrections: route connectivity and movement verification,
furniture accessibility, court details, and further matched-reference visual review.
Static camera clearance alone does not establish map playability.
