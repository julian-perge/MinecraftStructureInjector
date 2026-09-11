package dev.structurelab;

import com.google.gson.*;
import net.minecraft.core.BlockPos;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.nbt.*;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.MinecraftServer;
import net.minecraft.world.level.GameType;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.GameRules;
import net.minecraft.world.level.storage.LevelResource;
import java.nio.file.*;
import java.util.*;

/** Server-thread-only world operations. The lab dimension type is the persistent opt-in. */
public final class LabSession {
    public static volatile MinecraftServer server;
    private static final ResourceLocation LAB = ResourceLocation.fromNamespaceAndPath("structurelab", "lab");
    public static final BlockPos ORIGIN = new BlockPos(0, -60, 0);
    public static final long MAX_VOLUME = 16_000_000L;
    public static final int MAX_BLOCKS = 1_000_000;
    static int[] previousSize;
    static Path ledger;
    public static void open(MinecraftServer value) {
        server = value;
        previousSize = null;
        ledger = value.getWorldPath(LevelResource.ROOT).resolve("structurelab-placement.json");
        if (!isLab()) return;
        if (Boolean.getBoolean("structurelab.hiddenClient") && value.getWorldData() instanceof net.minecraft.world.level.storage.PrimaryLevelData data)
            data.withConfirmedWarning(true);
        try {
            if (Files.exists(ledger)) previousSize = JsonParser.parseString(Files.readString(ledger)).getAsJsonArray().asList().stream().mapToInt(JsonElement::getAsInt).toArray();
        } catch (Exception e) { throw new IllegalStateException("Cannot read lab recovery ledger", e); }
        var rules = value.getGameRules();
        rules.getRule(GameRules.RULE_DAYLIGHT).set(false, value);
        rules.getRule(GameRules.RULE_WEATHER_CYCLE).set(false, value);
        rules.getRule(GameRules.RULE_DOMOBSPAWNING).set(false, value);
        rules.getRule(GameRules.RULE_RANDOMTICKING).set(0, value);
        // Command blocks remain disabled in the lab server configuration.
        value.getCommands().performPrefixedCommand(value.createCommandSourceStack(), "time set noon");
        value.getCommands().performPrefixedCommand(value.createCommandSourceStack(), "weather clear");
        value.tickRateManager().setFrozen(true);
    }
    public static void close(MinecraftServer value) { LabPlacement.closed(value); if (server == value) { server = null; previousSize = null; } }
    public static boolean isLab() {
        return server != null && server.overworld().dimensionTypeRegistration().unwrapKey().map(k -> k.location().equals(LAB)).orElse(false);
    }
    public static void requireLab() {
        if (!isLab()) throw new IllegalStateException("Open a single-player world created with the Structure Lab preset");
    }
    public static JsonObject status() {
        JsonObject out = new JsonObject();
        out.addProperty("connected", server != null); out.addProperty("lab_world", isLab());
        out.addProperty("minecraft", "1.21.1"); out.addProperty("max_width", 1024); out.addProperty("max_length", 1024);
        out.addProperty("max_angles", 1024); out.addProperty("max_volume", MAX_VOLUME);
        out.addProperty("max_clear_volume", MAX_VOLUME * 2);
        out.addProperty("max_blocks", MAX_BLOCKS); out.addProperty("placement", "chunk_batched");
        out.addProperty("max_height", server == null ? 380 : Math.min(1024, server.overworld().getMaxBuildHeight() - 1 - ORIGIN.getY() + 1));
        out.add("origin", LabBridge.GSON.toJsonTree(new int[]{0, -60, 0}));
        return out;
    }
    public static JsonObject blocks(String query) {
        JsonObject out = new JsonObject();
        BuiltInRegistries.BLOCK.entrySet().stream().filter(e -> e.getKey().location().toString().contains(query)).limit(200).forEach(e -> {
            JsonObject props = new JsonObject();
            e.getValue().getStateDefinition().getProperties().forEach(p -> props.add(p.getName(), LabBridge.GSON.toJsonTree(p.getPossibleValues().stream().map(Object::toString).toList())));
            out.add(e.getKey().location().toString(), props);
        });
        return out;
    }
    public static CompoundTag validate(Path input) throws Exception {
        CompoundTag tag = NbtIo.readCompressed(input, NbtAccounter.create(256L * 1024 * 1024));
        if (!tag.contains("size", Tag.TAG_LIST) || !tag.contains("palette", Tag.TAG_LIST) || !tag.contains("blocks", Tag.TAG_LIST)) throw new IllegalArgumentException("Missing required structure lists");
        ListTag size = tag.getList("size", Tag.TAG_INT);
        if (size.size()!=3) throw new IllegalArgumentException("size must contain three integers");
        int x=size.getInt(0), y=size.getInt(1), z=size.getInt(2);
        if (x<1 || y<1 || z<1 || x>1024 || z>1024 || y>1024 || (long)x*y*z>MAX_VOLUME) throw new IllegalArgumentException("Structure exceeds reported dimension or volume limits");
        if (server != null && ORIGIN.getY()+y-1>server.overworld().getMaxBuildHeight() - 1) throw new IllegalArgumentException("Structure exceeds world height");
        if (tag.contains("palettes")) throw new IllegalArgumentException("Multiple palettes are not supported in milestone 1");
        ListTag palette=tag.getList("palette", Tag.TAG_COMPOUND);
        if (palette.isEmpty()) throw new IllegalArgumentException("Empty palette");
        for (Tag entry:palette) {
            if (!(entry instanceof CompoundTag state)) throw new IllegalArgumentException("Invalid palette entry");
            String name=state.getString("Name");
            ResourceLocation id=ResourceLocation.parse(name);
            if (!BuiltInRegistries.BLOCK.containsKey(id)) throw new IllegalArgumentException("Unknown block: "+name);
            Block block=BuiltInRegistries.BLOCK.get(id);
            CompoundTag properties=state.getCompound("Properties");
            for (String key:properties.getAllKeys()) {
                var property=block.getStateDefinition().getProperty(key);
                if (property==null || property.getValue(properties.getString(key)).isEmpty()) throw new IllegalArgumentException("Invalid property: "+name+"."+key);
            }
        }
        Set<Long> positions=new HashSet<>();
        if(tag.getList("blocks", Tag.TAG_COMPOUND).size()>MAX_BLOCKS)throw new IllegalArgumentException("At most "+MAX_BLOCKS+" explicit block records");
        for (Tag entry:tag.getList("blocks", Tag.TAG_COMPOUND)) {
            CompoundTag b=(CompoundTag)entry;
            if (!b.contains("state", Tag.TAG_INT)) throw new IllegalArgumentException("Missing palette index");
            int state=b.getInt("state");
            if (state<0 || state>=palette.size()) throw new IllegalArgumentException("Invalid palette index");
            ListTag p=b.getList("pos", Tag.TAG_INT);
            if (p.size()!=3) throw new IllegalArgumentException("Invalid block position");
            int px=p.getInt(0),py=p.getInt(1),pz=p.getInt(2);
            if (px<0 || py<0 || pz<0 || px>=x || py>=y || pz>=z) throw new IllegalArgumentException("Block outside bounds");
            if (!positions.add(BlockPos.asLong(px,py,pz))) throw new IllegalArgumentException("Duplicate block position");
        }
        if (!tag.getList("entities", Tag.TAG_COMPOUND).isEmpty()) throw new IllegalArgumentException("Entity templates will be supported after milestone 1; block entities are supported");
        return tag;
    }
    public static JsonArray extractPads(CompoundTag tag) {
        ListTag palette=tag.getList("palette", Tag.TAG_COMPOUND);
        Set<Integer> pads=new HashSet<>();
        for(int i=0;i<palette.size();i++) if(palette.getCompound(i).getString("Name").equals("structurelab:view_pad")) pads.add(i);
        JsonArray result=new JsonArray();
        CompoundTag air=new CompoundTag(); air.putString("Name","minecraft:air");
        for(Tag entry:tag.getList("blocks", Tag.TAG_COMPOUND)) {
            CompoundTag b=(CompoundTag)entry;
            if(!pads.contains(b.getInt("state"))) continue;
            CompoundTag view=b.getCompound("nbt").getCompound("view");
            String metadata=view.getString("json");
            if(metadata.isBlank()) throw new IllegalArgumentException("View pad needs nbt.view.json metadata");
            JsonObject v=JsonParser.parseString(metadata).getAsJsonObject();
            if(!v.has("position")) {
                ListTag p=b.getList("pos", Tag.TAG_INT);
                v.add("position",LabBridge.GSON.toJsonTree(new double[]{p.getInt(0)+0.5,p.getInt(1),p.getInt(2)+0.5}));
            }
            result.add(v);
            CompoundTag replacement=(view.contains("replacement", Tag.TAG_COMPOUND) ? view.getCompound("replacement") : air);
            palette.add(replacement.copy()); b.putInt("state",palette.size()-1); b.remove("nbt");
        }
        // Compact the palette so no mod identifiers survive export, even as unused entries.
        ListTag compact=new ListTag(); Map<Integer,Integer> remap=new HashMap<>();
        for(Tag entry:tag.getList("blocks", Tag.TAG_COMPOUND)) {
            CompoundTag b=(CompoundTag)entry; int old=b.getInt("state");
            int mapped=remap.computeIfAbsent(old,k->{compact.add(palette.get(k).copy());return compact.size()-1;});
            b.putInt("state",mapped);
        }
        tag.put("palette",compact);
        return result;
    }
    public static void move(JsonObject view) {
        requireLab();
        JsonArray p=view.getAsJsonArray("position");
        var player=server.getPlayerList().getPlayers().stream().findFirst().orElseThrow(()->new IllegalStateException("Player not connected"));
        player.setGameMode(GameType.SPECTATOR);
        double eye=view.has("eye_height")?view.get("eye_height").getAsDouble():1.62;
        player.teleportTo(server.overworld(),ORIGIN.getX()+p.get(0).getAsDouble(),ORIGIN.getY()+p.get(1).getAsDouble()+eye-player.getEyeHeight(),ORIGIN.getZ()+p.get(2).getAsDouble(),Set.of(),view.get("yaw").getAsFloat(),view.get("pitch").getAsFloat());
    }
    public static JsonObject inspect(JsonArray positions) {
        requireLab(); JsonObject out=new JsonObject();
        for(JsonElement e:positions) {JsonArray p=e.getAsJsonArray(); BlockPos b=ORIGIN.offset(p.get(0).getAsInt(),p.get(1).getAsInt(),p.get(2).getAsInt()); out.addProperty(p.toString(),server.overworld().getBlockState(b).toString());}
        return out;
    }
    /** Static native collision checks; this does not claim to simulate player movement. */
    public static JsonObject walkRoute(JsonArray positions) {
        requireLab();
        if(!Boolean.getBoolean("structurelab.hiddenClient"))throw new IllegalStateException("Movement tests require an isolated hidden client");
        if(positions.size()<2||positions.size()>512)throw new IllegalArgumentException("Route needs 2 to 512 points");
        var points=new ArrayList<net.minecraft.world.phys.Vec3>();
        for(var element:positions){
            var p=element.getAsJsonArray();if(p.size()!=3)throw new IllegalArgumentException("Expected XYZ");
            double x=p.get(0).getAsDouble(),y=p.get(1).getAsDouble(),z=p.get(2).getAsDouble();
            if(!Double.isFinite(x)||!Double.isFinite(y)||!Double.isFinite(z)||x<0||x>1024||y<0||y>380||z<0||z>1024)throw new IllegalArgumentException("Route outside lab limits");
            var point=new net.minecraft.world.phys.Vec3(x,y+ORIGIN.getY(),z);
            if(!points.isEmpty()&&point.distanceTo(points.get(points.size()-1))>4)throw new IllegalArgumentException("Route points must be at most four metres apart");
            points.add(point);
        }
        var player=server.getPlayerList().getPlayers().stream().findFirst().orElseThrow();
        var saved=player.position();var velocity=player.getDeltaMovement();var mode=player.gameMode.getGameModeForPlayer();
        float yaw=player.getYRot(),pitch=player.getXRot(),fall=player.fallDistance;
        boolean physics=player.noPhysics,flying=player.getAbilities().flying,invulnerable=player.getAbilities().invulnerable;
        JsonObject result=new JsonObject();JsonArray trace=new JsonArray();int reached=0;
        try {
            player.setGameMode(GameType.ADVENTURE);player.noPhysics=false;player.getAbilities().flying=false;player.getAbilities().invulnerable=true;
            var start=points.getFirst();player.setPos(start.x,start.y,start.z);player.setOnGround(true);
            for(int i=0;i<points.size();i++){
                var target=points.get(i);int steps=0;
                while(steps++<60){
                    double dx=target.x-player.getX(),dz=target.z-player.getZ(),length=Math.hypot(dx,dz);
                    if(length<0.04&&Math.abs(target.y-player.getY())<0.65){reached++;break;}
                    double scale=length>0?Math.min(0.12,length)/length:0;
                    player.move(net.minecraft.world.entity.MoverType.SELF,new net.minecraft.world.phys.Vec3(dx*scale,-0.08,dz*scale));
                }
                JsonObject sample=new JsonObject();sample.addProperty("point",i);sample.addProperty("reached",reached==i+1);
                sample.add("actual",LabBridge.GSON.toJsonTree(new double[]{player.getX(),player.getY()-ORIGIN.getY(),player.getZ()}));trace.add(sample);
                if(reached!=i+1)break;
            }
        } finally {
            player.setGameMode(mode);player.noPhysics=physics;player.getAbilities().flying=flying;player.getAbilities().invulnerable=invulnerable;
            player.teleportTo(saved.x,saved.y,saved.z);player.setYRot(yaw);player.setXRot(pitch);player.setDeltaMovement(velocity);player.fallDistance=fall;
        }
        result.addProperty("method","native_server_player_move_no_jump");result.addProperty("passed",reached==points.size());
        result.addProperty("reached",reached);result.addProperty("total",points.size());result.add("trace",trace);return result;
    }
    public static JsonObject clearance(JsonArray positions) {
        requireLab();
        if (positions.size()>10000) throw new IllegalArgumentException("At most 10000 clearance samples");
        JsonArray samples=new JsonArray(); int blocked=0,unsupported=0;
        var level=server.overworld();
        for (JsonElement element:positions) {
            JsonArray p=element.getAsJsonArray();
            if(p.size()!=3)throw new IllegalArgumentException("A sample needs three coordinates");
            double x=p.get(0).getAsDouble()+ORIGIN.getX(),y=p.get(1).getAsDouble()+ORIGIN.getY(),z=p.get(2).getAsDouble()+ORIGIN.getZ();
            if(!Double.isFinite(x)||!Double.isFinite(y)||!Double.isFinite(z))throw new IllegalArgumentException("Coordinates must be finite");
            var body=new net.minecraft.world.phys.AABB(x-0.3,y+0.001,z-0.3,x+0.3,y+1.8,z+0.3);
            boolean clear=level.noCollision(body);
            boolean supported=!level.noCollision(new net.minecraft.world.phys.AABB(x-0.29,y-0.08,z-0.29,x+0.29,y,z+0.29));
            JsonObject sample=new JsonObject();sample.add("position",p.deepCopy());sample.addProperty("clear",clear);sample.addProperty("supported",supported);
            samples.add(sample);if(!clear)blocked++;if(!supported)unsupported++;
        }
        JsonObject result=new JsonObject();result.addProperty("method","native_static_player_aabb");result.addProperty("blocked",blocked);result.addProperty("unsupported",unsupported);result.add("samples",samples);return result;
    }
}
