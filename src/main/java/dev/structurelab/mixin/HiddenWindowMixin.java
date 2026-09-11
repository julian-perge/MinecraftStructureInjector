package dev.structurelab.mixin;

import com.mojang.blaze3d.platform.Window;
import org.lwjgl.glfw.GLFW;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Shadow;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

/** Opt-in test process only. Visibility/focus hints are set before any game window exists. */
@Mixin(Window.class)
public abstract class HiddenWindowMixin {
    @Shadow private boolean fullscreen;
    @Shadow private long window;
    @Shadow private int windowedWidth;
    @Shadow private int windowedHeight;
    @Inject(method = "<init>", at = @At(value = "INVOKE", target = "Lnet/neoforged/fml/loading/ImmediateWindowHandler;setupMinecraftWindow(Ljava/util/function/IntSupplier;Ljava/util/function/IntSupplier;Ljava/util/function/Supplier;Ljava/util/function/LongSupplier;)J"))
    private void planetary$hiddenBeforeCreation(CallbackInfo ci) {
        if (!Boolean.getBoolean("structurelab.hiddenClient")) return;
        fullscreen = false;
        GLFW.glfwWindowHint(GLFW.GLFW_DECORATED, GLFW.GLFW_FALSE);
        GLFW.glfwWindowHint(GLFW.GLFW_VISIBLE, GLFW.GLFW_FALSE);
        GLFW.glfwWindowHint(GLFW.GLFW_FOCUSED, GLFW.GLFW_FALSE);
        GLFW.glfwWindowHint(GLFW.GLFW_FOCUS_ON_SHOW, GLFW.GLFW_FALSE);
    }
    @Inject(method = "setMode", at = @At("HEAD"), cancellable = true)
    private void planetary$noMonitorChanges(CallbackInfo ci) {
        if (Boolean.getBoolean("structurelab.hiddenClient")) { fullscreen = false; GLFW.glfwSetWindowSize(window, windowedWidth, windowedHeight); ci.cancel(); }
    }
    @Inject(method = "bootCrash", at = @At("HEAD"))
    private static void planetary$logBootFailure(int error, long description, CallbackInfo ci) {
        if (Boolean.getBoolean("structurelab.hiddenClient")) throw new IllegalStateException("Hidden client GLFW boot error " + error);
    }
}
