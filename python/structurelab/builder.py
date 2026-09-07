"""Sparse authoring, explicit air, typed block entities, and camera metadata."""
from __future__ import annotations
import json
import math
from pathlib import Path
from typing import Any
import nbtlib as nbt

DATA_VERSION = 4903  # Minecraft Java 26.2 version.json


class Structure:
    def __init__(self, size: tuple[int, int, int]):
        if len(size) != 3 or any(type(n) is not int or n < 1 or n > 1024 for n in size):
            raise ValueError("Dimensions must be integers between 1 and 1024")
        self.size = tuple(size)
        self.blocks: dict[tuple[int, int, int], tuple[str, dict, nbt.Compound | None]] = {}
        self.views: list[dict] = []

    def set(self, pos, block: str, properties: dict | None = None, block_entity: nbt.Compound | None = None):
        pos = tuple(pos)
        if len(pos) != 3 or any(type(p) is not int or not 0 <= p < n for p, n in zip(pos, self.size)):
            raise ValueError(f"Block position {pos} is outside {self.size}")
        if ":" not in block:
            block = "minecraft:" + block
        self.blocks[pos] = (block, {k: str(v).lower() for k, v in (properties or {}).items()}, block_entity)
        return self

    def fill(self, start, end, block: str, properties: dict | None = None):
        if any(a > b for a, b in zip(start, end)):
            raise ValueError("Fill endpoints must be ascending")
        for x in range(start[0], end[0] + 1):
            for y in range(start[1], end[1] + 1):
                for z in range(start[2], end[2] + 1):
                    self.set((x, y, z), block, properties)
        return self

    def room(self, start, end, wall="oak_planks", floor="spruce_planks", roof="oak_planks"):
        self.fill(start, end, wall)
        self.fill((start[0]+1, start[1]+1, start[2]+1), (end[0]-1, end[1]-1, end[2]-1), "air")
        self.fill(start, (end[0], start[1], end[2]), floor)
        self.fill((start[0], end[1], start[2]), end, roof)
        return self

    @staticmethod
    def look_at(position, target, eye_height=1.62):
        dx, dy, dz = (target[i] - position[i] for i in range(3))
        dy -= eye_height
        return {"yaw": math.degrees(math.atan2(-dx, dz)), "pitch": -math.degrees(math.atan2(dy, math.hypot(dx, dz)))}

    def view(self, id: str, position, angles: list[dict], *, label=None, spawn=False, eye_height=1.62, pad=None):
        if any(v["id"] == id for v in self.views):
            raise ValueError(f"Duplicate view ID: {id}")
        view = dict(id=id, label=label or id, position=list(position), angles=angles, spawn=spawn, eye_height=eye_height)
        if pad is None:
            self.views.append(view)
        else:
            self.set(pad, "structurelab:view_pad", block_entity=nbt.Compound({
                "id": nbt.String("structurelab:view_pad"),
                "view": nbt.Compound({"json": nbt.String(json.dumps(view))}),
            }))
        return self

    def save(self, path: str | Path) -> dict[str, str]:
        path = Path(path).resolve()
        path.parent.mkdir(parents=True, exist_ok=True)
        palette, indices, blocks = [], {}, []
        for pos, (name, props, entity) in sorted(self.blocks.items()):
            key = (name, tuple(sorted(props.items())))
            if key not in indices:
                indices[key] = len(palette)
                state = nbt.Compound({"Name": nbt.String(name)})
                if props:
                    state["Properties"] = nbt.Compound({k: nbt.String(v) for k, v in props.items()})
                palette.append(state)
            block = nbt.Compound({"pos": nbt.List[nbt.Int](pos), "state": nbt.Int(indices[key])})
            if entity is not None:
                block["nbt"] = entity
            blocks.append(block)
        root = nbt.File({"DataVersion": nbt.Int(DATA_VERSION), "size": nbt.List[nbt.Int](self.size),
                         "palette": nbt.List[nbt.Compound](palette), "blocks": nbt.List[nbt.Compound](blocks),
                         "entities": nbt.List[nbt.Compound]()})
        root.save(path, gzipped=True)
        views = path.with_suffix(".views.json")
        views.write_text(json.dumps(self.views, indent=2), encoding="utf-8")
        return {"path": str(path), "views_path": str(views)}
