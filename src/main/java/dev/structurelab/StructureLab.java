package dev.structurelab;

import com.mojang.serialization.MapCodec;
import net.minecraft.core.BlockPos;
import net.minecraft.core.registries.Registries;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.world.level.block.BaseEntityBlock;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.entity.BlockEntityType;
import net.minecraft.world.level.block.state.BlockBehaviour;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.storage.ValueInput;
import net.minecraft.world.level.storage.ValueOutput;
import net.neoforged.bus.api.IEventBus;
import net.neoforged.fml.common.Mod;
import net.neoforged.neoforge.common.NeoForge;
import net.neoforged.neoforge.event.server.ServerStartedEvent;
import net.neoforged.neoforge.event.server.ServerStoppedEvent;
import net.neoforged.neoforge.registries.*;

@Mod("structurelab")
public final class StructureLab {
    static final DeferredRegister.Blocks BLOCKS = DeferredRegister.createBlocks("structurelab");
    static final DeferredRegister.Items ITEMS = DeferredRegister.createItems("structurelab");
    static final DeferredRegister<BlockEntityType<?>> ENTITIES = DeferredRegister.create(Registries.BLOCK_ENTITY_TYPE, "structurelab");
    public static final DeferredBlock<ViewPad> PAD = BLOCKS.registerBlock("view_pad", ViewPad::new, p -> p.strength(0.5f));
    public static final DeferredHolder<BlockEntityType<?>, BlockEntityType<ViewPadEntity>> PAD_ENTITY = ENTITIES.register(
            "view_pad", () -> new BlockEntityType<>(ViewPadEntity::new, PAD.get()));
    public StructureLab(IEventBus bus) {
        ITEMS.registerSimpleBlockItem("view_pad", PAD);
        BLOCKS.register(bus); ITEMS.register(bus); ENTITIES.register(bus);
        NeoForge.EVENT_BUS.addListener((ServerStartedEvent e) -> LabSession.open(e.getServer()));
        NeoForge.EVENT_BUS.addListener((ServerStoppedEvent e) -> LabSession.close(e.getServer()));
        NeoForge.EVENT_BUS.addListener(LabPlacement::tick);
    }
    public static final class ViewPad extends BaseEntityBlock {
        public static final MapCodec<ViewPad> CODEC = simpleCodec(ViewPad::new);
        public ViewPad(BlockBehaviour.Properties properties) { super(properties); }
        @Override protected MapCodec<? extends BaseEntityBlock> codec() { return CODEC; }
        @Override public BlockEntity newBlockEntity(BlockPos pos, BlockState state) { return new ViewPadEntity(pos, state); }
    }
    public static final class ViewPadEntity extends BlockEntity {
        private CompoundTag view = new CompoundTag();
        public ViewPadEntity(BlockPos pos, BlockState state) { super(PAD_ENTITY.get(), pos, state); }
        @Override protected void loadAdditional(ValueInput input) {
            super.loadAdditional(input); view = input.read("view", CompoundTag.CODEC).orElseGet(CompoundTag::new);
        }
        @Override protected void saveAdditional(ValueOutput output) {
            super.saveAdditional(output); output.store("view", CompoundTag.CODEC, view);
        }
    }
}
