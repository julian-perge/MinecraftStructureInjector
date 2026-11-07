package dev.structurelab;

import com.google.gson.*;
import net.minecraft.client.Minecraft;
import net.minecraft.client.Screenshot;
import net.minecraft.client.gui.screens.Screen;
import net.minecraft.commands.CommandSource;
import net.minecraft.core.BlockPos;
import net.minecraft.core.registries.Registries;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.Identifier;
import net.minecraft.resources.ResourceKey;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.util.FileUtil;
import net.minecraft.world.level.GameType;
import net.minecraft.world.level.LevelSettings;
import net.minecraft.world.level.WorldDataConfiguration;
import net.minecraft.world.level.levelgen.WorldOptions;
import net.minecraft.world.level.levelgen.presets.WorldPresets;
import java.util.*;
import java.util.concurrent.*;

/** Operations for testing other mods in any world: commands, camera aim, Jade text, guide screens, screenshots and chunk state. */
public final class LabTestOps {
    static boolean handles(String op){
        return switch(op){case "client","new_world","command","aim","jade_tooltip","guide","close_screen","screenshot","chunk_loaded","quit"->true;default->false;};
    }
    static JsonObject rpc(String op,JsonObject request)throws Exception {
        return switch(op){
            case "client"->onClient(LabTestOps::client);
            case "new_world"->onClient(()->newWorld(request.get("name").getAsString()));
            case "command"->LabBridge.onServer(()->command(request.get("command").getAsString()));
            case "aim"->aim(request.getAsJsonArray("from"),request.getAsJsonArray("at"));
            case "jade_tooltip"->{
                if(!net.neoforged.fml.ModList.get().isLoaded("jade"))throw new IllegalStateException("Jade is not installed");
                yield LabJade.lastTooltip();
            }
            case "guide"->onClient(()->guide(request));
            case "close_screen"->onClient(()->{Minecraft.getInstance().setScreen(null);return new JsonObject();});
            case "screenshot"->screenshot(request.get("name").getAsString());
            case "chunk_loaded"->LabBridge.onServer(()->chunkLoaded(request));
            case "quit"->{Minecraft.getInstance().execute(Minecraft.getInstance()::stop);yield new JsonObject();}
            default->throw new IllegalArgumentException("Unknown operation: "+op);
        };
    }
    static <T>T onClient(Callable<T> fn)throws Exception {
        CompletableFuture<T> result=new CompletableFuture<>();
        Minecraft.getInstance().execute(()->{try{result.complete(fn.call());}catch(Throwable e){result.completeExceptionally(e);}});
        return result.get(30,TimeUnit.SECONDS);
    }
    static JsonObject client(){
        Minecraft mc=Minecraft.getInstance();JsonObject out=new JsonObject();
        out.addProperty("in_world",mc.level!=null&&mc.player!=null);out.addProperty("paused",mc.isPaused());
        out.addProperty("screen",mc.screen==null?null:mc.screen.getClass().getName());
        out.addProperty("pause_on_lost_focus",mc.options.pauseOnLostFocus);
        if(mc.player!=null){
            out.add("position",LabBridge.GSON.toJsonTree(new double[]{mc.player.getX(),mc.player.getY(),mc.player.getZ()}));
            out.addProperty("dimension",mc.player.level().dimension().identifier().toString());
        }
        return out;
    }
    // A creative world with cheats on, made the way the world list's debug button makes one, so the game opens it without any screen in between.
    static JsonObject newWorld(String name)throws Exception {
        Minecraft mc=Minecraft.getInstance();
        if(mc.level!=null)throw new IllegalStateException("Leave the current world before creating one");
        String folder=FileUtil.findAvailableName(mc.getLevelSource().getBaseDir(),name,"");
        LevelSettings settings=new LevelSettings(name,GameType.CREATIVE,LevelSettings.DifficultySettings.DEFAULT,true,WorldDataConfiguration.DEFAULT);
        mc.options.pauseOnLostFocus=false;
        mc.createWorldOpenFlows().createFreshLevel(folder,settings,WorldOptions.defaultWithRandomSeed(),WorldPresets::createNormalWorldDimensions,mc.screen);
        JsonObject out=new JsonObject();out.addProperty("folder",folder);return out;
    }
    static ServerPlayer player(MinecraftServer server){
        List<ServerPlayer> players=server.getPlayerList().getPlayers();
        if(players.isEmpty())throw new IllegalStateException("No player has joined the world yet");
        return players.getFirst();
    }
    // The command runs as the player, and every message it would print is returned instead of only going to chat.
    static JsonObject command(String command){
        MinecraftServer server=LabSession.server;List<String> messages=new ArrayList<>();
        CommandSource collector=new CommandSource(){
            @Override public void sendSystemMessage(Component message){messages.add(message.getString());}
            @Override public boolean acceptsSuccess(){return true;}
            @Override public boolean acceptsFailure(){return true;}
            @Override public boolean shouldInformAdmins(){return false;}
        };
        server.getCommands().performPrefixedCommand(player(server).createCommandSourceStack().withSource(collector),command);
        JsonObject out=new JsonObject();out.add("messages",LabBridge.GSON.toJsonTree(messages));return out;
    }
    // The player's eyes end up at `from`, looking at the centre of the block at `at`, with no screen open, so Jade can show that block.
    static JsonObject aim(JsonArray from,JsonArray at)throws Exception {
        double fx=from.get(0).getAsDouble(),fy=from.get(1).getAsDouble(),fz=from.get(2).getAsDouble();
        double dx=at.get(0).getAsInt()+0.5-fx,dy=at.get(1).getAsInt()+0.5-fy,dz=at.get(2).getAsInt()+0.5-fz;
        float yaw=(float)Math.toDegrees(Math.atan2(-dx,dz)),pitch=(float)-Math.toDegrees(Math.atan2(dy,Math.sqrt(dx*dx+dz*dz)));
        LabBridge.onServer(()->{ServerPlayer p=player(LabSession.server);return p.teleportTo(p.level(),fx,fy-p.getEyeHeight(),fz,Set.of(),yaw,pitch,false);});
        onClient(()->{Minecraft.getInstance().setScreen(null);return true;});
        JsonObject out=new JsonObject();out.addProperty("yaw",yaw);out.addProperty("pitch",pitch);return out;
    }
    // Oracle Index is optional, so it is reached by reflection. `item` opens the entry for an item id, and `wiki` with an optional `entry` opens a book page.
    static JsonObject guide(JsonObject request)throws Exception {
        Class<?> oracle=Class.forName("rearth.oracle.OracleClient");JsonObject out=new JsonObject();
        Screen parent=Minecraft.getInstance().screen;
        if(request.has("item")){
            Object opened=oracle.getMethod("openEntry",Identifier.class,Screen.class).invoke(null,Identifier.parse(request.get("item").getAsString()),parent);
            out.addProperty("opened",(Boolean)opened);
        }else{
            Identifier entry=request.has("entry")?Identifier.parse(request.get("entry").getAsString()):null;
            oracle.getMethod("openScreen",String.class,Identifier.class,Screen.class).invoke(null,request.get("wiki").getAsString(),entry,parent);
            out.addProperty("opened",true);
        }
        Screen now=Minecraft.getInstance().screen;out.addProperty("screen",now==null?null:now.getClass().getName());
        return out;
    }
    // The capture includes the HUD and any open screen, the same as pressing F2.
    static JsonObject screenshot(String name)throws Exception {
        if(!name.matches("[a-zA-Z0-9_-]{1,64}"))throw new IllegalArgumentException("Screenshot names must be simple file-safe names");
        CompletableFuture<String> done=new CompletableFuture<>();Minecraft mc=Minecraft.getInstance();
        mc.execute(()->Screenshot.grab(mc.gameDirectory,name+".png",mc.getMainRenderTarget(),1,message->done.complete(message.getString())));
        JsonObject out=new JsonObject();out.addProperty("message",done.get(30,TimeUnit.SECONDS));
        out.addProperty("path",mc.gameDirectory.toPath().resolve("screenshots").resolve(name+".png").toString());
        return out;
    }
    static JsonObject chunkLoaded(JsonObject request){
        MinecraftServer server=LabSession.server;JsonArray p=request.getAsJsonArray("position");
        ServerLevel level=request.has("dimension")?server.getLevel(ResourceKey.create(Registries.DIMENSION,Identifier.parse(request.get("dimension").getAsString()))):server.overworld();
        if(level==null)throw new IllegalArgumentException("Unknown dimension");
        JsonObject out=new JsonObject();out.addProperty("loaded",level.isLoaded(new BlockPos(p.get(0).getAsInt(),p.get(1).getAsInt(),p.get(2).getAsInt())));
        return out;
    }
}
