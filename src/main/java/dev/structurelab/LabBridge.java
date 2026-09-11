package dev.structurelab;

import com.google.gson.*;
import com.sun.net.httpserver.HttpServer;
import net.minecraft.client.Minecraft;
import net.minecraft.nbt.*;
import java.net.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.security.MessageDigest;
import java.util.*;
import java.util.concurrent.*;
import java.util.concurrent.atomic.AtomicBoolean;

/** Local transport. No remote binding, arbitrary command execution, or world creation API. */
public final class LabBridge {
    public static final Gson GSON=new GsonBuilder().setPrettyPrinting().create();
    public static Path root;
    public static volatile Job job;
    private static final AtomicBoolean busy=new AtomicBoolean();
    private static final ExecutorService IO=Executors.newSingleThreadExecutor(r->{Thread t=new Thread(r,"Structure Lab jobs");t.setDaemon(true);return t;});
    public static final class Job {
        public final String revision=UUID.randomUUID().toString();
        public volatile String state="validating",error="";
        public volatile int captured=0;
        public volatile int processed=0,workTotal=0;
        public Boolean pauseBefore;
        public String sha256;
        public final Path directory;
        public final net.minecraft.server.MinecraftServer world=LabSession.server;
        public JsonArray views=new JsonArray();
        public final List<JsonObject> captures=new CopyOnWriteArrayList<>();
        public volatile boolean cancelled;
        public Job() throws Exception { directory=root.resolve("revisions").resolve(revision);Files.createDirectories(directory); }
        public JsonObject json() {
            JsonObject j=new JsonObject();j.addProperty("revision",revision);j.addProperty("state",state);j.addProperty("error",error);
            j.addProperty("captured",captured);j.addProperty("total",views.size());j.addProperty("sha256",sha256);
            j.addProperty("processed",processed);j.addProperty("work_total",workTotal);
            j.add("views",views);j.add("captures",GSON.toJsonTree(captures));j.addProperty("directory",directory.toString());
            return j;
        }
    }
    public static void start() {
        try {
            root=Minecraft.getInstance().gameDirectory.toPath().toAbsolutePath().normalize().resolve("structurelab"); Files.createDirectories(root);
            String token=UUID.randomUUID().toString()+UUID.randomUUID();
            HttpServer http=HttpServer.create(new InetSocketAddress(InetAddress.getByName("127.0.0.1"),0),0);
            http.setExecutor(Executors.newFixedThreadPool(2,r->{Thread t=new Thread(r,"Structure Lab HTTP");t.setDaemon(true);return t;}));
            http.createContext("/rpc",exchange->{
                int status=200; JsonObject response;
                try {
                    if(!("Bearer "+token).equals(exchange.getRequestHeaders().getFirst("Authorization"))) throw new IllegalArgumentException("Unauthorized");
                    if(!exchange.getRequestMethod().equals("POST")) throw new IllegalArgumentException("POST required");
                    byte[] body=exchange.getRequestBody().readNBytes(1024*1024+1);
                    if(body.length>1024*1024) throw new IllegalArgumentException("Request too large");
                    response=rpc(JsonParser.parseString(new String(body,StandardCharsets.UTF_8)).getAsJsonObject());
                }catch(Exception e){status=400;response=new JsonObject();response.addProperty("error",message(e));}
                byte[] data=GSON.toJson(response).getBytes(StandardCharsets.UTF_8);
                exchange.getResponseHeaders().set("Content-Type","application/json");exchange.sendResponseHeaders(status,data.length);
                try(var out=exchange.getResponseBody()){out.write(data);}
            });
            http.start();
            JsonObject connection=new JsonObject();connection.addProperty("url","http://127.0.0.1:"+http.getAddress().getPort()+"/rpc");connection.addProperty("token",token);
            Files.writeString(root.resolve("connection.json"),GSON.toJson(connection));
        }catch(Exception e){throw new IllegalStateException("Cannot start Structure Lab bridge",e);}
    }
    static String message(Throwable e){while(e.getCause()!=null)e=e.getCause();return e.getClass().getSimpleName()+": "+e.getMessage();}
    static <T>T onServer(Callable<T> fn)throws Exception {
        var server=LabSession.server;if(server==null)throw new IllegalStateException("No single-player world is open");
        return server.submit(()->{try{return fn.call();}catch(Exception e){throw new CompletionException(e);}}).get(90,TimeUnit.SECONDS);
    }
    static <T>T onServer(Job j,Callable<T> fn)throws Exception {
        return onServer(()->{if(j.world!=LabSession.server)throw new IllegalStateException("Lab world changed during job");return fn.call();});
    }
    static JsonObject rpc(JsonObject request)throws Exception {
        String op=request.get("op").getAsString();
        switch(op){
            case "shutdown": {
                if(!Boolean.getBoolean("structurelab.hiddenClient"))throw new IllegalStateException("Shutdown is available only in an isolated hidden client");
                Minecraft.getInstance().execute(()->Minecraft.getInstance().stop());return new JsonObject();
            }
            case "status": {JsonObject result=LabSession.status();if(job!=null)result.add("job",job.json());return result;}
            case "blocks": return onServer(()->LabSession.blocks(request.has("query")?request.get("query").getAsString():""));
            case "inspect": return onServer(()->LabSession.inspect(request.getAsJsonArray("positions")));
            case "clearance": return onServer(()->LabSession.clearance(request.getAsJsonArray("positions")));
            case "walk_route": {
                if(job!=null&&!job.state.equals("complete"))throw new IllegalStateException("Finish capture before testing movement");
                return onServer(()->LabSession.walkRoute(request.getAsJsonArray("positions")));
            }
            case "job": {if(job==null)throw new IllegalStateException("No job submitted");return job.json();}
            case "cancel": {if(job!=null)job.cancelled=true;return job==null?new JsonObject():job.json();}
            case "validate": {
                CompoundTag tag=onServer(()->LabSession.validate(Path.of(request.get("path").getAsString())));
                JsonObject out=new JsonObject();out.addProperty("valid",true);out.addProperty("blocks",tag.getList("blocks", Tag.TAG_COMPOUND).size());return out;
            }
            case "submit": {
                onServer(()->{LabSession.requireLab();return true;});
                if(!busy.compareAndSet(false,true))throw new IllegalStateException("A job is active; wait or cancel it");
                Job next;
                try{next=new Job();}catch(Exception e){busy.set(false);throw e;}
                job=next;
                IO.execute(()->runSubmission(next,request));return next.json();
            }
            case "recapture": {
                Job previous=job;
                if(previous==null||!previous.state.equals("complete"))throw new IllegalStateException("Complete a revision before recapturing");
                if(!previous.revision.equals(request.get("revision").getAsString()))throw new IllegalArgumentException("Stale revision");
                onServer(previous,()->{LabSession.requireLab();return true;});
                if(!busy.compareAndSet(false,true))throw new IllegalStateException("A job is active");
                try{
                    Job next=new Job();next.sha256=previous.sha256;
                    next.views=request.has("views")?expandViews(request.getAsJsonArray("views"),new CompoundTag()):previous.views.deepCopy();
                    Files.copy(previous.directory.resolve("structure.nbt"),next.directory.resolve("structure.nbt"));
                    next.state="capturing";job=next;persist(next);Minecraft.getInstance().execute(()->LabCapture.begin(next));return next.json();
                }catch(Exception e){busy.set(false);throw e;}
            }
            default:throw new IllegalArgumentException("Unknown operation: "+op);
        }
    }
    static void runSubmission(Job next,JsonObject request){
        try{
            Path source=Path.of(request.get("path").getAsString());
            if(Files.size(source)>64L*1024*1024)throw new IllegalArgumentException("Compressed NBT exceeds 64 MiB limit");
            Path input=next.directory.resolve("input.nbt");Files.copy(source,input);
            next.sha256=HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(Files.readAllBytes(input)));
            CompoundTag tag=onServer(next,()->LabSession.validate(input));
            JsonArray pads=LabSession.extractPads(tag);
            JsonArray defined=request.has("views")?request.getAsJsonArray("views").deepCopy():new JsonArray();
            for(JsonElement pad:pads)defined.add(pad);
            next.views=expandViews(defined,tag);
            Path clean=next.directory.resolve("structure.nbt");NbtIo.writeCompressed(tag,clean);
            onServer(next,()->LabSession.validate(clean)); // includes replacement block validation
            if(next.cancelled)throw new CancellationException();
            next.state="placing";persist(next);
            CompletableFuture<Void> clientReady=new CompletableFuture<>();
            Minecraft.getInstance().execute(()->{next.pauseBefore=Minecraft.getInstance().options.pauseOnLostFocus;Minecraft.getInstance().options.pauseOnLostFocus=false;Minecraft.getInstance().setScreen(null);clientReady.complete(null);});
            clientReady.get(30,TimeUnit.SECONDS);
            onServer(next,()->LabPlacement.begin(tag,next)).get(300,TimeUnit.SECONDS);
            if(next.cancelled)throw new CancellationException();
            next.state="capturing";persist(next);
            Minecraft.getInstance().execute(()->LabCapture.begin(next));
        }catch(Exception e){fail(next,e);}
    }
    static JsonArray expandViews(JsonArray pads,CompoundTag tag){
        if(pads.isEmpty()){
            JsonObject v=new JsonObject();v.addProperty("id","spawn");v.addProperty("label","Generated exterior view");v.addProperty("spawn",true);
            v.add("position",GSON.toJsonTree(new double[]{-8,7,-8}));v.addProperty("yaw",-45);v.addProperty("pitch",25);pads.add(v);
        }
        List<JsonObject> views=new ArrayList<>();Set<String> ids=new HashSet<>();
        for(JsonElement entry:pads){
            JsonObject pad=entry.getAsJsonObject();String id=pad.get("id").getAsString();
            if(!id.matches("[a-zA-Z0-9_-]{1,64}")||!ids.add(id))throw new IllegalArgumentException("View IDs must be unique, simple file-safe names");
            JsonArray angles=pad.has("angles")?pad.getAsJsonArray("angles"):new JsonArray();
            if(angles.isEmpty()){JsonObject a=new JsonObject();a.addProperty("id","default");a.add("yaw",pad.get("yaw"));a.add("pitch",pad.get("pitch"));angles.add(a);}
            Set<String> angleIds=new HashSet<>();
            for(JsonElement a:angles){
                JsonObject angle=a.getAsJsonObject(),v=pad.deepCopy();v.remove("angles");String aid=angle.get("id").getAsString();
                if(!aid.matches("[a-zA-Z0-9_-]{1,64}")||!angleIds.add(aid))throw new IllegalArgumentException("Angle IDs must be unique within a pad");
                v.addProperty("angle",aid);v.add("yaw",angle.get("yaw"));v.add("pitch",angle.get("pitch"));
                if(angle.has("fov"))v.add("fov",angle.get("fov"));
                if(!v.has("fov"))v.addProperty("fov",70);
                if(!v.has("eye_height"))v.addProperty("eye_height",1.62);
                if(v.has("render_distance")){
                    double distance=v.get("render_distance").getAsDouble();
                    if(!Double.isFinite(distance)||distance!=Math.rint(distance)||distance<4||distance>24)throw new IllegalArgumentException("Render distance must be an integer between 4 and 24 chunks");
                }
                double eye=v.get("eye_height").getAsDouble();
                if(!Double.isFinite(eye)||eye<0||eye>4)throw new IllegalArgumentException("Eye height must be between 0 and 4");
                JsonArray p=v.getAsJsonArray("position");if(p==null||p.size()!=3)throw new IllegalArgumentException("View needs a 3D position");
                for(JsonElement n:p)if(!Double.isFinite(n.getAsDouble())||Math.abs(n.getAsDouble())>2048)throw new IllegalArgumentException("Invalid view coordinates");
                float yaw=v.get("yaw").getAsFloat(),pitch=v.get("pitch").getAsFloat();int fov=v.get("fov").getAsInt();
                if(!Float.isFinite(yaw)||!Float.isFinite(pitch)||pitch < -90||pitch>90||fov<30||fov>110)throw new IllegalArgumentException("Invalid camera angles or FOV");
                views.add(v);
            }
        }
        if(views.size()>1024)throw new IllegalArgumentException("At most 1024 captured angles are supported");
        views.sort(Comparator.comparing(v->!(v.has("spawn")&&v.get("spawn").getAsBoolean())));
        JsonArray out=new JsonArray();views.forEach(out::add);return out;
    }
    public static void persist(Job j)throws Exception {
        Path temp=j.directory.resolve("manifest.tmp");Files.writeString(temp,GSON.toJson(j.json()));
        Files.move(temp,j.directory.resolve("manifest.json"),StandardCopyOption.REPLACE_EXISTING);
    }
    public static void fail(Job j,Throwable e){
        j.state=j.cancelled?"cancelled":"failed";j.error=message(e);
        j.cancelled=true; // Stop queued chunk work after an I/O or placement timeout.
        try{persist(j);}catch(Exception ignored){}busy.set(false);
        if(j.pauseBefore!=null)Minecraft.getInstance().execute(()->Minecraft.getInstance().options.pauseOnLostFocus=j.pauseBefore);
    }
    public static void complete(Job j){
        IO.execute(()->{
            try{
                j.state="complete";persist(j);
                Path latest=root.resolve("latest.json");String old=null;
                if(Files.exists(latest))old=JsonParser.parseString(Files.readString(latest)).getAsJsonObject().get("revision").getAsString();
                Files.writeString(latest,GSON.toJson(j.json()));
                if(old!=null&&!old.equals(j.revision)){
                    Path oldDir=root.resolve("revisions").resolve(old).normalize();
                    if(old.matches("[a-f0-9-]{36}")&&oldDir.getParent().equals(root.resolve("revisions"))&&Files.isDirectory(oldDir)){
                        try(var paths=Files.walk(oldDir)){for(Path p:paths.sorted(Comparator.reverseOrder()).toList())Files.delete(p);}
                    }
                }
                busy.set(false);
            }catch(Exception e){fail(j,e);}
        });
    }
}
