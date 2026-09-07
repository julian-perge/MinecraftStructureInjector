import json
import nbtlib
import pytest
from structurelab import Structure
from structurelab.example import house


def test_roundtrip_states_explicit_air_and_omissions(tmp_path):
    s = Structure((3, 3, 3))
    s.set((0, 0, 0), "oak_stairs", {"facing": "west", "half": "top"})
    s.set((1, 1, 1), "air")
    path = tmp_path / "test.nbt"
    s.save(path)
    actual = nbtlib.load(path)
    assert int(actual["DataVersion"]) == 4903
    assert len(actual["blocks"]) == 2  # omitted positions stay omitted
    assert str(actual["palette"][0]["Properties"]["facing"]) == "west"
    assert str(actual["palette"][1]["Name"]) == "minecraft:air"


def test_view_angles_use_minecraft_coordinates():
    assert Structure.look_at((0, 0, 0), (0, 1.62, 1)) == {"yaw": 0, "pitch": 0}
    assert Structure.look_at((0, 0, 0), (1, 1.62, 0))["yaw"] == -90
    assert Structure.look_at((0, 0, 0), (0, 2.62, 0))["pitch"] == -90


def test_example_contains_pad_and_cleanup_sentinel(tmp_path):
    first=house(tmp_path/"first.nbt",1)
    second=house(tmp_path/"second.nbt",2)
    a,b=nbtlib.load(first["path"]),nbtlib.load(second["path"])
    assert list(map(int,a["size"])) == [19,10,17]
    assert list(map(int,b["size"])) == [17,10,17]
    assert any(str(p["Name"])=="structurelab:view_pad" for p in a["palette"])
    assert any(str(p["Name"])=="minecraft:gold_block" for p in a["palette"])
    assert not any(str(p["Name"])=="minecraft:gold_block" for p in b["palette"])
    assert len(json.loads(open(first["views_path"]).read())) == 3


def test_out_of_bounds_is_rejected():
    with pytest.raises(ValueError):
        Structure((3,3,3)).set((3,1,1), "stone")
