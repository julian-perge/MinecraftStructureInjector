package dev.structurelab.mixin;

import net.minecraft.client.MouseHandler;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Shadow;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

/** Logical in-game mouse state without calling OS cursor capture/position APIs. */
@Mixin(MouseHandler.class)
public abstract class HiddenMouseMixin {
    @Shadow private boolean mouseGrabbed;
    @Inject(method = "grabMouse", at = @At("HEAD"), cancellable = true)
    private void planetary$virtualGrab(CallbackInfo ci) {
        if (Boolean.getBoolean("structurelab.hiddenClient")) { mouseGrabbed = true; ci.cancel(); }
    }
    @Inject(method = "releaseMouse", at = @At("HEAD"), cancellable = true)
    private void planetary$virtualRelease(CallbackInfo ci) {
        if (Boolean.getBoolean("structurelab.hiddenClient")) { mouseGrabbed = false; ci.cancel(); }
    }
    @Inject(method = "turnPlayer", at = @At("HEAD"), cancellable = true)
    private void planetary$scriptedLookOnly(CallbackInfo ci) {
        if (Boolean.getBoolean("structurelab.hiddenClient")) ci.cancel();
    }
}
