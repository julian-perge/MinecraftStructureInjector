package dev.structurelab;

import com.google.gson.*;
import net.minecraft.client.*;
import net.minecraft.core.BlockPos;
import net.minecraft.world.level.chunk.status.ChunkStatus;
import net.minecraft.world.phys.Vec3;
import net.neoforged.api.distmarker.Dist;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.fml.event.lifecycle.FMLClientSetupEvent;
import net.neoforged.neoforge.client.event.RenderFrameEvent;
import java.nio.file.*;
import java.util.concurrent.*;

@EventBusSubscriber(modid="structurelab",value=Dist.CLIENT)
public final class LabCapture {
    private static LabBridge.Job active;
    private static int index,stableFrames,oldFov,oldWidth,oldHeight,oldDistance;
    private static boolean oldPause,oldHidden,oldBob,writing;
    private static CameraType oldCamera;
    private static long movedAt;
    private static CompletableFuture<?> move;
    @SubscribeEvent public static void setup(FMLClientSetupEvent event){event.enqueueWork(LabBridge::start);}
    public static void begin(LabBridge.Job job){
        Minecraft mc=Minecraft.getInstance();
        if(mc.player==null||mc.level==null||job.world!=LabSession.server){LabBridge.fail(job,new IllegalStateException("Client lab world not ready"));return;}
        try{
            active=job;index=0;writing=false;
            oldPause=job.pauseBefore==null?mc.options.pauseOnLostFocus:job.pauseBefore;oldHidden=mc.gui.hud.isHidden();oldBob=mc.options.bobView().get();oldFov=mc.options.fov().get();oldCamera=mc.options.getCameraType();
            oldDistance=mc.options.renderDistance().get();int distance=oldDistance;
            for(JsonElement e:job.views)if(e.getAsJsonObject().has("render_distance"))distance=Math.max(distance,e.getAsJsonObject().get("render_distance").getAsInt());
            mc.options.renderDistance().set(distance);
            oldWidth=mc.getWindow().getWidth();oldHeight=mc.getWindow().getHeight();
            mc.options.pauseOnLostFocus=false;mc.options.bobView().set(false);mc.options.setCameraType(CameraType.FIRST_PERSON);
            if(!mc.gui.hud.isHidden())mc.gui.hud.toggle();
            mc.gui.setScreen(null);mc.setCameraEntity(mc.player);
            if(!mc.getWindow().isFullscreen())mc.getWindow().setWindowed(1920,1080);
            next();
        }catch(Exception e){abort(e);}
    }
    private static void next(){
        if(active.world!=LabSession.server)throw new IllegalStateException("Lab world changed during capture");
        JsonObject v=active.views.get(index).getAsJsonObject();
        Minecraft.getInstance().options.fov().set(v.get("fov").getAsInt());
        movedAt=System.nanoTime();stableFrames=0;
        var world=active.world;
        move=world.submit(()->{if(world!=LabSession.server)throw new IllegalStateException("Lab world changed during capture");LabSession.move(v);});
    }
    @SubscribeEvent public static void rendered(RenderFrameEvent.Post event){
        if(active==null||writing)return;
        Minecraft mc=Minecraft.getInstance();
        try{
            if(active.cancelled)throw new CancellationException("Capture cancelled");
            if(mc.level==null||mc.player==null||!LabSession.isLab()||active.world!=LabSession.server)throw new IllegalStateException("Lab disconnected during capture");
            long elapsed=System.nanoTime()-movedAt;
            if(elapsed>60_000_000_000L)throw new TimeoutException("View did not become render-ready within 60 seconds: "+index);
            if(!move.isDone())return;move.join();
            JsonObject view=active.views.get(index).getAsJsonObject();JsonArray p=view.getAsJsonArray("position");
            Vec3 target=new Vec3(p.get(0).getAsDouble(),p.get(1).getAsDouble()-60+view.get("eye_height").getAsDouble(),p.get(2).getAsDouble());
            boolean ready=mc.gui.screen()==null&&mc.gameRenderer.mainCamera().position().distanceToSqr(target)<0.04
                    &&Math.abs(net.minecraft.util.Mth.wrapDegrees(mc.gameRenderer.mainCamera().yRot()-view.get("yaw").getAsFloat()))<0.5
                    &&Math.abs(mc.gameRenderer.mainCamera().xRot()-view.get("pitch").getAsFloat())<0.5
                    &&mc.levelRenderer.hasRenderedAllSections()&&!mc.level.getChunkSource().getLightEngine().hasLightWork();
            BlockPos camera=BlockPos.containing(target);
            for(int x=-2;x<=2;x++)for(int z=-2;z<=2;z++)ready&=mc.level.getChunkSource().getChunk((camera.getX()>>4)+x,(camera.getZ()>>4)+z,ChunkStatus.FULL,false)!=null;
            stableFrames=ready?stableFrames+1:0;
            if(stableFrames<12||elapsed<2_000_000_000L)return;
            var framebuffer=mc.gameRenderer.mainRenderTarget();
            if(framebuffer.width!=1920||framebuffer.height!=1080)throw new IllegalStateException("Capture requires 1920x1080 framebuffer; actual "+framebuffer.width+"x"+framebuffer.height);
            writing=true;
            LabBridge.Job capturedJob=active;int capturedIndex=index;JsonObject capturedView=view.deepCopy();
            Path file=capturedJob.directory.resolve(view.get("id").getAsString()+"__"+view.get("angle").getAsString()+".png");
            Screenshot.takeScreenshot(framebuffer,image->{
                CompletableFuture.runAsync(()->{
                    try(image){
                        image.writeToFile(file);capturedView.addProperty("file",file.getFileName().toString());capturedView.addProperty("width",image.getWidth());capturedView.addProperty("height",image.getHeight());
                        capturedView.addProperty("revision",capturedJob.revision);capturedView.addProperty("status","complete");
                        capturedJob.captures.add(capturedView);capturedJob.captured=capturedIndex+1;LabBridge.persist(capturedJob);
                        mc.execute(()->{
                            writing=false;
                            if(active!=capturedJob)return;
                            if(capturedJob.cancelled||capturedJob.world!=LabSession.server){abort(new CancellationException("Lab job cancelled or world changed"));return;}
                            index++;
                            if(index>=active.views.size()){
                                writing=true; // wait for the server to return the player to spawn
                                capturedJob.world.submit(()->{if(capturedJob.world!=LabSession.server)throw new IllegalStateException("Lab world changed");LabSession.move(capturedJob.views.get(0).getAsJsonObject());})
                                    .whenComplete((ignored,error)->mc.execute(()->{if(error!=null){abort(error);return;}restore();active=null;LabBridge.complete(capturedJob);}));
                            }else next();
                        });
                    }catch(Exception e){mc.execute(()->abort(e));}
                });
            });
        }catch(Exception e){abort(e);}
    }
    private static void restore(){
        Minecraft mc=Minecraft.getInstance();mc.options.pauseOnLostFocus=oldPause;mc.options.bobView().set(oldBob);mc.options.fov().set(oldFov);mc.options.setCameraType(oldCamera);mc.options.renderDistance().set(oldDistance);
        if(mc.gui.hud.isHidden()!=oldHidden)mc.gui.hud.toggle();
        if(!mc.getWindow().isFullscreen())mc.getWindow().setWindowed(oldWidth,oldHeight);
    }
    private static void abort(Throwable e){if(active==null)return;LabBridge.Job j=active;try{restore();}finally{active=null;writing=false;LabBridge.fail(j,e);}}
}
