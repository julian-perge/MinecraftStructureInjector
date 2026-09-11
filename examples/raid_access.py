"""Minimal-cost circulation repairs for the measured Raid geometry."""
import heapq

CONNECTIONS=[('garage','gym'),('gym','art'),('art','circle_north'),
 ('circle_north','circle_east'),('circle_east','circle_south'),
 ('circle_south','laundry_balcony'),('laundry_balcony','laundry'),
 ('circle_south','garden_steps'),('garden_steps','garden'),
 ('garden','basketball_entry'),('basketball_entry','basketball'),
 ('basketball','pool_south'),('pool_south','pool_bar'),('pool_bar','hot_tub'),
 ('hot_tub','pool_north'),('pool_north','garage_court'),('garage_court','garage'),
 ('garden_steps','kitchen'),('kitchen','money'),('money','pool_bar'),
 ('kitchen','central_court'),('central_court','court_north'),
 ('court_north','bedroom'),('bedroom','bedroom_balcony'),
 ('bedroom','garage_court'),('central_court','court_east'),('court_east','art'),
 ('circle_east','drive_entry')]


def repair(s, revision=3):
    stations={v['id']:tuple(int(a) for a in v['position']) for v in s.views}
    def name(p):return s.blocks.get(p,('minecraft:air',{},None))[0]
    def cost(p):
        x,y,z=p
        floor=name((x,y-1,z));body=[name((x,y+h,z)) for h in (0,1)]
        # Strongly favor existing openings and supported floors. Water is not
        # used as a shortcut across the pool, and solid walls are expensive.
        return 1+sum(35 if b!='minecraft:air' else 0 for b in body)+(20 if floor=='minecraft:air' else 0)+(150 if 'water' in floor or any('water' in b for b in body) else 0)
    paths=[];stair_directions={}
    for a,b in CONNECTIONS:
        start,end=stations[a],stations[b]
        low=[max(1,min(start[i],end[i])-(10 if i!=1 else 2)) for i in range(3)]
        high=[min(s.size[i]-2,max(start[i],end[i])+(10 if i!=1 else 2)) for i in range(3)]
        def heuristic(p):return sum(abs(v-w) for v,w in zip(p,end))
        queue=[(heuristic(start),0,start)];distance={start:0};previous={}
        while queue:
            _,score,p=heapq.heappop(queue)
            if score!=distance[p]:continue
            if p==end:break
            x,y,z=p
            for dx,dz in [(1,0),(-1,0),(0,1),(0,-1)]:
                for dy in (-1,0,1):
                    q=(x+dx,y+dy,z+dz)
                    if any(not low[i]<=q[i]<=high[i] for i in range(3)):continue
                    # Prevent stair hairpins: keep the direction of successive
                    # height changes until there is a level landing.
                    if dy and p in previous:
                        last=previous[p]
                        if p[1]!=last[1] and (dx,dz)!=(p[0]-last[0],p[2]-last[2]):continue
                    candidate=score+cost(q)+abs(dy)*3
                    if candidate<distance.get(q,float('inf')):
                        distance[q]=candidate;previous[q]=p;heapq.heappush(queue,(candidate+heuristic(q),candidate,q))
        if end not in distance:raise ValueError(f'No circulation repair found: {a} to {b}')
        route=[end]
        while route[-1]!=start:route.append(previous[route[-1]])
        route.reverse()
        # A centreline with two blocks of headroom is the minimum guaranteed
        # route. Adjacent existing openings retain their original widths.
        for x,y,z in route:
            if name((x,y-1,z))=='minecraft:air':s.set((x,y-1,z),'smooth_stone')
            s.set((x,y,z),'air');s.set((x,y+1,z),'air')
        for p,q in zip(route,route[1:]):
            if p[1]==q[1]:continue
            lower,higher=(p,q) if p[1]<q[1] else (q,p)
            dx,dz=higher[0]-lower[0],higher[2]-lower[2]
            facing={(1,0):'east',(-1,0):'west',(0,1):'south',(0,-1):'north'}[(dx,dz)]
            stair=(higher[0],higher[1]-1,higher[2])
            stair_directions.setdefault(stair,set()).add(facing)
            s.set(stair,'stone_brick_stairs',{'facing':facing,'half':'bottom','shape':'straight','waterlogged':'false'})
            s.set((lower[0],lower[1]+2,lower[2]),'air')
        paths.append({'from':a,'to':b,'points':route,'cost':distance[end]})
    if revision>=4:
        for p,directions in stair_directions.items():
            if len(directions)>1:
                # A full landing with half-height approaches also joins safely
                # to a further stair immediately above the junction.
                upper=any(name((p[0]+dx,p[1]+1,p[2]+dz)).endswith('_stairs') for dx,dz in [(1,0),(-1,0),(0,1),(0,-1)])
                if upper:
                    s.set(p,'stone_bricks')
                    for direction in directions:
                        dx,dz={'east':(1,0),'west':(-1,0),'south':(0,1),'north':(0,-1)}[direction]
                        s.set((p[0]-dx,p[1],p[2]-dz),'stone_brick_slab',{'type':'bottom','waterlogged':'false'})
                else:s.set(p,'stone_brick_slab',{'type':'bottom','waterlogged':'false'})
    return paths
