"""Classic Raid, one vanilla block per metre, with reproducible review cameras.

The optional ignored reference grid supplies measured geometry. This generator maps
materials to vanilla blocks and applies Minecraft-specific construction refinements.
"""
import argparse
import json
from pathlib import Path
import math
import numpy as np
from structurelab import Structure


def block_for(material, revision=1):
    name=material['name'].lower().split('::')[0]
    if revision >= 2:
        if 'plaster_wall_bluepaint' in name:return 'light_blue_concrete' if revision>=3 else 'blue_concrete'
        if 'stone_floor' in name:
            return ('gray_concrete' if revision>=3 else 'polished_deepslate') if max(material['color']) < .3 else 'smooth_stone'
        if 'solar' in name:return 'blue_concrete'
        if 'rock' in name or 'cliff' in name:return 'andesite'
        if 'metal' in name and not any(k in name for k in ('dark','rubber','sportscar')):return 'smooth_stone'
        if 'light' in name and 'lamp' not in name:return 'smooth_quartz'
    if 'water_pool' in name:return 'water'
    if 'solar' in name:return 'blue_terracotta'
    if 'glass' in name or 'window_clear' in name:return 'light_gray_stained_glass'
    if any(k in name for k in ['foliage','leaves','leaf','grass_','bush','ivy','fern','canopy']):return 'jungle_leaves'
    if 'palm' in name or 'tree' in name:return 'jungle_log'
    if 'sculpture' in name:return 'terracotta'
    if 'sportscar' in name:
        if 'rubber' in name:return 'black_concrete'
        if 'orange' in name:return 'orange_concrete'
        if 'yellow' in name:return 'yellow_concrete'
        return 'gray_concrete'
    if 'off_white' in name:return 'white_concrete'
    if any(k in name for k in ['wood','plank','timber']):return 'dark_oak_planks'
    if 'rock' in name or 'cliff' in name:return 'sandstone'
    if any(k in name for k in ['dirt','mud','sand_','ground_']):return 'coarse_dirt'
    # Gravel falls when placed over air (e.g. roofs); andesite is a
    # similar speckled grey that stays put.
    if 'gravel' in name or 'pebble' in name:return 'andesite'
    if 'concrete_plates' in name:return 'smooth_stone'
    if 'concrete_vertical' in name:return 'light_gray_concrete'
    if 'concrete' in name or 'plaster' in name:return 'smooth_quartz'
    if 'asphalt' in name or 'road' in name:return 'gray_concrete'
    if 'metal_dark' in name or 'rubber' in name:return 'black_concrete'
    if 'metal' in name or 'chrome' in name:return 'iron_block'
    if any(k in name for k in ['cloth','fabric','bed_','pillow']):return 'white_wool'
    if 'tile' in name:return 'quartz_block'
    if 'light' in name or 'lamp' in name:return 'sea_lantern'
    r,g,b=material['color']
    if max(r,g,b)<.12:return 'black_concrete'
    if r>g*1.4 and r>b*1.4:return 'terracotta'
    if g>r*1.2 and g>b*1.1:return 'green_terracotta'
    if b>r*1.2:return 'blue_terracotta'
    if max(r,g,b)>.65:return 'white_concrete'
    if max(r,g,b)>.3:return 'light_gray_concrete'
    return 'gray_concrete'


# Source metres, Z up. These names follow the original mansion's landmarks.
STATIONS=[
    ('garage',(109,82,1),'Garage and sports cars'),
    ('garage_entry',(96,85,1),'Garage entrance and driveway'),
    ('garage_court',(100,94,1),'Garage-side curved terrace'),
    ('bedroom',(75,105,4),'Bedroom overlooking the pool'),
    ('bedroom_balcony',(73,114,4),'Bedroom pool sightline'),
    ('pool_north',(76,118,0),'Pool from bedroom end'),
    ('pool_middle',(56,117,0),'Pool and hot tub'),
    ('pool_south',(30,117,0),'Pool from basketball end'),
    ('pool_bar',(42,110,0),'Circular pool bar'),
    ('hot_tub',(62,109,0),'Hot tub and water steps'),
    ('basketball',(14,108,0),'Basketball half court'),
    ('basketball_entry',(20,100,0),'Court approach'),
    ('garden',(6,72,0),'Garden spawn and rock cover'),
    ('garden_steps',(20,65,1),'Garden to courtyard steps'),
    ('kitchen',(33,74,3),'Kitchen counters and island'),
    ('money',(32,88,3),'Money room'),
    ('central_court',(56,75,3),'Central courtyard'),
    ('court_north',(64,79,3),'Courtyard north entrance'),
    ('court_south',(46,73,3),'Courtyard kitchen entrance'),
    ('court_east',(62,67,3),'Courtyard to circle route'),
    ('laundry',(34,42,6),'Upper laundry room'),
    ('laundry_balcony',(38,49,6),'Laundry overlook'),
    ('art',(79,58,3),'Art room beside circle'),
    ('gym',(99,59,1),'Gym and treadmills'),
    ('circle_north',(76,43,3),'Circle drive from garage side'),
    ('circle_east',(58,25,3),'Sculpture and circle approach'),
    ('circle_south',(37,42,3),'Circle from laundry side'),
    ('circle_west',(57,57,3),'Circle toward main drive'),
    ('drive_entry',(55,13,3),'Main driveway and truck'),
]


def convert(p):return (140-p[1],p[2]+16,140-p[0])


def accessible_steps(s, revision=2):
    """Split broad one-metre floor risers into Minecraft half-metre stair steps.

    Require a three-block-wide landing on both levels, preventing furniture,
    narrow cover and wall edges from being treated as circulation stairs.
    """
    def floor(x,y,z):
        state=s.blocks.get((x,y,z),('minecraft:air',{},None))[0]
        return state in {'minecraft:smooth_quartz','minecraft:smooth_stone',
                         'minecraft:polished_deepslate','minecraft:light_gray_concrete',
                         'minecraft:white_concrete','minecraft:quartz_block'} or (revision>=3 and state=='minecraft:gray_concrete')
    def air(x,y,z):return s.blocks.get((x,y,z),('minecraft:air',{},None))[0]=='minecraft:air'
    changes={}
    for x,y,z in list(s.blocks):
        if not 14<=y<=27 or not floor(x,y,z):continue
        for dx,dz,facing in [(1,0,'east'),(-1,0,'west'),(0,1,'south'),(0,-1,'north')]:
            if all(floor(x+dz*w,y,z+dx*w) and floor(x+dx+dz*w,y,z+dz+dx*w)
                   and floor(x-dx+dz*w,y-1,z-dz+dx*w)
                   and all(air(x-dx+dz*w,y+h,z-dz+dx*w) for h in range(3))
                   and all(air(x+dz*w,y+h,z+dx*w) for h in (1,2,3))
                   for w in (-1,0,1)):
                block='quartz_stairs' if 'quartz' in s.blocks[(x,y,z)][0] else 'stone_brick_stairs'
                changes[(x,y,z)]=(block,{'facing':facing,'half':'bottom','shape':'straight','waterlogged':'false'})
                break
    for p,(block,props) in changes.items():s.set(p,block,props)
    return len(changes)


def cameras(s, revision=1):
    for name,source,label in STATIONS:
        if revision>=3:
            source={'garage_entry':(94,81,1),'garden':(10,75,4),
                    'circle_west':(60,54,3),'bedroom':(74,110,4),
                    'pool_bar':(44,107,0)}.get(name,source)
        if revision>=4 and name=='art':source=(79,58,5)
        x,y,z=convert(source)
        # Choose the nearest clear standing point without moving to a different floor.
        candidates=[]
        radius=6 if revision>=2 else 3
        interior=revision>=4 and name in ('bedroom','kitchen','money','laundry','art','gym','basketball_entry')
        if interior:radius=2
        for dx in range(-radius,radius+1):
            for dz in range(-radius,radius+1):
                for dy in range(-1,2 if interior else (7 if revision>=2 else 2)):
                    p=(round(x)+dx,round(y)+dy,round(z)+dz)
                    def solid(q):return s.blocks.get(q,('minecraft:air',{},None))[0] not in ('minecraft:air','minecraft:water')
                    if solid((p[0],p[1]-1,p[2])) and not solid(p) and not solid((p[0],p[1]+1,p[2])):
                        floor=s.blocks.get((p[0],p[1]-1,p[2]),('air',{},None))[0]
                        if revision>=2 and any(k in floor for k in ('leaves','log','glass')):continue
                        crowd=sum(solid((p[0]+a,p[1]+1,p[2]+b)) for a,b in [(1,0),(-1,0),(0,1),(0,-1)])
                        nearby=sum(solid((p[0]+a,p[1],p[2]+b)) for a in range(-2,3) for b in range(-2,3)) if revision>=3 else 0
                        candidates.append((dx*dx+dz*dz+dy*dy*4+(crowd*8 if revision>=2 else 0)+nearby*3,p))
        if candidates:
            _,p=min(candidates);position=(p[0]+.5,p[1],p[2]+.5)
        elif revision>=2:raise ValueError(f'No usable camera floor for {name}')
        else:position=(x+.5,y,z+.5)
        if revision>=4 and name=='gym':position=(79.5,17,40.5)
        s.view(name,position,[dict(id=label,yaw=yaw,pitch=6,fov=80) for label,yaw in [('north',180),('east',-90),('south',0),('west',90)]],label=label,spawn=name=='garage')
    target=(70,20,85)
    for name,position in [('aerial_pool',(-18,73,90)),('aerial_circle',(166,76,85)),('aerial_garage',(75,77,-16)),('aerial_garden',(70,75,188)),('overhead',(75,145,85))]:
        if name=='overhead' and revision>=2:position=(75,108,85)
        s.view(name,position,[dict(id='survey',**s.look_at(position,target),fov=90 if name=='overhead' and revision>=2 else 70)],label=name.replace('_',' ').title())


def build(grid,revision):
    data=np.load(grid/'metre-surfaces.npz');materials=json.loads((grid/('materials-measured.json' if revision>=2 else 'materials.json')).read_text())
    sampling=json.loads((grid/'sampling.json').read_text());s=Structure(tuple(sampling['size']))
    palette=[block_for(m,revision) for m in materials]
    for pos,mi in zip(data['positions'],data['materials']):
        p=tuple(map(int,pos));block=palette[int(mi)]
        props={'persistent':'true','distance':'1'} if block.endswith('_leaves') else None
        s.set(p,block,props)
    # Seal the bottom of the standalone structure; omitted space above floors remains air.
    columns={}
    for x,y,z in s.blocks:columns[(x,z)]=min(y,columns.get((x,z),s.size[1]))
    for (x,z),floor in columns.items():
        for y in range(floor):s.set((x,y,z),'stone')
    if revision>=2:
        count=accessible_steps(s,revision)
        print(f'Converted {count} broad floor edges to traversable stairs')
    if revision>=3:
        # Painted half-court markings are integral floor blocks, without a
        # carpet lip. The hoop is approximately three metres above the court.
        for x in range(22,36):
            for z in range(118,134):
                if s.blocks.get((x,15,z),('',{},None))[0]!='minecraft:light_blue_concrete':continue
                boundary=x in (22,35) or z in (118,133)
                key=(x<=28 and z in (123,128)) or (x==28 and 123<=z<=128)
                arc=abs(math.hypot(x-23,z-125.5)-7)<.45 and x>=23
                if boundary or key or arc:s.set((x,15,z),'white_concrete')
        s.fill((22,16,125),(24,20,128),'air')
        s.fill((22,16,126),(22,19,126),'polished_blackstone_wall')
        s.fill((22,19,125),(22,20,127),'white_concrete')
        s.set((23,18,126),'orange_stained_glass_pane')
        s.set((23,17,126),'iron_bars')
        # Discreet ceiling luminaires improve usable interiors without replacing
        # whole ceilings with emissive blocks.
        for sx,sy,sz in [(75,108,4),(34,86,3),(36,74,3),(99,60,1),(79,59,4),(34,43,6),(108,84,1)]:
            x,y,z=map(round,convert((sx,sy,sz)))
            for dx,dz in [(-2,0),(2,0),(0,-2),(0,2)]:
                for h in range(2,6):
                    q=(x+dx,y+h,z+dz)
                    if s.blocks.get(q,('minecraft:air',{},None))[0]!='minecraft:air':
                        s.set(q,'sea_lantern');break
    if revision>=4:
        # Replace the metre-thick mattress with usable vanilla beds and low
        # bedside tables, retaining the original bedroom furniture footprint.
        s.fill((31,20,63),(34,21,66),'air')
        for x in (32,33):
            s.set((x,20,64),'white_bed',{'facing':'north','part':'foot','occupied':'false'})
            s.set((x,20,63),'white_bed',{'facing':'north','part':'head','occupied':'false'})
        for x in (31,34):s.set((x,20,63),'dark_oak_slab',{'type':'bottom','waterlogged':'false'})
        # Functional vanilla appliances occupy the reference counter run.
        s.set((66,19,100),'cauldron')
        s.set((64,19,100),'furnace',{'facing':'west','lit':'false'})
        s.set((65,19,100),'smoker',{'facing':'west','lit':'false'})
    cameras(s,revision)
    if revision>=3:
        from raid_access import repair
        s.routes=repair(s,revision)
    if revision>=4:
        for p,(name,props,entity) in list(s.blocks.items()):
            x,y,z=p
            if name.endswith('_leaves') and 18<=y<=28 and 25<x<110 and 25<z<135 and (x+z)%4==0:
                if any(s.blocks.get((x+dx,y,z+dz),('',{},None))[0] in ('minecraft:white_concrete','minecraft:smooth_quartz') for dx,dz in [(1,0),(-1,0),(0,1),(0,-1)]):
                    s.set(p,'flowering_azalea_leaves',props)
        for v in s.views:
            x,y,z=v['position'];floor=s.blocks.get((int(x),int(y)-1,int(z)),('',{},None))
            if floor[0].endswith('_slab') and floor[1].get('type')=='bottom':v['position'][1]-=.5
    return s,materials,palette


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--grid',type=Path,default=Path('artifacts/raid/reference-grid'));p.add_argument('--output',type=Path,required=True);p.add_argument('--revision',type=int,choices=range(1,5),required=True)
    p.add_argument('--explicit-air',action='store_true',help='Clear empty cells below each occupied column top for portable placement')
    args=p.parse_args();s,materials,palette=build(args.grid,args.revision);args.output.mkdir(parents=True,exist_ok=True)
    if args.explicit_air:
        tops={}
        for x,y,z in s.blocks:tops[(x,z)]=max(y,tops.get((x,z),0))
        for (x,z),top in tops.items():
            for y in range(top+1):
                if (x,y,z) not in s.blocks:s.set((x,y,z),'air')
    result=s.save(args.output/'raid.nbt')
    if hasattr(s,'routes'):(args.output/'route-repairs.json').write_text(json.dumps(s.routes,indent=2))
    (args.output/'material-map.json').write_text(json.dumps([{'reference':m['name'],'minecraft':b} for m,b in zip(materials,palette)],indent=2))
    (args.output/'build.json').write_text(json.dumps({'revision':args.revision,'size':s.size,'blocks':len(s.blocks),'angles':sum(len(v['angles']) for v in s.views),'metres_per_block':1},indent=2))
    print(json.dumps(result),len(s.blocks),'blocks',sum(len(v['angles']) for v in s.views),'angles')
