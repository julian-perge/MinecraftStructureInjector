package dev.structurelab;

import com.google.gson.*;
import net.minecraft.core.BlockPos;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.nbt.*;
import net.minecraft.resources.Identifier;
import net.minecraft.server.MinecraftServer;
import net.minecraft.world.level.GameType;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.gamerules.GameRules;
import net.minecraft.world.level.storage.LevelResource;
import java.nio.file.*;
import java.util.*;

/** Server-thread-only world operations. The lab dimension type is the persistent opt-in. */
public final class LabSession {
    public static volatile MinecraftServer server;
    private static final Identifier LAB = Identifier.fromNamespaceAndPath("structurelab", "lab");
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
        try {
            if (Files.exists(ledger)) previousSize = JsonParser.parseString(Files.readString(ledger)).getAsJsonArray().asList().stream().mapToInt(JsonElement::getAsInt).toArray();
        } catch (Exception e) { throw new IllegalStateException("Cannot read lab recovery ledger", e); }
        var rules = value.getGameRules();
        rules.set(GameRules.ADVANCE_TIME, false, value);
        rules.set(GameRules.ADVANCE_WEATHER, false, value);
        rules.set(GameRules.SPAWN_MOBS, false, value);
        rules.set(GameRules.RANDOM_TICK_SPEED, 0, value);
        rules.set(GameRules.COMMAND_BLOCKS_WORK, false, value);
        value.getCommands().performPrefixedCommand(value.createCommandSourceStack(), "time set noon");
        value.getCommands().performPrefixedCommand(value.createCommandSourceStack(), "weather clear");
        value.tickRateManager().setFrozen(true);
    }
    public static void close(MinecraftServer value) { LabPlacement.closed(value); if (server == value) { server = null; previousSize = null; } }
    public static boolean isLab() {
        return server != null && server.overworld().dimensionTypeRegistration().unwrapKey().map(k -> k.identifier().equals(LAB)).orElse(false);
    }
    public static void requireLab() {
        if (!isLab()) throw new IllegalStateException("Open a single-player world created with the Structure Lab preset");
    }
    public static JsonObject status() {
        JsonObject out = new JsonObject();
        out.addProperty("connected", server != null); out.addProperty("lab_world", isLab());
        out.addProperty("minecraft", "26.3"); out.addProperty("max_width", 1024); out.addProperty("max_length", 1024);
        out.addProperty("max_angles", 1024); out.addProperty("max_volume", MAX_VOLUME);
        out.addProperty("max_clear_volume", MAX_VOLUME * 2);
        out.addProperty("max_blocks", MAX_BLOCKS); out.addProperty("placement", "chunk_batched");
        out.addProperty("max_height", server == null ? 380 : Math.min(1024, server.overworld().getMaxY() - ORIGIN.getY() + 1));
        out.add("origin", LabBridge.GSON.toJsonTree(new int[]{0, -60, 0}));
        return out;
    }
    public static JsonObject blocks(String query) {
        JsonObject out = new JsonObject();
        BuiltInRegistries.BLOCK.entrySet().stream().filter(e -> e.getKey().identifier().toString().contains(query)).limit(200).forEach(e -> {
            JsonObject props = new JsonObject();
            e.getValue().getStateDefinition().getProperties().forEach(p -> props.add(p.getName(), LabBridge.GSON.toJsonTree(p.getPossibleValues().stream().map(Object::toString).toList())));
            out.add(e.getKey().identifier().toString(), props);
        });
        return out;
    }
    public static CompoundTag validate(Path input) throws Exception {
        CompoundTag tag = NbtIo.readCompressed(input, NbtAccounter.create(256L * 1024 * 1024));
        ListTag size = tag.getList("size").orElseThrow(() -> new IllegalArgumentException("Missing size"));
        if (size.size()!=3) throw new IllegalArgumentException("size must contain three integers");
        int x=size.getIntOr(0,0), y=size.getIntOr(1,0), z=size.getIntOr(2,0);
        if (x<1 || y<1 || z<1 || x>1024 || z>1024 || y>1024 || (long)x*y*z>MAX_VOLUME) throw new IllegalArgumentException("Structure exceeds reported dimension or volume limits");
        if (server != null && ORIGIN.getY()+y-1>server.overworld().getMaxY()) throw new IllegalArgumentException("Structure exceeds world height");
        if (tag.contains("palettes")) throw new IllegalArgumentException("Multiple palettes are not supported in milestone 1");
        ListTag palette=tag.getList("palette").orElseThrow();
        if (palette.isEmpty()) throw new IllegalArgumentException("Empty palette");
        for (Tag entry:palette) {
            if (!(entry instanceof CompoundTag state)) throw new IllegalArgumentException("Invalid palette entry");
            String name=state.getString("id").orElseThrow(()->new IllegalArgumentException("Palette entries need an id. Minecraft 26.3 renamed Name to id and Properties to properties"));
            Identifier id=Identifier.parse(name);
            if (!BuiltInRegistries.BLOCK.containsKey(id)) throw new IllegalArgumentException("Unknown block: "+name);
            Block block=BuiltInRegistries.BLOCK.getValue(id);
            CompoundTag properties=state.getCompoundOrEmpty("properties");
            for (String key:properties.keySet()) {
                var property=block.getStateDefinition().getProperty(key);
                if (property==null || property.getValue(properties.getString(key).orElseThrow()).isEmpty()) throw new IllegalArgumentException("Invalid property: "+name+"."+key);
            }
        }
        Set<Long> positions=new HashSet<>();
        if(tag.getListOrEmpty("blocks").size()>MAX_BLOCKS)throw new IllegalArgumentException("At most "+MAX_BLOCKS+" explicit block records");
        for (Tag entry:tag.getList("blocks").orElseThrow()) {
            CompoundTag b=(CompoundTag)entry;
            int state=b.getIntOr("state",-1);
            if (state<0 || state>=palette.size()) throw new IllegalArgumentException("Invalid palette index");
            ListTag p=b.getListOrEmpty("pos");
            if (p.size()!=3) throw new IllegalArgumentException("Invalid block position");
            int px=p.getIntOr(0,-1),py=p.getIntOr(1,-1),pz=p.getIntOr(2,-1);
            if (px<0 || py<0 || pz<0 || px>=x || py>=y || pz>=z) throw new IllegalArgumentException("Block outside bounds");
            if (!positions.add(BlockPos.asLong(px,py,pz))) throw new IllegalArgumentException("Duplicate block position");
        }
        if (!tag.getListOrEmpty("entities").isEmpty()) throw new IllegalArgumentException("Entity templates will be supported after milestone 1; block entities are supported");
        return tag;
    }
    public static JsonArray extractPads(CompoundTag tag) {
        ListTag palette=tag.getListOrEmpty("palette");
        Set<Integer> pads=new HashSet<>();
        for(int i=0;i<palette.size();i++) if(palette.getCompoundOrEmpty(i).getStringOr("id","").equals("structurelab:view_pad")) pads.add(i);
        JsonArray result=new JsonArray();
        CompoundTag air=new CompoundTag(); air.putString("id","minecraft:air");
        for(Tag entry:tag.getListOrEmpty("blocks")) {
            CompoundTag b=(CompoundTag)entry;
            if(!pads.contains(b.getIntOr("state",-1))) continue;
            CompoundTag view=b.getCompoundOrEmpty("nbt").getCompoundOrEmpty("view");
            String metadata=view.getStringOr("json", "");
            if(metadata.isBlank()) throw new IllegalArgumentException("View pad needs nbt.view.json metadata");
            JsonObject v=JsonParser.parseString(metadata).getAsJsonObject();
            if(!v.has("position")) {
                ListTag p=b.getListOrEmpty("pos");
                v.add("position",LabBridge.GSON.toJsonTree(new double[]{p.getIntOr(0,0)+0.5,p.getIntOr(1,0),p.getIntOr(2,0)+0.5}));
            }
            result.add(v);
            CompoundTag replacement=view.getCompound("replacement").orElse(air);
            palette.add(replacement.copy()); b.putInt("state",palette.size()-1); b.remove("nbt");
        }
        // Compact the palette so no mod identifiers survive export, even as unused entries.
        ListTag compact=new ListTag(); Map<Integer,Integer> remap=new HashMap<>();
        for(Tag entry:tag.getListOrEmpty("blocks")) {
            CompoundTag b=(CompoundTag)entry; int old=b.getIntOr("state",-1);
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
        player.teleportTo(server.overworld(),ORIGIN.getX()+p.get(0).getAsDouble(),ORIGIN.getY()+p.get(1).getAsDouble()+eye-player.getEyeHeight(),ORIGIN.getZ()+p.get(2).getAsDouble(),Set.of(),view.get("yaw").getAsFloat(),view.get("pitch").getAsFloat(),true);
    }
    public static JsonObject inspect(JsonArray positions) {
        requireLab(); JsonObject out=new JsonObject();
        for(JsonElement e:positions) {JsonArray p=e.getAsJsonArray(); BlockPos b=ORIGIN.offset(p.get(0).getAsInt(),p.get(1).getAsInt(),p.get(2).getAsInt()); out.addProperty(p.toString(),server.overworld().getBlockState(b).toString());}
        return out;
    }
}
