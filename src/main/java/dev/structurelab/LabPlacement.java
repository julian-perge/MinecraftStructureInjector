package dev.structurelab;

import net.minecraft.core.BlockPos;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.nbt.*;
import net.minecraft.server.MinecraftServer;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.levelgen.structure.templatesystem.*;
import net.minecraft.world.phys.AABB;
import net.neoforged.neoforge.event.tick.ServerTickEvent;
import java.nio.file.Files;
import java.util.*;
import java.util.concurrent.*;

/** Clear/place one chunk column per tick; skip empty sections and retain native template BE loading. */
public final class LabPlacement {
    private static Work active;
    private static final int FLAGS=Block.UPDATE_CLIENTS|Block.UPDATE_SKIP_ALL_SIDEEFFECTS;
    private record Part(BlockPos offset,CompoundTag tag) {}
    private static final class Work {
        final LabBridge.Job job;
        final int[] size,clear;
        final List<Part> parts;
        final CompletableFuture<Void> done=new CompletableFuture<>();
        int clearing,placing;
        Work(LabBridge.Job job,int[] size,int[] clear,List<Part> parts){this.job=job;this.size=size;this.clear=clear;this.parts=parts;}
    }
    public static CompletableFuture<Void> begin(CompoundTag tag,LabBridge.Job job)throws Exception {
        LabSession.requireLab();
        if(active!=null)throw new IllegalStateException("Placement already active");
        ListTag dims=tag.getListOrEmpty("size");int[] size={dims.getIntOr(0,0),dims.getIntOr(1,0),dims.getIntOr(2,0)},clear=size.clone();
        if(LabSession.previousSize!=null)for(int i=0;i<3;i++)clear[i]=Math.max(clear[i],LabSession.previousSize[i]);
        if((long)clear[0]*clear[1]*clear[2]>LabSession.MAX_VOLUME*2)throw new IllegalArgumentException("Cleanup bounding volume exceeds limit");
        Map<Long,ListTag> groups=new LinkedHashMap<>();
        for(Tag entry:tag.getListOrEmpty("blocks")){
            CompoundTag b=(CompoundTag)entry;ListTag pos=b.getListOrEmpty("pos");int x=pos.getIntOr(0,0),z=pos.getIntOr(2,0);
            long key=((long)(x>>4)<<32)|(z>>4);CompoundTag local=b.copy();
            ListTag p=new ListTag();p.add(IntTag.valueOf(x&15));p.add(IntTag.valueOf(pos.getIntOr(1,0)));p.add(IntTag.valueOf(z&15));local.put("pos",p);
            groups.computeIfAbsent(key,k->new ListTag()).add(local);
        }
        List<Part> parts=new ArrayList<>();
        for(var entry:groups.entrySet()){
            int x=(int)(entry.getKey()>>32)*16,z=(int)(long)entry.getKey()*16;
            CompoundTag local=new CompoundTag();ListTag d=new ListTag();d.add(IntTag.valueOf(Math.min(16,size[0]-x)));d.add(IntTag.valueOf(size[1]));d.add(IntTag.valueOf(Math.min(16,size[2]-z)));
            local.put("size",d);local.put("palette",tag.getListOrEmpty("palette"));local.put("blocks",entry.getValue());local.put("entities",new ListTag());
            parts.add(new Part(new BlockPos(x,0,z),local));
        }
        Files.writeString(LabSession.ledger,LabBridge.GSON.toJson(clear));LabSession.previousSize=clear;
        active=new Work(job,size,clear,parts);job.state="clearing";job.processed=0;job.workTotal=((clear[0]+15)/16)*((clear[2]+15)/16)+parts.size();
        return active.done;
    }
    public static void closed(MinecraftServer server){if(active!=null&&active.job.world==server){active.done.completeExceptionally(new IllegalStateException("World closed during placement"));active=null;}}
    public static void tick(ServerTickEvent.Post event){
        Work w=active;if(w==null||w.job.world!=event.getServer())return;
        try{
            if(w.job.cancelled)throw new CancellationException("Placement cancelled");
            if(w.job.world!=LabSession.server)throw new IllegalStateException("Lab world changed");
            var level=w.job.world.overworld();int nx=(w.clear[0]+15)/16,nz=(w.clear[2]+15)/16;
            if(w.clearing<nx*nz){
                int cx=w.clearing%nx,cz=w.clearing/nx,x0=cx*16,z0=cz*16,x1=Math.min(x0+15,w.clear[0]-1),z1=Math.min(z0+15,w.clear[2]-1);
                var chunk=level.getChunk(cx,cz);int y0=LabSession.ORIGIN.getY(),y1=y0+w.clear[1]-1;
                level.getEntitiesOfClass(net.minecraft.world.entity.Entity.class,new AABB(x0,y0,z0,x1+1,y1+1,z1+1),e->!(e instanceof net.minecraft.world.entity.player.Player)).forEach(net.minecraft.world.entity.Entity::discard);
                for(int sy=y0>>4;sy<=y1>>4;sy++){
                    if(chunk.getSection(chunk.getSectionIndexFromSectionY(sy)).hasOnlyAir())continue;
                    for(BlockPos p:BlockPos.betweenClosed(x0,Math.max(y0,sy*16),z0,x1,Math.min(y1,sy*16+15),z1))
                        if(!level.getBlockState(p).isAir())level.setBlock(p,Blocks.AIR.defaultBlockState(),FLAGS);
                }
                w.clearing++;
            }else if(w.placing<w.parts.size()){
                w.job.state="placing";Part part=w.parts.get(w.placing++);StructureTemplate template=new StructureTemplate();template.load(BuiltInRegistries.BLOCK,part.tag);
                BlockPos origin=LabSession.ORIGIN.offset(part.offset);
                if(!template.placeInWorld(level,origin,origin,new StructurePlaceSettings().setKnownShape(true).setIgnoreEntities(true),net.minecraft.util.RandomSource.create(0),FLAGS))throw new IllegalStateException("Chunk template failed");
            }else{
                LabSession.previousSize=w.size;Files.writeString(LabSession.ledger,LabBridge.GSON.toJson(w.size));active=null;w.done.complete(null);return;
            }
            w.job.processed=w.clearing+w.placing;
        }catch(Throwable error){active=null;w.done.completeExceptionally(error);}
    }
}
