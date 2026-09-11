"""Conservative authored-block route audit; native collision checks remain required."""
import argparse
import json
import sys
from collections import deque
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'examples'))
from raid import build


def audit(s):
    def empty(p):return s.blocks.get(p,('minecraft:air',{},None))[0]=='minecraft:air'
    nodes={}
    for (x,y,z),(name,props,_) in s.blocks.items():
        if not 14<=y<=30 or name=='minecraft:air' or any(k in name for k in ('water','leaves','log','glass','bars')):continue
        if empty((x,y+1,z)) and empty((x,y+2,z)):
            nodes[(x,y+1,z)]=(name,props)
    def neighbors(p):
        x,y,z=p
        for dx,dz,facing in [(1,0,'east'),(-1,0,'west'),(0,1,'south'),(0,-1,'north')]:
            for dy in (-1,0,1):
                q=(x+dx,y+dy,z+dz)
                if q not in nodes:continue
                if dy==0:yield q
                elif dy==1 and nodes[q][0].endswith('_stairs') and nodes[q][1].get('facing')==facing:yield q
                elif dy==-1 and nodes[p][0].endswith('_stairs') and nodes[p][1].get('facing')=={'east':'west','west':'east','south':'north','north':'south'}[facing]:yield q
    stations={v['id']:tuple(int(a) for a in v['position']) for v in s.views if not v['id'].startswith('aerial') and v['id']!='overhead'}
    components=[];remaining=set(nodes)
    while remaining:
        start=min(remaining);queue=deque([start]);remaining.remove(start);members={start}
        while queue:
            for q in neighbors(queue.popleft()):
                if q in remaining:remaining.remove(q);members.add(q);queue.append(q)
        components.append(members)
    components.sort(key=len,reverse=True)
    result={'method':'conservative_authored_blocks_no_jump','nodes':len(nodes),'components':len(components),
            'largest_components':[len(c) for c in components[:20]],'stations':{name:next((i for i,c in enumerate(components) if p in c),None) for name,p in stations.items()}}
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--revision',type=int,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    s,_,_=build(Path('artifacts/raid/reference-grid'),a.revision);result=audit(s)
    a.output.write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
