"""Exercise generated circulation routes through the running lab's native movement."""
import argparse,json
from pathlib import Path
from structurelab.server import test_walking_route

p=argparse.ArgumentParser();p.add_argument('folder',type=Path);a=p.parse_args()
routes=json.loads((a.folder/'route-repairs.json').read_text());results=[]
for route in routes:
    points=[[x+.5,y,z+.5] for x,y,z in route['points']]
    for direction,positions in [('forward',points),('reverse',list(reversed(points)))]:
        result=test_walking_route(positions)
        result.update({'from':route['from'],'to':route['to'],'direction':direction})
        results.append(result)
        print(route['from'],route['to'],direction,result['passed'],result['reached'],result['total'],flush=True)
        (a.folder/'native-walking.json').write_text(json.dumps(results,indent=2))
print('PASSED',sum(r['passed'] for r in results),'OF',len(results))
