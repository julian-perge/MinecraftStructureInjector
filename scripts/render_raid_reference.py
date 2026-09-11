"""Render the local research scene with original textures, never loading embedded scripts."""
import bpy
from mathutils import Vector
from pathlib import Path
import sys,json,math

out=Path(sys.argv[sys.argv.index('--')+1]).resolve();out.mkdir(parents=True,exist_ok=True)
scene=bpy.context.scene
scene.render.engine='CYCLES'
scene.cycles.samples=12
scene.cycles.use_denoising=True
scene.render.resolution_x=1600;scene.render.resolution_y=1600;scene.render.resolution_percentage=100
scene.world=bpy.data.worlds.new('Reference daylight')
scene.world.use_nodes=True
scene.world.node_tree.nodes['Background'].inputs['Color'].default_value=(0.65,0.72,0.85,1)
scene.world.node_tree.nodes['Background'].inputs['Strength'].default_value=0.7
scene.render.film_transparent=False
for obj in scene.objects:
    if obj.type=='LIGHT':obj.hide_render=True
light=bpy.data.lights.new('Reference sun','SUN');light.energy=2
sun=bpy.data.objects.new('Reference sun',light);scene.collection.objects.link(sun);sun.rotation_euler=(0.5,-0.3,0.3)
camera=bpy.data.cameras.new('Survey');obj=bpy.data.objects.new('Survey',camera);scene.collection.objects.link(obj);scene.camera=obj
obj.location=(60,72,200);obj.rotation_euler=(Vector((60,72,0))-obj.location).to_track_quat('-Z','Y').to_euler()
camera.type='ORTHO';camera.ortho_scale=160
scene.render.filepath=str(out/'overhead.png')
arguments=sys.argv[sys.argv.index('--')+1:]
if len(arguments)==1:
    bpy.ops.render.render(write_still=True)
else:
    scene.render.resolution_x=960;scene.render.resolution_y=540
    scene.render.threads_mode='FIXED';scene.render.threads=4
    scene.cycles.samples=8;scene.render.use_persistent_data=True
    camera.type='PERSP';camera.sensor_fit='VERTICAL';camera.sensor_height=24
    fill_data=bpy.data.lights.new('Research camera fill','POINT');fill_data.energy=500;fill_data.shadow_soft_size=2
    fill=bpy.data.objects.new('Research camera fill',fill_data);scene.collection.objects.link(fill)
    views=json.loads(Path(arguments[1]).read_text())
    manifest=[]
    for view in views:
        x,y,z=view['position'];obj.location=(140-z,140-x,y-16+view.get('eye_height',1.62))
        fill.location=obj.location
        for angle in view['angles']:
            yaw=math.radians(angle['yaw']);pitch=math.radians(angle['pitch'])
            direction=Vector((-math.cos(yaw)*math.cos(pitch),math.sin(yaw)*math.cos(pitch),-math.sin(pitch)))
            obj.rotation_euler=direction.to_track_quat('-Z','Y').to_euler()
            camera.lens=12/math.tan(math.radians(angle.get('fov',70))/2)
            filename=view['id']+'__'+angle['id']+'.png'
            scene.render.filepath=str(out/filename)
            if not (out/filename).exists():bpy.ops.render.render(write_still=True)
            manifest.append({'id':view['id'],'angle':angle['id'],'file':filename,'position':view['position'],'label':view['label']})
            print('REFERENCE_VIEW',filename,flush=True)
    (out/'reference-manifest.json').write_text(json.dumps(manifest,indent=2))
