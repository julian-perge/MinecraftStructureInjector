"""Raid material mapping regression tests."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "examples"))

from raid import block_for


FALLING_BLOCKS = {"gravel", "sand", "red_sand", "suspicious_gravel",
                  "suspicious_sand", "white_concrete_powder"}


def _material(name):
    return {"name": name, "color": [0.4, 0.34, 0.29]}


def test_gravel_pebble_bed_does_not_map_to_falling_block():
    for revision in (1, 2, 3, 4):
        for name in ("gravel_pebble_bed",
                     "gravel_pebble_bed::dirt_mud_drying_blend",
                     "gravel_pebble_bed::pb_decal_wall_fillet_2_blend"):
            mapped = block_for(_material(name), revision)
            assert mapped not in FALLING_BLOCKS, (name, revision, mapped)


def test_gravel_pebble_bed_maps_to_andesite():
    for revision in (1, 2, 3, 4):
        assert block_for(_material("gravel_pebble_bed"), revision) == "andesite"
