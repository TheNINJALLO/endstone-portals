"""Proximity-based particle effect rendering for block portals."""

from __future__ import annotations

import random
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from endstone.plugin import Plugin
    from .models import PortalStore

# Available particle effects that operators can choose from
PARTICLE_LIST = [
    "minecraft:basic_portal_particle",
    "minecraft:end_chest",
    "minecraft:redstone_ore_dust_particle",
    "minecraft:basic_flame_particle",
    "minecraft:blue_flame_particle",
    "minecraft:soul_particle",
    "minecraft:dragon_breath_trail",
    "minecraft:enchanting_table_particle",
    "minecraft:totem_particle",
    "minecraft:heart_particle",
    "minecraft:villager_happy",
    "minecraft:water_drip_particle",
    "minecraft:lava_drip_particle",
    "minecraft:basic_smoke_particle",
    "minecraft:campfire_smoke_particle",
    "minecraft:campfire_tall_smoke_particle",
    "minecraft:critical_hit_emitter",
    "minecraft:endrod",
    "minecraft:snowflake_particle",
    "minecraft:sparkler_emitter",
    "minecraft:wax_particle",
    "minecraft:crop_growth_emitter",
    "minecraft:falling_dust_dragon_egg_particle",
    "minecraft:mob_portal",
    # ── New particles ──
    "minecraft:water_splash_particle",
    "minecraft:cauldron_splash_particle",
    "minecraft:honey_drip_particle",
    "minecraft:stalactite_lava_drip_particle",
    "minecraft:candle_flame_particle",
    "minecraft:sculk_soul_particle",
    "minecraft:cherry_leaves_particle",
    "minecraft:dust_plume_particle",
    "minecraft:trial_spawner_particle",
    "minecraft:wind_explosion_emitter",
    "minecraft:vault_connection_particle",
    "minecraft:ominous_item_spawner_particle",
    "minecraft:eyeblossom_open_particle",
    "minecraft:eyeblossom_close_particle",
    "minecraft:pale_oak_leaves_particle",
    "minecraft:creaking_heart_trial_spawner_particle",
]

# Friendly display names for the form toggles
PARTICLE_DISPLAY_NAMES = [
    "Portal (Purple Swirl)",
    "Ender Chest",
    "Redstone Dust",
    "Flame",
    "Blue Flame (Soul)",
    "Soul",
    "Dragon Breath",
    "Enchanting Table",
    "Totem of Undying",
    "Hearts",
    "Happy Villager",
    "Water Drip",
    "Lava Drip",
    "Smoke",
    "Campfire Smoke",
    "Campfire Tall Smoke",
    "Critical Hit",
    "End Rod",
    "Snowflake",
    "Sparkler",
    "Wax",
    "Crop Growth",
    "Dragon Egg Dust",
    "Mob Portal",
    # ── New display names ──
    "Water Splash",
    "Cauldron Splash",
    "Honey Drip",
    "Stalactite Lava Drip",
    "Candle Flame",
    "Sculk Soul",
    "Cherry Leaves",
    "Dust Plume",
    "Trial Spawner",
    "Wind Explosion",
    "Vault Connection",
    "Ominous Item Spawner",
    "Eyeblossom Open",
    "Eyeblossom Close",
    "Pale Oak Leaves",
    "Creaking Heart",
]

# Heavy emitter particles — these spawn many sub-particles per call and cause
# massive lag if spawned at the normal rate.  We only spawn 1 per block for these.
HEAVY_PARTICLES = {
    "minecraft:enchanting_table_particle",
    "minecraft:critical_hit_emitter",
    "minecraft:sparkler_emitter",
    "minecraft:crop_growth_emitter",
    "minecraft:wind_explosion_emitter",
    "minecraft:trial_spawner_particle",
    "minecraft:creaking_heart_trial_spawner_particle",
    "minecraft:ominous_item_spawner_particle",
}


def normalize_dimension(dimension) -> str:
    """Normalize a dimension object or string to a lowercase name."""
    name = getattr(dimension, 'name', str(dimension)).lower()
    if 'name=' in name:
        name = name.split("name='")[-1].split("'")[0]
    if ":" in name:
        name = name.split(":")[-1]
    name = name.strip()
    if name in ("end", "the_end"):
        return "the_end"
    return name


class ParticleManager:
    """Handles proximity-based particle rendering for all block portals."""

    def __init__(self, plugin: Plugin, store: PortalStore):
        self.plugin = plugin
        self.store = store
        self._task = None

    def start(self) -> None:
        """Start the particle rendering loop (every 10 ticks = ~0.5s)."""
        if self._task is not None:
            return
        self._task = self.plugin.server.scheduler.run_task(
            self.plugin, self._tick, delay=20, period=10
        )

    def stop(self) -> None:
        """Stop the particle rendering loop."""
        if self._task is not None:
            try:
                self.plugin.server.scheduler.cancel_task(self._task.task_id)
            except Exception:
                pass
            self._task = None

    def _tick(self) -> None:
        """Render particles for portals near online players."""
        try:
            online_players = self.plugin.server.online_players
            if not online_players:
                return

            for portal in self.store.block_portals.values():
                if not portal.inner_blocks:
                    continue

                # Resolve the particle list.  Supports both the old single-string
                # format and the new list-of-strings format.
                p_type = portal.particle_type
                if isinstance(p_type, str):
                    particles = [p_type]
                elif isinstance(p_type, list) and p_type:
                    particles = p_type
                else:
                    particles = ["minecraft:basic_portal_particle"]

                # Find players near this portal
                nearby_players = []
                for player in online_players:
                    try:
                        loc = player.location
                        p_dim = normalize_dimension(loc.dimension)
                        if p_dim != portal.dimension:
                            continue
                        if portal.player_near(loc.x, loc.y, loc.z):
                            nearby_players.append(player)
                    except Exception:
                        continue

                if not nearby_players:
                    continue

                # Spawn particles at inner block positions for nearby players
                for player in nearby_players:
                    try:
                        for block_pos in portal.inner_blocks:
                            bx, by, bz = block_pos

                            # Pick a random particle from the list each block
                            chosen = random.choice(particles)

                            # Heavy emitters get 1 spawn per block to avoid lag;
                            # normal particles get 8 for a thick, filled look.
                            count = 1 if chosen in HEAVY_PARTICLES else 8

                            for _ in range(count):
                                ox = random.uniform(-0.4, 0.4)
                                oy = random.uniform(0.0, 1.0)
                                oz = random.uniform(-0.4, 0.4)

                                player.spawn_particle(
                                    chosen,
                                    bx + 0.5 + ox,
                                    by + oy,
                                    bz + 0.5 + oz,
                                )
                    except Exception:
                        continue
        except Exception:
            pass
