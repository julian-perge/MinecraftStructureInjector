"""Run with Blender --background --disable-autoexec <reference.blend> --python this_file -- <output.json>."""
import bpy
import json
from pathlib import Path
import sys
from mathutils import Vector

destination=Path(sys.argv[sys.argv.index('--')+1])
objects=[]
for instance in bpy.context.evaluated_depsgraph_get().object_instances:
    obj=instance.object
    if obj.type!='MESH':
        continue
    corners=[instance.matrix_world @ Vector(c) for c in obj.bound_box]
    objects.append({'name':obj.name,'vertices':len(obj.data.vertices),'polygons':len(obj.data.polygons),
        'min':[min(c[i] for c in corners) for i in range(3)],
        'max':[max(c[i] for c in corners) for i in range(3)],
        'materials':[m.name if m else None for m in obj.data.materials]})
report={'file':bpy.data.filepath,'unit_system':bpy.context.scene.unit_settings.system,
    'scale_length':bpy.context.scene.unit_settings.scale_length,'objects':objects,
    'images':[{'name':i.name,'path':i.filepath,'packed':bool(i.packed_file),'size':list(i.size)} for i in bpy.data.images]}
destination.parent.mkdir(parents=True,exist_ok=True)
destination.write_text(json.dumps(report,indent=2))
print('RAID_SCENE_INSPECTED',len(objects),str(destination))
