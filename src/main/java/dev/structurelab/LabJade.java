package dev.structurelab;

import com.google.gson.JsonObject;
import net.minecraft.world.phys.BlockHitResult;
import snownee.jade.api.IWailaClientRegistration;
import snownee.jade.api.IWailaPlugin;
import snownee.jade.api.WailaPlugin;

/** Jade finds this class by its annotation, so it never loads when Jade is missing. It keeps the text of the last tooltip Jade built. */
@WailaPlugin
public final class LabJade implements IWailaPlugin {
    private static volatile String text;
    private static volatile String target;
    private static volatile long collectedAt;
    @Override public void registerClient(IWailaClientRegistration registration){
        registration.addTooltipCollectedCallback((box,accessor)->{
            text=box.getTooltip().getNarration();
            target=accessor.getHitResult() instanceof BlockHitResult hit?hit.getBlockPos().toShortString():null;
            collectedAt=System.currentTimeMillis();
        });
    }
    static JsonObject lastTooltip(){
        JsonObject out=new JsonObject();out.addProperty("text",text);out.addProperty("block",target);
        out.addProperty("age_ms",collectedAt==0?-1:System.currentTimeMillis()-collectedAt);
        return out;
    }
}
