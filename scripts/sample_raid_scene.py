"""Sample the locally acquired Raid reference onto a metre grid for vanilla reconstruction.

Run only using Blender --background --disable-autoexec. Raw reference assets stay local.
"""
import bpy
import numpy as np
from pathlib import Path
import sys,json,time

out=Path(sys.argv[sys.argv.index('--')+1]).resolve();out.mkdir(parents=True,exist_ok=True)
SIZE=(150,64,170)
materials=[];material_ids={};voxels={};started=time.time()

def material_id(mat):
    name=mat.name if mat else 'unknown'
    if name in material_ids:return material_ids[name]
    color=[0.6,0.6,0.6];image=None
    if mat and mat.use_nodes:
        # The imported materials use a Principled shader with the diffuse texture linked to Base Color.
        for node in mat.node_tree.nodes:
            if node.type=='BSDF_PRINCIPLED':
                socket=node.inputs.get('Base Color')
                if socket and socket.is_linked:
                    source=socket.links[0].from_node
                    if source.type=='TEX_IMAGE':image=source.image
                if socket:color=list(socket.default_value[:3])
    if image and image.size[0] and image.size[1]:
        pixels=np.empty(len(image.pixels),dtype=np.float32);image.pixels.foreach_get(pixels)
        pixels=pixels.reshape(-1,4)[::max(1,len(pixels)//4//2048)]
        useful=pixels[pixels[:,3]>.2]
        if len(useful):color=np.median(useful[:,:3],axis=0).tolist()
    index=len(materials);material_ids[name]=index
    materials.append({'name':name,'color':color,'image':image.filepath if image else None})
    return index

depsgraph=bpy.context.evaluated_depsgraph_get()
for number,instance in enumerate(depsgraph.object_instances):
    obj=instance.object
    if obj.type!='MESH' or obj.hide_render or (instance.parent and instance.parent.hide_render):continue
    matrix=np.array(instance.matrix_world)
    bounds=np.array(obj.bound_box)@matrix[:3,:3].T+matrix[:3,3]
    if any(bounds[:,i].max()<a or bounds[:,i].min()>b for i,(a,b) in enumerate([(-30,140),(-10,140),(-16,48)])):continue
    mesh=obj.data
    vertices=np.empty(len(mesh.vertices)*3,dtype=np.float32);mesh.vertices.foreach_get('co',vertices)
    vertices=vertices.reshape(-1,3)@matrix[:3,:3].T+matrix[:3,3]
    mesh.calc_loop_triangles()
    indices=np.empty(len(mesh.loop_triangles)*3,dtype=np.int32);mesh.loop_triangles.foreach_get('vertices',indices)
    indices=indices.reshape(-1,3)
    mids=np.empty(len(mesh.loop_triangles),dtype=np.int32);mesh.loop_triangles.foreach_get('material_index',mids)
    mapping={i:material_id(m) for i,m in enumerate(mesh.materials)}
    if not mapping:mapping[0]=material_id(None)
    for triangle,mi in zip(indices,mids):
        a,b,c=vertices[triangle]
        lo=np.minimum(np.minimum(a,b),c);hi=np.maximum(np.maximum(a,b),c)
        if hi[0]<-30 or lo[0]>=140 or hi[1]<-10 or lo[1]>=140 or hi[2]<-16 or lo[2]>=48:continue
        mid=mapping.get(int(mi),0);name=materials[mid]['name'].lower()
        if any(k in name for k in ['skybox','sky_','clip','portal','trigger','shadow','occlusion']):continue
        ab=b-a;ac=c-a;normal=np.cross(ab,ac);area=np.linalg.norm(normal)
        if area<1e-8:continue
        normal/=area
        steps=max(1,int(np.ceil(max(np.linalg.norm(ab),np.linalg.norm(ac),np.linalg.norm(c-b))/.38)))
        # Long terrain polygons are sampled in rows to bound memory.
        for row in range(steps+1):
            u=row/steps
            v=np.arange(steps-row+1)/steps
            points=a+u*ab+v[:,None]*ac-normal*.035
            xyz=np.column_stack((140-points[:,1],points[:,2]+16,140-points[:,0]))
            coords=np.floor(xyz).astype(np.int32)
            good=np.all((coords>=0)&(coords<np.array(SIZE)),axis=1)
            coords=coords[good];xyz=xyz[good]
            # Prefer surfaces nearest each voxel centre; very small overlays should not thicken walls.
            scores=np.sum((xyz-(coords+.5))**2,axis=1)
            for pos,score in zip(coords,scores):
                key=tuple(int(v) for v in pos)
                previous=voxels.get(key)
                if previous is None or score<previous[1]:voxels[key]=(mid,float(score))
    if number%200==0:print('SAMPLED',number,'voxels',len(voxels),'seconds',round(time.time()-started),flush=True)
positions=np.array(list(voxels),dtype=np.int16)
ids=np.array([v[0] for v in voxels.values()],dtype=np.int16)
np.savez_compressed(out/'metre-surfaces.npz',positions=positions,materials=ids)
(out/'materials.json').write_text(json.dumps(materials,indent=2))
(out/'sampling.json').write_text(json.dumps({'size':SIZE,'transform':'minecraft=(140-sourceY, sourceZ+16, 140-sourceX)','metres_per_block':1,'voxels':len(voxels),'seconds':time.time()-started},indent=2))
print('RAID_SAMPLED',len(voxels),round(time.time()-started),flush=True)
