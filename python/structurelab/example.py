"""A furnished house exercising interior cameras, block entities, and replacement."""
from .builder import Structure
import nbtlib as nbt


def house(path, revision=1):
    s = Structure((19 if revision == 1 else 17, 10, 17))
    s.room((1, 0, 1), (15, 5, 13), wall="stripped_oak_log", floor="spruce_planks", roof="oak_planks")
    # Timber frame and stone foundation.
    s.fill((0, 0, 0), (16, 0, 14), "stone_bricks")
    s.fill((2, 0, 2), (14, 0, 12), "spruce_planks")
    for x in (1, 8, 15):
        for z in (1, 13):
            s.fill((x, 1, z), (x, 5, z), "spruce_log", {"axis": "y"})
    for x in (3, 4, 11, 12):
        for z in (1, 13):
            s.fill((x, 2, z), (x, 3, z), "glass_pane", {"east": "true", "west": "true"})
    for z in (4, 5, 9, 10):
        for x in (1, 15):
            s.fill((x, 2, z), (x, 3, z), "glass_pane", {"north": "true", "south": "true"})
    # Roof, with stepped eaves and a ridge.
    for step in range(4):
        for z, facing in ((step, "south"), (14-step, "north")):
            s.fill((0, 5+step, z), (16, 5+step, z), "dark_oak_stairs", {"facing": facing, "half": "bottom", "shape": "straight"})
        s.fill((0, 5+step, step+1), (16, 5+step, 13-step), "dark_oak_planks")
    s.fill((7, 1, 1), (8, 2, 1), "air")
    for y, half in ((1, "lower"), (2, "upper")):
        s.set((7, y, 1), "oak_door", {"half": half, "facing": "north", "hinge": "left", "open": "true"})
    # Bedroom partition and doorway.
    s.fill((8, 1, 2), (8, 4, 8), "oak_planks")
    s.fill((9, 1, 8), (14, 4, 8), "oak_planks")
    s.fill((8, 1, 5), (8, 2, 6), "air")
    for x in (11, 12):
        s.set((x, 1, 3), "blue_bed", {"part": "head", "facing": "north"})
        s.set((x, 1, 4), "blue_bed", {"part": "foot", "facing": "north"})
    s.set((10, 1, 3), "bookshelf")
    s.set((10, 2, 3), "lantern", {"hanging": "false"})
    s.set((14, 1, 3), "barrel", {"facing": "up"})
    s.fill((10, 1, 5), (12, 1, 6), "blue_carpet" if revision == 1 else "red_carpet")
    # Living room.
    s.fill((2, 1, 9), (5, 1, 9), "oak_stairs", {"facing": "north"})
    s.fill((3, 1, 7), (5, 1, 7), "oak_slab", {"type": "top"})
    s.fill((3, 1, 4), (5, 1, 5), "white_carpet")
    s.fill((2, 1, 11), (2, 3, 12), "bookshelf")
    s.set((3, 4, 7), "lantern", {"hanging": "true"})
    # Kitchen, including a furnace block entity.
    s.fill((10, 1, 11), (14, 1, 12), "smooth_stone")
    s.set((10, 1, 11), "furnace", {"facing": "north"}, nbt.Compound({"id": nbt.String("minecraft:furnace")}))
    s.set((11, 1, 11), "crafting_table")
    s.set((14, 2, 12), "lantern", {"hanging": "false"})
    # A first-revision sentinel outside the second revision's bounds proves cleanup.
    if revision == 1:
        s.fill((18, 0, 15), (18, 3, 15), "gold_block")
    def angle(id, pos, target):
        return {"id": id, **s.look_at(pos, target)}
    pos = (8, 4, -9)
    s.view("spawn", pos, [angle("front", pos, (8, 3, 7))], label="Front facade and roof", spawn=True)
    pos = (11.5, 1, 6.5)
    s.view("bedroom", pos, [angle("beds", pos, (11.5, 1.8, 3)), angle("window", pos, (15, 2.7, 5))], label="Bedroom", pad=(13, 1, 7))
    pos = (6.5, 1, 4.5)
    s.view("living", pos, [angle("seating", pos, (3.5, 1.5, 9.5))], label="Living room")
    pos = (9.5, 1, 9.5)
    s.view("kitchen", pos, [angle("counter", pos, (12, 1.7, 12))], label="Kitchen counter")
    return s.save(path)
