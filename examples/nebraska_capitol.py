"""Nebraska State Capitol, approximately one block per metre, vanilla Java 26.2.

North is -Z. Public-room locations follow the Legislature's three-page floor map.
Procedural mosaics/sculptures interpret the reference art at block resolution.
"""
from __future__ import annotations
import argparse
import json
import math
from pathlib import Path
import random
from structurelab import Structure

N=185
C=92
LIMESTONE="smooth_sandstone"
TRIM="cut_sandstone"
MARBLE="polished_granite"
BRONZE="waxed_weathered_copper"
ROOF="waxed_oxidized_copper"


class Capitol:
    def __init__(self, revision):
        self.revision=revision
        self.s=Structure((N,130,N))
        self.rooms={}
        self.rng=random.Random(1922)

    def b(self,x,y,z,block,props=None):
        self.s.set((int(x),int(y),int(z)),block,props)

    def fill(self,x0,y0,z0,x1,y1,z1,block,props=None):
        if x0<=x1 and y0<=y1 and z0<=z1:
            self.s.fill((x0,y0,z0),(x1,y1,z1),block,props)

    def shell(self,x0,y0,z0,x1,y1,z1,wall=LIMESTONE,floor="smooth_quartz",roof=ROOF):
        self.fill(x0,y0,z0,x1,y0,z1,floor)
        self.fill(x0,y0+1,z0,x1,y1,z0,wall)
        self.fill(x0,y0+1,z1,x1,y1,z1,wall)
        self.fill(x0,y0+1,z0,x0,y1,z1,wall)
        self.fill(x1,y0+1,z0,x1,y1,z1,wall)
        self.fill(x0,y1,z0,x1,y1,z1,roof)

    def disc(self,cx,y,cz,r,block,inner=0):
        for x in range(cx-r,cx+r+1):
            for z in range(cz-r,cz+r+1):
                d=(x-cx)**2+(z-cz)**2
                if inner**2<=d<=r*r:self.b(x,y,z,block)

    def line(self,a,b,block,width=0):
        steps=max(abs(b[i]-a[i]) for i in range(3))
        for t in range(steps+1):
            p=[round(a[i]+(b[i]-a[i])*t/max(1,steps)) for i in range(3)]
            self.fill(p[0]-width,p[1],p[2]-width,p[0]+width,p[1],p[2]+width,block)

    def floor_mosaic(self,cx,y,cz,r,style=0):
        colors=["black_concrete","white_terracotta","yellow_terracotta","cyan_terracotta","red_terracotta"]
        for x in range(cx-r,cx+r+1):
            for z in range(cz-r,cz+r+1):
                dx,dz=x-cx,z-cz;d=math.hypot(dx,dz)
                if d>r:continue
                if d>r-1 or r-3<d<r-2:mat="polished_blackstone"
                elif d>r-2:mat="smooth_quartz"
                else:
                    sector=int((math.atan2(dz,dx)+math.pi)*4/math.pi)
                    mat=colors[(sector+int(d/2)+style)%len(colors)]
                    if abs(dx)<1 or abs(dz)<1:mat="gold_block"
                self.b(x,y,z,mat)

    def window_north(self,x,z,y=12,w=2,h=4):
        self.fill(x-1,y-1,z-1,x+w,y-1,z-1,TRIM)
        self.fill(x,y,z,x+w-1,y+h-1,z,"gray_stained_glass")
        self.fill(x,y+h,z-1,x+w-1,y+h,z-1,"sandstone_slab")

    def window_east(self,x,z,y=12,w=2,h=4):
        self.fill(x+1,y-1,z-1,x+1,y-1,z+w,TRIM)
        self.fill(x,y,z,x,y+h-1,z+w-1,"gray_stained_glass")
        self.fill(x+1,y+h,z,x+1,y+h,z+w-1,"sandstone_slab")

    def arch(self,axis,fixed,center,bottom,spring,r,depth=1,material="smooth_quartz"):
        # Aperture with a true semicircular head and a one-block archivolt.
        for a in range(center-r-1,center+r+2):
            dx=abs(a-center)
            top=spring+round(math.sqrt(max(0,r*r-min(dx,r)**2)))
            for t in range(depth):
                if dx<=r:
                    if axis=="z":self.fill(a,bottom,fixed+t,a,top,fixed+t,"air")
                    else:self.fill(fixed+t,bottom,a,fixed+t,top,a,"air")
                if axis=="z":
                    self.b(a,top+1,fixed+t,material)
                    if dx==r+1:self.fill(a,bottom,fixed+t,a,spring,fixed+t,material)
                else:
                    self.b(fixed+t,top+1,a,material)
                    if dx==r+1:self.fill(fixed+t,bottom,a,fixed+t,spring,a,material)

    def grounds(self):
        self.fill(0,0,0,184,0,184,"stone")
        self.fill(0,1,0,184,1,184,"dirt")
        self.fill(0,2,0,184,2,184,"grass_block")
        # Perimeter paving and axial approaches.
        for a in (3,178):
            self.fill(a,2,3,a+3,2,181,"smooth_stone")
            self.fill(3,2,a,181,2,a+3,"smooth_stone")
        self.fill(75,2,0,109,2,26,"smooth_stone")
        self.fill(83,2,158,101,2,184,"smooth_stone")
        self.fill(0,2,84,26,2,100,"smooth_stone")
        self.fill(158,2,84,184,2,100,"smooth_stone")
        self.fill(22,2,22,162,2,25,"smooth_stone")
        self.fill(22,2,159,162,2,162,"smooth_stone")
        self.fill(22,2,22,25,2,162,"smooth_stone")
        self.fill(159,2,22,162,2,162,"smooth_stone")
        for x,z in [(12,16),(35,12),(57,12),(128,12),(150,12),(173,16),(12,48),(172,48),(12,135),(172,135),(15,171),(49,173),(137,173),(170,172)]:
            self.tree(x,3,z,7,"spruce")
        if self.revision>=2:
            for x,z in [(69,8),(115,8),(69,20),(115,20),(11,80),(11,104),(174,80),(174,104),(79,172),(105,172)]:
                self.lamp(x,3,z)
            # West Lincoln memorial: a bronze figure before an inscribed stone screen.
            self.fill(9,3,87,15,3,97,"cut_red_sandstone")
            self.fill(9,4,87,9,10,97,LIMESTONE)
            self.fill(12,4,91,14,5,93,"polished_andesite")
            self.fill(13,6,92,13,9,92,BRONZE);self.b(13,10,92,BRONZE)
            self.b(14,8,92,BRONZE);self.b(12,8,92,BRONZE)

    def tree(self,x,y,z,h,kind="oak"):
        self.fill(x,y,z,x,y+h,z,kind+"_log",{"axis":"y"})
        for dy in range(3,h+3):
            r=max(1,4-(dy-3)//2) if kind=="spruce" else (3 if dy<h else 2)
            for dx in range(-r,r+1):
                for dz in range(-r,r+1):
                    if abs(dx)+abs(dz)<=r+2:
                        self.b(x+dx,y+dy,z+dz,kind+"_leaves",{"persistent":"true"})

    def lamp(self,x,y,z):
        self.b(x,y,z,"polished_blackstone_wall")
        self.fill(x,y+1,z,x,y+3,z,"dark_oak_fence")
        self.b(x,y+4,z,"lantern",{"hanging":"false"})

    def base(self):
        # 437 ft = 133.2 m. The enclosed base is exactly 133 blocks square.
        self.shell(26,3,26,158,22,158,roof=ROOF,floor="polished_andesite")
        for y in (4,10,16):self.fill(27,y,27,157,y,157,"smooth_quartz")
        for y in (3,9,21,23):
            mat=TRIM if y!=3 else "polished_andesite"
            self.fill(25,y,25,159,y,26,mat);self.fill(25,y,158,159,y,159,mat)
            self.fill(25,y,26,26,y,158,mat);self.fill(158,y,26,159,y,158,mat)
        for x in range(30,155,6):
            if 78<=x<=106:continue
            for y,h in ((5,3),(12,4),(18,2)):
                self.window_north(x,26,y,h=h);self.window_north(x,158,y,h=h)
        for z in range(30,155,6):
            for y,h in ((5,3),(12,4),(18,2)):
                self.window_east(26,z,y,h=h);self.window_east(158,z,y,h=h)
        # Quiet office wings and circulation, laid out around each floor's cross and ring.
        for y in (4,10,16):
            for q in (42,142):
                self.fill(q,y+1,28,q,y+5,156,LIMESTONE)
                self.fill(28,y+1,q,156,y+5,q,LIMESTONE)
            for a in range(31,154,11):
                self.fill(a,y+1,27,a,y+5,41,LIMESTONE)
                self.fill(a,y+1,143,a,y+5,157,LIMESTONE)
                self.fill(27,y+1,a,41,y+5,a,LIMESTONE)
                self.fill(143,y+1,a,157,y+5,a,LIMESTONE)
                self.fill(a+3,y+1,42,a+4,y+3,42,"air")
                self.fill(a+3,y+1,142,a+4,y+3,142,"air")
                self.fill(42,y+1,a+3,42,y+3,a+4,"air")
                self.fill(142,y+1,a+3,142,y+3,a+4,"air")
                if self.revision>=2:
                    self.fill(a+3,y+1,30,a+6,y+1,31,"dark_oak_slab",{"type":"top"})
                    self.b(a+4,y+1,33,"dark_oak_stairs",{"facing":"north"})
                    self.fill(a+2,y+1,151,a+5,y+1,152,"dark_oak_slab",{"type":"top"})
                    self.b(a+3,y+1,149,"dark_oak_stairs",{"facing":"south"})
                    self.b(a+5,y+4,36,"sea_lantern")
                    self.b(37,y+4,a+5,"sea_lantern")
                    self.b(147,y+4,a+5,"sea_lantern")
                    self.b(a+5,y+4,147,"sea_lantern")
            # A ring passage and axial first-floor circulation stay traversable.
            self.fill(43,y+1,43,141,y+4,46,"air");self.fill(43,y+1,138,141,y+4,141,"air")
            self.fill(43,y+1,43,46,y+4,141,"air");self.fill(138,y+1,43,141,y+4,141,"air")
        for x in (52,104):
            for z in (49,103):self.courtyard(x,z)
        # Ground-level cross, with its information desk under the rotunda.
        self.fill(87,5,26,97,9,158,"air");self.fill(26,5,87,158,9,97,"air")
        self.fill(89,5,91,95,5,93,"dark_oak_planks")
        self.b(92,6,92,"lantern")
        for x,z in ((81,81),(101,81),(81,101),(101,101)):
            self.fill(x,5,z,x+2,21,z+5,"air")
            for y in range(5,21):
                xx=x+(y-5)%3;zz=z+(0 if ((y-5)//3)%2==0 else 2)
                self.b(xx,y,zz,"sandstone_stairs",{"facing":"east" if ((y-5)//3)%2==0 else "west"})

    def courtyard(self,x,z):
        w,d=28,33
        self.fill(x,4,z,x+w,24,z+d,"air")
        self.fill(x,3,z,x+w,3,z+d,"cut_red_sandstone")
        if self.revision>=2:
            for zz in (z-1,z+d+1):self.fill(x-1,4,zz,x+w+1,22,zz,LIMESTONE)
            for xx in (x-1,x+w+1):self.fill(xx,4,z,xx,22,z+d,LIMESTONE)
        for yy in (4,10,16,22):
            self.fill(x-1,yy,z-1,x+w+1,yy,z-1,TRIM);self.fill(x-1,yy,z+d+1,x+w+1,yy,z+d+1,TRIM)
            self.fill(x-1,yy,z,x-1,yy,z+d,TRIM);self.fill(x+w+1,yy,z,x+w+1,yy,z+d,TRIM)
        for xx in range(x+2,x+w,5):
            for yy in (6,12,18):
                self.window_north(xx,z-1,yy,h=3);self.window_north(xx,z+d+1,yy,h=3)
        for zz in range(z+2,z+d,5):
            for yy in (6,12,18):
                self.window_east(x-1,zz,yy,h=3);self.window_east(x+w+1,zz,yy,h=3)
        cx,cz=x+w//2,z+d//2
        for xx in (x+3,cx+3):
            for zz in (z+3,cz+3):
                self.fill(xx,3,zz,xx+8,3,zz+9,"grass_block")
                if self.revision>=2:
                    self.fill(xx,4,zz,xx+8,4,zz,"azalea_leaves",{"persistent":"true"})
                    self.fill(xx,4,zz+9,xx+8,4,zz+9,"azalea_leaves",{"persistent":"true"})
                    self.b(xx+4,4,zz+5,"rose_bush",{"half":"lower"});self.b(xx+4,5,zz+5,"rose_bush",{"half":"upper"})
        self.fill(cx-1,3,z,cx+1,3,z+d,"smooth_quartz")
        self.fill(x,3,cz-1,x+w,3,cz+1,"smooth_quartz")
        self.disc(cx,3,cz,5,"polished_andesite");self.disc(cx,4,cz,5,"sandstone_slab",4)
        self.disc(cx,4,cz,3,"water");self.disc(cx,4,cz,1,BRONZE)
        self.b(cx,5,cz,BRONZE);self.b(cx,6,cz,"water")
        self.fill(cx-3,5,cz-3,cx+3,5,cz+3,"air")
        self.b(cx,5,cz,BRONZE);self.b(cx,6,cz,BRONZE)
        if self.revision>=2:
            for dx,dz in ((-1,0),(1,0),(0,-1),(0,1)):self.b(cx+dx,6,cz+dz,"lightning_rod",{"facing":"up","waterlogged":"false"})
        for xx,zz in ((x+3,z+3),(x+w-3,z+d-3)):
            self.fill(xx,4,zz,xx+2,4,zz,"sandstone_stairs",{"facing":"south"})

    def entrance(self):
        self.fill(78,4,24,106,30,35,LIMESTONE)
        self.fill(84,10,25,100,28,39,"air")
        for y in (10,27,30):self.fill(77,y,23,107,y,35,TRIM)
        self.arch("z",23,92,11,20,6,depth=4)
        # Bronze entry screen below a high arched glazed transom.
        self.fill(87,11,26,97,17,26,"black_stained_glass")
        for x in (87,90,94,97):self.fill(x,11,25,x,17,25,BRONZE)
        self.fill(91,11,25,93,14,27,"air")
        for x in range(87,98):
            h=20+round(math.sqrt(max(0,25-(x-92)**2)))
            self.fill(x,19,26,x,h,26,"cyan_stained_glass")
        self.fill(91,19,25,93,24,25,TRIM)
        for step in range(8):
            z=10+step*2;y=3+step
            self.fill(77,3,z,107,y,z+1,LIMESTONE)
            self.fill(77,y,z,107,y,z,"sandstone_stairs",{"facing":"south"})
            for x in (74,75,76,108,109,110):self.fill(x,3,z,x,y+2,z+1,TRIM)
        # North pavilion relief panels and entrance retaining-wall medallions.
        for x in (79,103):
            self.fill(x,12,22,x+2,25,23,TRIM)
            self.fill(x,13,21,x+2,15,21,"chiseled_sandstone")
        if self.revision>=2:
            for x in (74,108):
                self.fill(x,5,9,x+2,9,10,"chiseled_sandstone")
            for x in range(81,106,4):self.b(x,29,22,"chiseled_sandstone")
        self.rooms["vestibule"]=[92,11,32]

    def great_hall(self):
        self.fill(85,11,35,99,26,81,"air")
        self.fill(85,10,35,99,10,81,"smooth_quartz")
        for x in (84,100):self.fill(x,11,35,x,25,81,LIMESTONE)
        for z in range(37,81):
            for x in range(85,100):
                dx=x-92;y=20+round(math.sqrt(max(0,49-dx*dx))*.72)
                self.b(x,y,z,"yellow_terracotta" if (x+z)%9==0 else "smooth_sandstone")
        for z in (39,49,59,69,79):
            for x in (85,99):
                self.fill(x,11,z,x,18,z,MARBLE);self.b(x,19,z,"chiseled_quartz_block")
            for x in range(85,100):
                yy=20+round(math.sqrt(max(0,49-(x-92)**2))*.72)
                self.b(x,yy-1,z,"smooth_quartz")
            self.b(92,23,z,"sea_lantern")
        for z in (46,60,74):self.floor_mosaic(92,10,z,5,style=z%3)
        for x in (85,99):
            for z in (44,54,64,74):
                self.arch("x",x-1 if x==85 else x, z,11,16,2,depth=2)
                if self.revision>=2:
                    self.b(x,11,z-3,"chiseled_sandstone");self.b(x,12,z-3,BRONZE)
        if self.revision>=2:
            # Cover the vault continuously; glazed side apertures face the gardens.
            for z in range(35,82):
                for x in range(84,101):
                    yy=20+round(math.sqrt(max(0,49-(x-92)**2))*.72)
                    self.b(x,yy+1,z,LIMESTONE);self.b(x,yy+2,z,ROOF)
            for x in (84,100):
                for z in (44,54,64,74):
                    self.fill(x,12,z-1,x,17,z+1,"light_gray_stained_glass")
            for z in (40,50,60,70,78):
                for x in (86,98):self.b(x,14,z,"lantern")
        self.rooms["great_hall"]=[92,11,42]

    def rotunda(self):
        self.fill(80,11,80,104,36,104,"air")
        if self.revision>=2:
            for a in (80,104):
                self.fill(80,11,a,104,34,a,LIMESTONE)
                self.fill(a,11,80,a,34,104,LIMESTONE)
        # Square piers make the dome stand on four broad arches.
        for x,z in ((80,80),(101,80),(80,101),(101,101)):
            self.fill(x,11,z,x+3,28,z+3,LIMESTONE)
            self.fill(x,18,z,x+3,18,z+3,TRIM)
        self.floor_mosaic(92,10,92,11,style=1)
        far=103 if self.revision>=2 else 102
        for axis,fixed in (("z",80),("z",far),("x",80),("x",far)):
            self.arch(axis,fixed,92,11,21,8,depth=2,material=TRIM)
        for x in range(81,104):
            for z in range(81,104):
                r=math.hypot(x-92,z-92)
                if r<=11.6:
                    y=25+round(math.sqrt(max(0,121-r*r))*.8)
                    self.b(x,y,z,"yellow_terracotta" if int(r)%3 else "gold_block")
                    if self.revision>=2 and (x+z)%4==0:self.b(x,y,z,"orange_terracotta")
        self.b(92,32,92,"sea_lantern")
        for x,z in ((83,88),(101,88),(83,97),(101,97)):
            self.fill(x,11,z,x,18,z,MARBLE);self.b(x,19,z,"chiseled_quartz_block")
        if self.revision>=2:
            for x,z in ((85,85),(99,85),(85,99),(99,99),(92,84),(92,100),(84,92),(100,92)):
                self.b(x,10,z,"sea_lantern");self.b(x,11,z,"white_carpet")
            for x,z in ((84,87),(100,87),(84,98),(100,98)):
                self.b(x,14,z,"lantern")
            for dx,dz in ((-1,0),(1,0),(0,-1),(0,1)):
                x,z=92+dx*9,92+dz*9
                self.b(x,21,z,"sea_lantern")
                if dx:
                    self.fill(x,22,z-4,x,25,z+4,"red_terracotta")
                    for dz2 in (-3,0,3):self.fill(x,23,z+dz2,x,25,z+dz2,"yellow_terracotta")
                else:
                    self.fill(x-4,22,z,x+4,25,z,"red_terracotta")
                    for dx2 in (-3,0,3):self.fill(x+dx2,23,z,x+dx2,25,z,"yellow_terracotta")
        self.rooms["rotunda"]=[92,11,87]

    def chamber(self,west=True):
        x0,x1=(44,79) if west else (105,140)
        self.fill(x0,11,84,x1,30,100,"air")
        self.fill(x0,10,84,x1,10,100,"oak_planks" if west else "orange_terracotta")
        self.fill(x0,11,83,x1,25,83,LIMESTONE);self.fill(x0,11,101,x1,25,101,LIMESTONE)
        self.fill(x0,11,84,x0,27,100,LIMESTONE);self.fill(x1,11,84,x1,27,100,LIMESTONE)
        for x in range(x0,x1+1):
            for z in range(83,102):
                y=22+round(math.sqrt(max(0,81-(z-92)**2))*.65)
                mat="smooth_sandstone" if west else "blue_terracotta"
                self.b(x,y,z,mat)
                if self.revision>=2 and ((x-x0)%7==0 or abs(z-92)==7):self.b(x,y-1,z,TRIM if west else "yellow_terracotta")
        dais=x0+3 if west else x1-3
        self.fill(dais-1,11,87,dais+1,11,97,"dark_oak_planks")
        self.fill(dais,12,89,dais,13,95,"dark_oak_planks")
        self.fill(dais-1 if west else dais+1,12,91,dais-1 if west else dais+1,14,93,"dark_oak_stairs",{"facing":"east" if west else "west"})
        self.arch("x",x0+1 if west else x1-1,92,12,20,6,material="smooth_quartz")
        # A dark announcement board, galleries, red-marble supports and desks.
        bx=x0+1 if west else x1-1
        self.fill(bx,18,90,bx,22,94,"black_concrete")
        self.fill(bx,17,89,bx,17,95,"gold_block")
        for x in range(x0+7,x1-4,4):
            for z in (86,90,94,98):
                self.fill(x,11,z,x+1,11,z+1,"dark_oak_slab",{"type":"top"})
                chair=x+2 if west else x-1
                self.b(chair,11,z,"dark_oak_stairs",{"facing":"west" if west else "east"})
                if self.revision>=2:self.b(x,12,z,"birch_pressure_plate")
        for z in (84,100):
            self.fill(x0+2,18,z,x1-2,18,z,"smooth_quartz")
            self.fill(x0+2,19,z,x1-2,19,z,"sandstone_wall")
            for x in range(x0+3,x1-1,7):
                self.fill(x,11,z,x,17,z,MARBLE)
                self.b(x,17,z,"chiseled_quartz_block")
        self.fill(x1 if west else x0,11,90,x1 if west else x0,15,94,"air")
        for x in range(x0+5,x1-3,7):self.b(x,25,92,"sea_lantern")
        if self.revision>=2:
            # Low suspended lamps illuminate desks, not just the high barrel vault.
            for x in range(x0+5,x1-3,7):
                for z in (88,96):
                    self.fill(x,18,z,x,24,z,"iron_chain",{"axis":"y"})
                    self.b(x,17,z,"sea_lantern")
                    for dx,dz in ((-1,0),(1,0),(0,-1),(0,1)):
                        self.b(x+dx,17,z+dz,"gold_block")
                for z in (83,101):
                    self.fill(x-1,20,z,x+1,21,z,"light_gray_stained_glass")
                for z in (85,99):self.b(x,13,z,"lantern")
            for x in range(x0,x1+1):
                for z in range(83,102):
                    yy=22+round(math.sqrt(max(0,81-(z-92)**2))*.65)
                    self.b(x,yy+1,z,ROOF)
        self.rooms["norris" if west else "warner"]=[x1-2 if west else x0+2,11,92]

    def public_suites(self):
        # Supreme Court on the south axis, Governor in the northeast quadrant.
        self.fill(80,11,145,104,23,156,"air")
        self.fill(80,10,145,104,10,156,"red_carpet")
        self.fill(80,22,145,104,22,156,"dark_oak_planks")
        self.fill(82,11,153,102,11,155,"dark_oak_planks")
        self.fill(82,12,153,102,12,153,"dark_oak_slab",{"type":"top"})
        for x in range(83,103,3):self.b(x,12,155,"dark_oak_stairs",{"facing":"north"})
        for z in (146,149):
            for x in (83,87,97,101):self.b(x,11,z,"oak_stairs",{"facing":"south"})
        self.fill(90,11,142,94,15,146,"air")
        self.b(92,21,150,"sea_lantern")
        if self.revision>=2:
            self.fill(80,23,145,104,23,156,ROOF)
            for x in (84,92,100):
                self.fill(x,17,150,x,21,150,"iron_chain",{"axis":"y"})
                self.b(x,16,150,"sea_lantern")
                for z in (146,155):self.b(x,14,z,"lantern")
        self.fill(118,11,28,153,15,39,"air")
        self.fill(118,10,28,153,10,39,"dark_oak_planks")
        self.fill(144,11,30,150,11,32,"dark_oak_planks")
        self.fill(144,12,30,150,12,32,"dark_oak_slab",{"type":"bottom"})
        self.b(147,11,29,"dark_oak_stairs",{"facing":"south"})
        self.fill(120,11,29,120,14,38,"bookshelf")
        self.fill(129,10,30,138,10,37,"red_wool")
        self.fill(128,11,31,128,11,36,"dark_oak_stairs",{"facing":"east"})
        self.fill(140,11,31,140,11,36,"dark_oak_stairs",{"facing":"west"})
        for x in (125,135,145):self.b(x,15,34,"sea_lantern")
        self.fill(132,11,40,134,14,43,"air")
        self.rooms["supreme_court"]=[92,11,145]
        self.rooms["governor"]=[123,11,35]

    def tower(self):
        # The occupied shaft rises above the domed rotunda, with stepped buttresses.
        if self.revision>=2:
            for a in (78,106):
                self.fill(78,23,a,106,35,a,LIMESTONE)
                self.fill(a,23,78,a,35,106,LIMESTONE)
            for a in (77,107):
                self.fill(77,23,a,107,27,a,TRIM)
                self.fill(a,23,77,a,27,107,TRIM)
        self.shell(78,35,78,106,40,106,roof=TRIM)
        self.shell(81,40,81,103,91,103,roof=TRIM)
        for x in (79,102):
            for z in (79,102):
                self.fill(x,36,z,x+3,89,z+3,LIMESTONE)
                self.fill(x,90,z,x+3,92,z+3,TRIM)
                if self.revision>=2:
                    self.fill(x+1,79,z-1,x+1,87,z-1,"black_stained_glass")
                    self.fill(x-1,79,z+1,x-1,87,z+1,"black_stained_glass")
        for y in (41,48,55,62,69,76,83,90):
            self.fill(82,y,82,102,y,102,"smooth_stone")
            self.fill(89,y+1,89,95,y+6,95,LIMESTONE)
            self.fill(91,y+1,89,93,y+3,89,"air")
            self.b(86,y+5,86,"sea_lantern");self.b(98,y+5,98,"sea_lantern")
            if self.revision>=2:
                for x,z in ((84,85),(98,85),(84,98),(98,98)):
                    self.b(x,y+1,z,"spruce_slab",{"type":"top"});self.b(x,y+1,z+1,"spruce_stairs",{"facing":"north"})
            # Climbable service core for the model's tower.
            self.fill(90,y+1,91,90,y+6,91,"ladder",{"facing":"east"})
        for a in (85,88,92,96,99):
            for y in range(43,84):
                mat="black_stained_glass" if (y-43)%7 not in (5,6) else BRONZE
                self.b(a,y,80,mat);self.b(a,y,104,mat)
                self.b(80,y,a,mat);self.b(104,y,a,mat)
                # recess into the actual shaft wall
                self.b(a,y,81,mat);self.b(a,y,103,mat);self.b(81,y,a,mat);self.b(103,y,a,mat)
            for y in (85,88):
                self.b(a,y,81,"black_stained_glass");self.b(a,y,103,"black_stained_glass")
                self.b(81,y,a,"black_stained_glass");self.b(103,y,a,"black_stained_glass")
        # Observation/Memorial Chamber octagon and pierced upper screen.
        if self.revision>=2:self.fill(82,93,82,102,107,102,"air")
        for y in range(92,109):
            for x in range(81,104):
                for z in range(81,104):
                    dx,dz=abs(x-C),abs(z-C)
                    inside=max(dx,dz)<=11 and dx+dz<=17
                    edge=max(dx,dz)==11 or dx+dz==17
                    if inside and (edge or y in (92,108)):
                        self.b(x,y,z,TRIM if y in (92,105,108) else LIMESTONE)
        for a in (87,91,95):
            self.fill(a,95,81,a+1,103,81,"black_stained_glass")
            self.fill(a,95,103,a+1,103,103,"black_stained_glass")
            self.fill(81,95,a,81,103,a+1,"black_stained_glass")
            self.fill(103,95,a,103,103,a+1,"black_stained_glass")
        self.floor_mosaic(C,92,C,9,2)
        if self.revision>=2:
            for a in range(83,102,3):
                self.b(a,107,80,"chiseled_sandstone");self.b(a,107,104,"chiseled_sandstone")
                self.b(80,107,a,"chiseled_sandstone");self.b(104,107,a,"chiseled_sandstone")
        self.b(92,106,92,"sea_lantern")
        if self.revision>=2:
            for x,z in ((86,86),(98,86),(86,98),(98,98)):
                self.b(x,92,z,"sea_lantern");self.b(x,93,z,"white_carpet")
                self.b(x,99,z,"lantern")
        # Blue-and-gold thunderbird frieze below the shallow gold-tiled cap.
        for y in (108,109,110):
            for x in range(82,103):
                for z in range(82,103):
                    rr=math.hypot(x-C,z-C)
                    if 8.2<=rr<=10:
                        self.b(x,y,z,"blue_terracotta" if y==109 else "yellow_terracotta")
                        if (x+z)%5==0:self.b(x,y,z,"gold_block")
        for y in range(110,117):
            r=round(9*math.sqrt(max(0,1-((y-110)/7)**2)))
            self.disc(C,y,C,r,"gold_block",max(0,r-2))
        self.disc(C,117,C,2,"gold_block")
        self.fill(91,118,91,93,119,93,BRONZE)
        # Six-metre Sower: forward leg, torso, seed bag, extended sowing arm.
        self.fill(91,120,92,91,122,92,BRONZE);self.fill(93,120,93,93,122,93,BRONZE)
        self.fill(91,122,92,93,123,93,BRONZE);self.b(92,124,92,BRONZE);self.b(92,125,92,BRONZE)
        self.line((93,123,92),(96,122,91),BRONZE)
        self.line((91,123,92),(89,122,93),BRONZE);self.b(90,122,93,"waxed_exposed_copper")
        self.rooms["memorial"]=[92,93,87]

    def details(self):
        if self.revision<2:return
        # Cornice rhythm and shallow relief panels, deliberately subordinate to the broad base.
        for a in range(29,157,4):
            for x,z in ((a,24),(a,160),(24,a),(160,a)):
                self.b(x,22,z,"chiseled_sandstone")
        for a in range(32,155,12):
            for x,z in ((a,25),(a,159),(25,a),(159,a)):
                self.b(x,20,z,"chiseled_sandstone")
        # South lawgiver figures, interpreted as small limestone reliefs.
        for x in range(70,116,5):
            self.fill(x,24,143,x+1,25,143,TRIM);self.b(x,26,143,"chiseled_sandstone")
        # Four corner lanterns at the upper tower's transition.
        for x,z in ((80,80),(104,80),(80,104),(104,104)):
            self.b(x,39,z,"chiseled_sandstone")
        if self.revision>=3:
            self.final_refinements()
            for x,z in ((72,20),(112,20)):
                self.fill(x,3,z,x,13,z,"iron_bars")
                for xx in range(x+1,x+5):
                    for yy in range(10,14):self.b(xx,yy,z,"white_wool" if yy%2 else "red_wool")
                self.fill(x+1,12,z,x+2,13,z,"blue_wool")

    def final_refinements(self):
        # The southern public gallery continues the Great Hall's vaulted cross.
        self.fill(85,11,105,99,27,141,"air")
        self.fill(85,10,105,99,10,141,"smooth_quartz")
        for x in (84,100):self.fill(x,11,105,x,25,141,LIMESTONE)
        for z in range(105,142):
            for x in range(85,100):
                yy=20+round(math.sqrt(max(0,49-(x-92)**2))*.72)
                self.b(x,yy,z,LIMESTONE);self.b(x,yy+1,z,ROOF)
        for z in (110,120,130,140):
            for x in (85,99):
                self.fill(x,11,z,x,18,z,MARBLE)
                self.b(x,19,z,"chiseled_quartz_block")
            self.b(92,23,z,"sea_lantern")
            for x in (84,100):self.fill(x,14,z-2,x,18,z+2,"light_gray_stained_glass")
        for z in (113,127,139):self.floor_mosaic(92,10,z,5)
        # Lighter ceramic dome, gold rings and a small constellation of inset lamps.
        for x in range(81,104):
            for z in range(81,104):
                r=math.hypot(x-92,z-92)
                if r<=11.6:
                    yy=25+round(math.sqrt(max(0,121-r*r))*.8)
                    mat="gold_block" if int(r) in (3,8) else "yellow_terracotta"
                    if abs(x-92)==abs(z-92):mat="white_terracotta"
                    self.b(x,yy,z,mat)
        for dx,dz in ((-6,-6),(6,-6),(-6,6),(6,6),(0,0)):
            x,z=92+dx,92+dz;yy=25+round(math.sqrt(max(0,121-dx*dx-dz*dz))*.8)
            self.b(x,yy,z,"sea_lantern")
        # Small figurative panels: sky, prairie, wheat, earth and stylized people.
        colors={"s":"light_blue_terracotta","w":"yellow_terracotta","e":"brown_terracotta","g":"green_terracotta","h":"white_terracotta","r":"red_terracotta"}
        panel=["ggwgggwgg","wwrwwwrww","sshsss hss".replace(" ",""),"sssssssss"]
        for dx,dz in ((-1,0),(1,0),(0,-1),(0,1)):
            x,z=92+dx*9,92+dz*9
            for y,row in enumerate(panel,22):
                for a,char in enumerate(row):self.b(x if dx else 88+a,y,88+a if dx else z,colors[char])
        # Refine the dais, and give the two rooms different carpeted central aisles.
        for x0,x1,west in ((44,79,True),(105,140,False)):
            bx=x0+1 if west else x1-1
            for z in (88,96):self.fill(bx,18,z,bx,22,z,"gold_block")
            self.fill(bx,23,88,bx,23,96,"gold_block")
            self.fill(x0+7,10,92,x1-5,10,93,"red_wool" if west else "blue_wool")
        # Governor's reception and office are separate, with a broad doorway.
        self.fill(141,11,28,141,15,39,LIMESTONE)
        self.fill(141,11,33,141,14,35,"air")
        self.fill(142,10,29,151,10,37,"green_wool")
        for x in (145,149):self.b(x,12,31,"birch_pressure_plate")
        # Continuous climbable tower access; floor slabs no longer interrupt ladders.
        self.fill(89,36,91,89,92,91,LIMESTONE)
        self.fill(90,36,91,90,92,91,"ladder",{"facing":"east"})
        self.fill(89,93,91,90,94,91,"air")
        # The actual Sower has an asymmetric outstretched arm and a seed bag.
        self.fill(89,120,90,97,125,94,"air")
        self.fill(91,120,92,91,122,92,BRONZE)
        self.fill(93,120,93,93,121,93,BRONZE)
        self.fill(92,122,92,93,123,93,BRONZE)
        self.b(92,124,92,BRONZE);self.b(92,125,92,BRONZE)
        self.line((93,123,92),(96,122,90),BRONZE)
        self.line((92,123,93),(90,122,93),BRONZE)
        self.b(90,121,93,"waxed_exposed_copper")

    def views(self):
        def view(id,pos,target,label,fov=70,spawn=False):
            self.s.view(id,pos,[{"id":"overview",**self.s.look_at(pos,target),"fov":fov}],label=label,spawn=spawn)
            self.s.views[-1]["render_distance"]=24
        view("spawn",(92,35,-76),(92,57,92),"North elevation — complete Capitol silhouette",60,True)
        view("northwest_aerial",(-38,112,-28),(92,35,92),"Northwest aerial — square base, tower, four courtyards",65)
        view("southwest_aerial",(-28,107,217),(92,34,92),"Southwest aerial — south wing and courtyard plan",65)
        view("north_entrance",(92,5,1),(92,18,27),"North entrance — grand stair, retaining walls and bronze portal",72)
        view("courtyard",(60.5,6,76.5),(69,8,57),"Northwest courtyard — fountain and red sandstone garden",82)
        view("great_hall",(92,11,41),(92,18,73),"Great Hall — marble columns, vaults and mosaic pavement",78)
        view("rotunda",(92,11,85),(92,23,96),"Central rotunda — four arches and mosaic dome",90)
        view("rotunda_floor",(92,26,92),(92,10,92),"Rotunda — geometric interpretation of the floor mosaic",75)
        view("norris",(76,12,92),(47,17,92),"Norris Legislative Chamber — dais, desks and galleries",82)
        view("warner",(108,12,92),(136,17,92),"Warner Chamber — patterned ceiling and seating",82)
        view("supreme_court",(92,12,144),(92,15,155),"Supreme Court — seven-seat bench and public seating",85)
        view("governor",(122,12,35),(148,12,31),"Governor's Suite — northeast reception and office",78)
        view("memorial",(92,94,87),(92,101,99),"Memorial Chamber — octagonal upper room",90)
        view("crown",(124,119,64),(92,115,92),"Tower crown — blue frieze, gold dome and Sower",58)
        if self.revision>=3:
            view("south_gallery",(92,11,108),(92,17,136),"South gallery — vaulted connection to the Supreme Court",78)
            view("governor_office",(142.5,11,36.5),(147,12,30),"Governor's office — desk, green carpet and north windows",78)

    def build(self,path):
        for name in ("grounds","base","entrance","great_hall","rotunda"):
            getattr(self,name)();print(name,len(self.s.blocks),flush=True)
        self.chamber(True);self.chamber(False);self.public_suites();self.tower();self.details();self.views()
        stats={"revision":self.revision,"size":self.s.size,"bounding_volume":math.prod(self.s.size),"block_records":len(self.s.blocks),"solid_blocks":sum(name!="minecraft:air" for name,_,_ in self.s.blocks.values()),"scale":"approximately 1 block per metre","building_base":[133,133],"north":"-Z","rooms":self.rooms,"views":len(self.s.views)}
        result=self.s.save(path)
        Path(path).with_suffix(".model.json").write_text(json.dumps(stats,indent=2))
        print(json.dumps({**result,**stats},indent=2),flush=True)
        return result


if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--revision",type=int,choices=[1,2,3],default=1);p.add_argument("--output",type=Path,required=True)
    args=p.parse_args();Capitol(args.revision).build(args.output)
