package dev.structurelab;

import com.mojang.logging.LogUtils;
import net.minecraft.client.Minecraft;
import net.minecraft.client.Screenshot;
import net.minecraft.client.gui.screens.TitleScreen;
import net.neoforged.api.distmarker.Dist;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.client.event.ClientTickEvent;
import net.neoforged.neoforge.client.event.RenderFrameEvent;
import org.lwjgl.glfw.GLFW;
import java.io.IOException;
import java.util.HashSet;

@EventBusSubscriber(modid = "structurelab", value = Dist.CLIENT)
public final class HiddenClientScenario {
    private static int ticks, readyTicks;
    private static int disconnectedTicks;
    private static boolean finished, worldStarted, reportedReady;
    @SubscribeEvent public static void tick(ClientTickEvent.Post event) {
        if (!Boolean.getBoolean("structurelab.hiddenClient") || finished) return;
        var minecraft = Minecraft.getInstance();
        disconnectedTicks=minecraft.screen instanceof net.minecraft.client.gui.screens.DisconnectedScreen?disconnectedTicks+1:0;
        if(disconnectedTicks>40)throw new IllegalStateException("Hidden test client remained disconnected; see the connection error in its log");
        ticks++;
        String selected=System.getProperty("structurelab.scenario", "");
        int limit=selected.equals("planetary")||selected.equals("benchmark")?200000:selected.equals("streamed_reconnect")||selected.equals("streamed_traversal")?24000:selected.equals("streamed_patch")?18000:4800;
        if (!selected.equals("lab") && ticks > limit) throw new IllegalStateException("Hidden client scenario timed out after "+limit+" ticks");
        if (minecraft.screen instanceof TitleScreen && minecraft.getOverlay() == null) readyTicks++;
        if (selected.equals("lab") && readyTicks >= 20 && !worldStarted) {
            worldStarted = true;
            if (java.nio.file.Files.exists(minecraft.gameDirectory.toPath().resolve("saves/structurelab/level.dat"))) {
                minecraft.createWorldOpenFlows().openWorld("structurelab", () -> { throw new IllegalStateException("Could not reopen hidden lab world"); });
                return;
            }
            var settings = new net.minecraft.world.level.LevelSettings("Structure Lab", net.minecraft.world.level.GameType.CREATIVE, false,
                net.minecraft.world.Difficulty.PEACEFUL, true, new net.minecraft.world.level.GameRules(), net.minecraft.world.level.WorldDataConfiguration.DEFAULT);
            minecraft.createWorldOpenFlows().createFreshLevel("structurelab", settings,
                new net.minecraft.world.level.levelgen.WorldOptions(0L, false, false),
                access -> access.registryOrThrow(net.minecraft.core.registries.Registries.WORLD_PRESET)
                    .get(net.minecraft.resources.ResourceLocation.fromNamespaceAndPath("structurelab", "lab")).createWorldDimensions(),
                new TitleScreen());
        }
    }
    @SubscribeEvent public static void frame(RenderFrameEvent.Post event) {
        if (!Boolean.getBoolean("structurelab.hiddenClient") || finished) return;
        var minecraft = Minecraft.getInstance();
        long window = minecraft.getWindow().getWindow();
        if (GLFW.glfwGetWindowAttrib(window, GLFW.GLFW_VISIBLE) != GLFW.GLFW_FALSE
            || GLFW.glfwGetWindowAttrib(window, GLFW.GLFW_FOCUSED) != GLFW.GLFW_FALSE
            || GLFW.glfwGetInputMode(window, GLFW.GLFW_CURSOR) != GLFW.GLFW_CURSOR_NORMAL)
            throw new IllegalStateException("Hidden client visibility/focus/cursor contract violated");
        String scenario = System.getProperty("structurelab.scenario", "");
        if (scenario.equals("smoke")) { if (readyTicks < 40) return; }
        else {
            if (scenario.equals("lab") && minecraft.level != null && minecraft.player != null && !reportedReady) {
                if(minecraft.getMainRenderTarget().width!=1920 || minecraft.getMainRenderTarget().height!=1080)
                    throw new IllegalStateException("Hidden lab must render at 1920x1080");
                LogUtils.getLogger().info("HIDDEN_LAB_READY visible=false focused=false cursor=normal framebuffer=1920x1080");
                reportedReady=true;
            }
            return;
        }
        try (var picture = Screenshot.takeScreenshot(minecraft.getMainRenderTarget())) {
            var colors = new HashSet<Integer>();
            for (int x = 0; x < picture.getWidth(); x += 8) for (int y = 0; y < picture.getHeight(); y += 8) colors.add(picture.getPixelRGBA(x, y));
            if (colors.size() < 32) throw new IllegalStateException("Insufficient rendered framebuffer variation: " + colors.size());
            picture.writeToFile(minecraft.gameDirectory.toPath().resolve("hidden-" + scenario + ".png"));
            LogUtils.getLogger().info("HIDDEN_CLIENT_PASS scenario={} readyTicks={} visible=false focused=false cursor=normal framebuffer={}x{} colors={}", scenario, readyTicks, picture.getWidth(), picture.getHeight(), colors.size());
        } catch (IOException exception) { throw new IllegalStateException("Screenshot write failed", exception); }
        finished = true;
        minecraft.stop();
    }
}
