"""Resolve diffuse images inside imported shader groups for reference color measurements."""
import bpy,json
import numpy as np
from pathlib import Path
import sys

directory=Path(sys.argv[sys.argv.index('--')+1])
materials=json.loads((directory/'materials.json').read_text())

def textures(tree,seen=None):
    seen=set() if seen is None else seen
    if tree.name in seen:return []
    seen.add(tree.name);result=[]
    for node in tree.nodes:
        if node.type=='TEX_IMAGE' and node.image:result.append(node.image)
        if node.type=='GROUP' and node.node_tree:result.extend(textures(node.node_tree,seen))
    return result

for record in materials:
    mat=bpy.data.materials.get(record['name'])
    if not mat or not mat.node_tree:continue
    candidates=[i for i in textures(mat.node_tree) if i.name.startswith(('~~-g','~-g')) and i.size[0]>0]
    if not candidates:continue
    image=candidates[0]
    pixels=np.empty(len(image.pixels),dtype=np.float32);image.pixels.foreach_get(pixels)
    pixels=pixels.reshape(-1,4)[::max(1,len(pixels)//4//4096)]
    pixels=pixels[pixels[:,3]>.25]
    if not len(pixels):continue
    record['color']=np.median(pixels[:,:3],axis=0).tolist()
    record['image']=image.filepath
(directory/'materials-measured.json').write_text(json.dumps(materials,indent=2))
print('MATERIALS_MEASURED',len(materials))
