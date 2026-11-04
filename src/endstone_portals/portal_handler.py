"""Handles block-based portal triggers (proximity detection and teleportation)."""

from __future__ import annotations

import time
from collections.abc import Callable
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from endstone.plugin import Plugin
    from .models import PortalStore

from .particle_effects import normalize_dimension


# Blocks that accept a "facing" block state
_FACING_BLOCKS = {
    "minecraft:observer", "minecraft:dispenser", "minecraft:dropper",
    "minecraft:piston", "minecraft:sticky_piston", "minecraft:hopper",
    "minecraft:furnace", "minecraft:blast_furnace", "minecraft:smoker",
    "minecraft:chest", "minecraft:trapped_chest", "minecraft:barrel",
    "minecraft:carved_pumpkin", "minecraft:jack_o_lantern",
    "minecraft:loom", "minecraft:lectern", "minecraft:grindstone",
    "minecraft:stonecutter", "minecraft:end_portal_frame",
}

# Nether portal uses "portal_axis" ("x" or "z"), not "facing"
_NETHER_PORTAL = "minecraft:nether_portal"

# End portal has no relevant block states to set
_END_PORTAL = "minecraft:end_portal"


def _facing_for_orientation(orientation: str) -> str:
    """
    Map portal orientation to a Minecraft block facing value.
      north/south  → portal plane is perpendicular to Z → blocks face north
      east/west    → portal plane is perpendicular to X → blocks face east
      up           → horizontal portal → blocks face up
    """
    return {
        "north": "north", "south": "north",
        "east":  "east",  "west":  "east",
        "up":    "up",
    }.get(orientation.lower(), "north")


def _portal_axis_for_orientation(orientation: str) -> str:
    """
    Map portal orientation to the nether_portal portal_axis state.
      north/south  → frame spans the X axis → portal_axis = "x"
      east/west    → frame spans the Z axis → portal_axis = "z"
      up           → horizontal, default to "x"
    """
    return {
        "north": "x", "south": "x",
        "east":  "z", "west":  "z",
        "up":    "x",
    }.get(orientation.lower(), "x")


def place_inner_blocks(plugin, dimension, portal) -> None:
    """
    Place filler blocks inside a portal frame using the correct Endstone API.

    Uses ``server.create_block_data(type, states)`` to build a BlockData
    with the correct facing/axis state, then ``block.set_data(block_data)``
    to place it in the world.
    """
    if not portal.inner_block_type or not portal.inner_blocks:
        return

    block_id  = portal.inner_block_type
    facing    = _facing_for_orientation(portal.inner_block_facing)
    server    = plugin.server

    # Pre-build the BlockData object once — reuse for every position
    try:
        if block_id == _NETHER_PORTAL:
            axis = _portal_axis_for_orientation(portal.inner_block_facing)
            block_data = server.create_block_data(block_id, {"portal_axis": axis})
        elif block_id == _END_PORTAL:
            block_data = server.create_block_data(block_id)
        elif block_id in _FACING_BLOCKS:
            block_data = server.create_block_data(block_id, {"facing_direction": facing})
        else:
            # Plain block — no extra states needed
            block_data = server.create_block_data(block_id)
    except Exception as e:
        plugin.logger.warning(f"create_block_data failed for '{block_id}': {e}")
        # Fallback: try with no states
        try:
            block_data = server.create_block_data(block_id)
        except Exception as e2:
            plugin.logger.error(f"Cannot create block data for '{block_id}': {e2}")
            return

    placed = 0
    for pos in portal.inner_blocks:
        bx, by, bz = pos
        try:
            block = dimension.get_block_at(bx, by, bz)
            if block is None:
                continue
            block.set_data(block_data)
            placed += 1
        except Exception as ex:
            plugin.logger.debug(f"Inner block set_data at {bx},{by},{bz}: {ex}")

    plugin.logger.info(
        f"Portal '{portal.name}': placed {placed}/{len(portal.inner_blocks)} "
        f"'{block_id}' fill blocks (facing={facing})"
    )


def clear_inner_blocks(plugin, dimension, portal) -> None:
    """
    Replace portal fill blocks with air (called when a portal is deleted).
    Only replaces positions that still contain the fill block type.
    """
    if not portal.inner_block_type or not portal.inner_blocks:
        return

    server         = plugin.server
    expected_type  = normalize_block_type(portal.inner_block_type)

    try:
        air_data = server.create_block_data("minecraft:air")
    except Exception as e:
        plugin.logger.warning(f"Cannot create air BlockData: {e}")
        return

    cleared = 0
    for pos in portal.inner_blocks:
        bx, by, bz = pos
        try:
            block = dimension.get_block_at(bx, by, bz)
            if block is None:
                continue
            # Only clear if it's still our fill block — don't nuke player-placed blocks
            if normalize_block_type(block.type) == expected_type:
                block.set_data(air_data)
                cleared += 1
        except Exception as ex:
            plugin.logger.debug(f"Inner block clear at {bx},{by},{bz}: {ex}")

    plugin.logger.info(
        f"Portal '{portal.name}': cleared {cleared}/{len(portal.inner_blocks)} fill blocks"
    )


def normalize_block_type(block_type: str) -> str:
    """Normalize block type strings for comparison (strips namespace, lowercases)."""
    if not block_type:
        return ""
    return block_type.lower().replace("minecraft:", "")


# List of common passable blocks where players can stand without suffocating
_PASSABLE_BLOCKS = {
    "air", "cave_air", "void_air",
    "water", "lava",
    "grass", "tall_grass", "fern", "large_fern",
    "deadbush", "dandelion", "poppy", "blue_orchid", "allium", "azure_bluet",
    "red_tulip", "orange_tulip", "white_tulip", "pink_tulip", "oxeye_daisy",
    "cornflower", "lily_of_the_valley", "wither_rose", "sunflower", "lilac",
    "rose_bush", "peony", "pitcher_plant", "torchflower",
    "torch", "soul_torch", "redstone_torch",
    "sapling", "oak_sapling", "spruce_sapling", "birch_sapling", "jungle_sapling",
    "acacia_sapling", "dark_oak_sapling", "mangrove_propagule", "cherry_sapling",
    "bamboo_sapling",
    "ladder", "vine", "cave_vines", "cave_vines_plant", "twisting_vines",
    "twisting_vines_plant", "weeping_vines", "weeping_vines_plant",
    "sugar_cane", "snow", "fire", "soul_fire",
    "redstone_wire", "tripwire", "tripwire_hook",
    "nether_portal", "end_portal", "end_gateway",
    "sign", "wall_sign", "spruce_sign", "spruce_wall_sign", "birch_sign",
    "birch_wall_sign", "jungle_sign", "jungle_wall_sign", "acacia_sign",
    "acacia_wall_sign", "dark_oak_sign", "dark_oak_wall_sign", "mangrove_sign",
    "mangrove_wall_sign", "cherry_sign", "cherry_wall_sign", "bamboo_sign",
    "bamboo_wall_sign",
    "lever", "stone_button", "wooden_button",
    "carpet", "white_carpet", "orange_carpet", "magenta_carpet", "light_blue_carpet",
    "yellow_carpet", "lime_carpet", "pink_carpet", "gray_carpet", "light_gray_carpet",
    "cyan_carpet", "purple_carpet", "blue_carpet", "brown_carpet", "green_carpet",
    "red_carpet", "black_carpet",
    "seagrass", "tall_seagrass", "kelp", "kelp_plant",
    "sculk_vein", "glow_lichen",
}


def is_passable(block_type: str) -> bool:
    """Return True if the block is passable / non-solid (e.g. air, grass, flower)."""
    if not block_type:
        return True
    norm = normalize_block_type(block_type)
    if norm in ("", "air", "cave_air", "void_air", "water", "lava"):
        return True
    # check category suffixes
    if (norm.endswith("_air") or 
            norm.endswith("_flower") or 
            norm.endswith("_torch") or 
            norm.endswith("_sign") or 
            norm.endswith("_sapling") or 
            norm.endswith("_button") or 
            norm.endswith("_carpet") or
            norm.endswith("_vines") or
            norm.endswith("_vines_plant")):
        return True
    return norm in _PASSABLE_BLOCKS


def find_safe_location(
    dimension, x: float, y: float, z: float, *,
    accept: Callable[[float, float, float], bool] | None = None,
    require_ground: bool = False,
) -> tuple[float, float, float] | None:
    """
    Search around (x, y, z) in the given dimension to find a location
    where a player can stand without suffocating.
    Prioritizes 3D distance to the original destination.

    Portal exits use ``require_ground`` and ``accept`` to reject unloaded,
    hazardous, floating, or occupied destinations, returning None on failure.
    """
    import math

    # Generate candidate offsets and sort them by absolute 3D distance
    candidates = []
    for dx in range(-3, 4):
        for dz in range(-3, 4):
            for dy in range(-8, 9):
                dist = math.sqrt(dx*dx + dy*dy + dz*dz)
                candidates.append((dist, dx, dy, dz))

    candidates.sort(key=lambda item: item[0])

    best_passable = None

    for dist, dx, dy, dz in candidates:
        target_x = x + dx
        target_y = y + dy
        target_z = z + dz

        # Bounds check
        if target_y < -64 or target_y > 320:
            continue

        bx = int(math.floor(target_x))
        by = int(math.floor(target_y))
        bz = int(math.floor(target_z))

        try:
            feet_block = dimension.get_block_at(bx, by, bz)
            head_block = dimension.get_block_at(bx, by + 1, bz)
            floor_block = dimension.get_block_at(bx, by - 1, bz)

            # Check if chunk is unloaded (returns None)
            if feet_block is None or head_block is None or floor_block is None:
                if require_ground:
                    continue
                try:
                    highest_y = dimension.get_highest_block_y_at(bx, bz)
                    # Adjust y level to be right above the highest block
                    feet_type = "minecraft:air"
                    head_type = "minecraft:air"
                    floor_type = "minecraft:stone" # pretend floor is solid block
                    by = int(highest_y + 1)
                except Exception:
                    feet_type = "minecraft:air"
                    head_type = "minecraft:air"
                    floor_type = "minecraft:air"
            else:
                feet_type = feet_block.type
                head_type = head_block.type
                floor_type = floor_block.type
        except Exception:
            if require_ground:
                continue
            feet_type = "minecraft:air"
            head_type = "minecraft:air"
            floor_type = "minecraft:air"

        frac_x = 0.5 if require_ground else x - math.floor(x)
        frac_z = 0.5 if require_ground else z - math.floor(z)
        candidate = (float(bx) + frac_x, float(by), float(bz) + frac_z)
        if accept is not None and not accept(*candidate):
            continue

        if require_ground:
            hazards = {
                "water", "flowing_water", "lava", "flowing_lava", "fire", "soul_fire",
                "nether_portal", "portal", "end_portal", "end_gateway", "powder_snow",
                "cactus", "magma", "magma_block", "campfire", "soul_campfire",
                "sweet_berry_bush", "wither_rose",
            }
            if any(normalize_block_type(t) in hazards for t in (feet_type, head_type, floor_type)):
                continue

        if is_passable(feet_type) and is_passable(head_type):
            # If the floor is solid, we found the perfect safe coordinate
            if not is_passable(floor_type):
                return candidate

            # Otherwise, keep as a floating fallback
            if not require_ground and best_passable is None:
                best_passable = (target_x, float(by), target_z)

    if best_passable is not None:
        return best_passable

    if require_ground or accept is not None:
        return None
    return (x, y, z)


class BlockPortalHandler:
    """Detects players entering block portal areas and triggers teleportation."""

    def __init__(self, plugin: Plugin, store: PortalStore):
        self.plugin = plugin
        self.store = store
        self._cooldowns: dict[str, float] = {}  # player_name -> last_use timestamp
        self._must_exit: set[str] = set()
        self._sessions: dict[str, object] = {}
        self._join_until: dict[str, float] = {}
        self._pending_transfers: dict[str, object] = {}
        self._task = None

    def start(self) -> None:
        """Start the proximity check loop (every 10 ticks = ~0.5s)."""
        if self._task is not None:
            return
        for player in self.plugin.server.online_players:
            self.on_player_join(player)
        self._task = self.plugin.server.scheduler.run_task(
            self.plugin, self._tick, delay=40, period=10
        )

    def stop(self) -> None:
        """Stop the proximity check loop."""
        self._sessions.clear()
        self._pending_transfers.clear()
        self._must_exit.clear()
        self._join_until.clear()
        self._cooldowns.clear()
        if self._task is not None:
            try:
                self.plugin.server.scheduler.cancel_task(self._task.task_id)
            except Exception:
                pass
            self._task = None

    def on_player_join(self, player) -> None:
        """Ensure players joining inside a portal are moved safely outside it."""
        try:
            p_name = player.name
            session = object()
            self._sessions[p_name] = session
            self._pending_transfers.pop(p_name, None)
            self._must_exit.add(p_name)
            self._cooldowns[p_name] = time.time() + 20.0
            self._join_until[p_name] = self._cooldowns[p_name]

            def check_spawn_in_portal():
                try:
                    p = self._session_player(p_name, session)
                    if not p:
                        return
                    self._move_out_of_portals(p)
                except Exception as e:
                    self.plugin.logger.error(f"Join safeguard check error: {e}")

            self.plugin.server.scheduler.run_task(self.plugin, check_spawn_in_portal, delay=1)
            self.plugin.server.scheduler.run_task(self.plugin, check_spawn_in_portal, delay=15)
            self.plugin.server.scheduler.run_task(self.plugin, check_spawn_in_portal, delay=35)

        except Exception as e:
            self.plugin.logger.error(f"Join safeguard error: {e}")

    def on_player_quit(self, player) -> None:
        """Invalidate callbacks so a reconnect cannot inherit an old transfer."""
        p_name = player.name
        self._sessions.pop(p_name, None)
        self._pending_transfers.pop(p_name, None)
        self._join_until.pop(p_name, None)
        self._cooldowns.pop(p_name, None)
        self._must_exit.discard(p_name)

    def on_player_teleport(self, player, destination) -> None:
        """Arrival by teleport must never count as walking into a portal."""
        if self._portal_at(destination) is not None:
            self._must_exit.add(player.name)

    def _session_player(self, name: str, session: object):
        if self._sessions.get(name) is not session:
            return None
        return self.plugin.server.get_player(name)

    def _portal_at(self, loc):
        dimension = normalize_dimension(loc.dimension)
        return next((portal for portal in self.store.block_portals.values()
                     if normalize_dimension(portal.dimension) == dimension
                     and portal.player_in_portal(loc.x, loc.y, loc.z)), None)

    def _move_out_of_portals(self, player) -> bool:
        """Move to loaded, solid ground outside every portal; never guess an exit."""
        loc = player.location
        portal = self._portal_at(loc)
        if portal is None:
            return True

        from endstone.level import Location

        dimension = normalize_dimension(loc.dimension)
        portals = [p for p in self.store.block_portals.values()
                   if normalize_dimension(p.dimension) == dimension]

        blocks = portal.inner_blocks + portal.frame_blocks
        min_x, max_x = min(b[0] for b in blocks), max(b[0] for b in blocks)
        min_z, max_z = min(b[2] for b in blocks), max(b[2] for b in blocks)

        def outside_portals(x, y, z):
            if min_x - 0.3 <= x < max_x + 1.3 and min_z - 0.3 <= z < max_z + 1.3:
                return False
            return not any(p.player_in_portal(x, y, z) for p in portals)

        # Use the full frame bounds, including large and horizontal portals.
        exits = [
            (min_x - 2.5, loc.y, loc.z), (max_x + 3.5, loc.y, loc.z),
            (loc.x, loc.y, min_z - 2.5), (loc.x, loc.y, max_z + 3.5),
        ]
        exits.sort(key=lambda p: (p[0] - loc.x) ** 2 + (p[2] - loc.z) ** 2)
        for x, y, z in exits:
            safe = find_safe_location(
                loc.dimension, x, y, z, accept=outside_portals, require_ground=True,
            )
            if safe is None:
                continue
            if not player.teleport(Location(loc.dimension, *safe, loc.pitch, loc.yaw)):
                return False
            # A teleport may be cancelled or redirected by another plugin.
            if self._portal_at(player.location) is not None:
                return False
            self.plugin.logger.info(f"Moved {player.name} outside portal '{portal.name}'")
            return True
        return False

    def _tick(self) -> None:
        """Check if any online player is standing inside a block portal."""
        try:
            now = time.time()
            online_players = self.plugin.server.online_players
            if not online_players:
                return

            for player in online_players:
                try:
                    p_name = player.name
                    loc = player.location
                    portal = self._portal_at(loc)

                    # Keep checking throughout login, including late location restores.
                    if p_name in self._join_until:
                        if portal is not None:
                            self._must_exit.add(p_name)
                            self._move_out_of_portals(player)
                            continue
                        if now < self._join_until[p_name]:
                            continue
                        self._join_until.pop(p_name, None)

                    # Cooldown expiry alone must never rearm an occupied portal.
                    if p_name in self._must_exit:
                        if portal is not None:
                            continue
                        self._must_exit.discard(p_name)

                    if p_name in self._pending_transfers:
                        continue

                    # Check cooldown
                    cooldown_until = self._cooldowns.get(p_name, 0)
                    if now < cooldown_until:
                        continue

                    if portal is not None:
                        self._trigger_portal(player, portal, now)

                except Exception:
                    continue

        except Exception:
            pass

    def _trigger_portal(self, player, portal, now: float) -> None:
        """Trigger a block portal teleport for a player."""
        try:
            p_name = player.name

            # Apply cooldown
            self._must_exit.add(p_name)
            self._cooldowns[p_name] = now + portal.cooldown

            if portal.dest_type == "server":
                self._transfer_to_server(player, portal)
            else:
                self._teleport_to_location(player, portal)

        except Exception as e:
            self.plugin.logger.error(f"Block portal trigger error: {e}")

    def _transfer_to_server(self, player, portal) -> None:
        """Transfer a player to another server with anti-loop protection."""
        p_name = player.name
        if p_name in self._pending_transfers:
            return
        session = self._sessions.setdefault(p_name, object())
        transfer = object()
        self._pending_transfers[p_name] = transfer

        def current_player():
            if self._pending_transfers.get(p_name) is not transfer:
                return None
            return self._session_player(p_name, session)

        def finish():
            if self._pending_transfers.get(p_name) is transfer:
                self._pending_transfers.pop(p_name, None)

        try:
            if portal.message:
                player.send_message(f"§a{portal.message}")
            player.send_message(
                f"§7Transferring to §f{portal.dest_host}:{portal.dest_port}§7..."
            )

            # Apply a longer cooldown (20 seconds) specifically for server transfers
            self._cooldowns[p_name] = max(self._cooldowns.get(p_name, 0), time.time() + 20.0)
            self._must_exit.add(p_name)

            # Teleport the player away first, then transfer them after a delay
            def do_teleport_and_transfer():
                try:
                    p = current_player()
                    if not p:
                        finish()
                        return

                    if not self._move_out_of_portals(p):
                        p.send_message("§cTransfer cancelled: could not move you safely outside the portal. Step outside and try again.")
                        self.plugin.logger.warning(f"Transfer cancelled for {p_name}: no verified portal exit")
                        finish()
                        return

                    # 2. Trigger transfer 60 ticks (3.0s) later to allow client coordinates to sync fully
                    def do_transfer():
                        try:
                            p2 = current_player()
                            if not p2:
                                return
                            # Verify the actual position again immediately before disconnecting.
                            if self._portal_at(p2.location) is not None:
                                self._must_exit.add(p_name)
                                p2.send_message("§cTransfer cancelled: you entered a portal again. Step outside and try again.")
                                return
                            p2.transfer(portal.dest_host, portal.dest_port)
                        except Exception as e:
                            self.plugin.logger.error(f"Delayed transfer error: {e}")
                        finally:
                            finish()

                    self.plugin.server.scheduler.run_task(
                        self.plugin, do_transfer, delay=60
                    )
                except Exception as e:
                    finish()
                    self.plugin.logger.error(f"Deferred teleport/transfer error: {e}")

            # Schedule teleport setup task on next tick
            self.plugin.server.scheduler.run_task(
                self.plugin, do_teleport_and_transfer, delay=1
            )

        except Exception as e:
            finish()
            self.plugin.logger.error(f"Server transfer error: {e}")
            player.send_message("§cTransfer failed!")

    def _teleport_to_location(self, player, portal) -> None:
        """Teleport a player to a local coordinate destination."""
        try:
            from endstone.level import Location

            dim = self._get_dimension(portal.dest_dim)
            if dim is None:
                player.send_message("§cDestination dimension not found!")
                return

            # Find safe landing spot (might run on unloaded chunk heightmap)
            safe_x, safe_y, safe_z = find_safe_location(dim, portal.dest_x, portal.dest_y, portal.dest_z)

            p_name = player.name

            # Schedule teleport on the next tick
            def do_teleport():
                try:
                    p = self.plugin.server.get_player(p_name)
                    if not p:
                        return
                    target_dim = self._get_dimension(portal.dest_dim)
                    if not target_dim:
                        return
                    loc = Location(target_dim, safe_x, safe_y, safe_z)
                    p.teleport(loc)

                    # Post-teleport safeguard check (2 ticks later, after chunk loads)
                    def post_teleport_check():
                        try:
                            p2 = self.plugin.server.get_player(p_name)
                            if not p2:
                                return
                            curr_loc = p2.location
                            curr_dim = curr_loc.dimension
                            sx, sy, sz = find_safe_location(curr_dim, curr_loc.x, curr_loc.y, curr_loc.z)
                            if abs(sx - curr_loc.x) > 0.01 or abs(sy - curr_loc.y) > 0.01 or abs(sz - curr_loc.z) > 0.01:
                                p2.teleport(Location(curr_dim, sx, sy, sz))
                                self.plugin.logger.info(f"Safeguard: adjusted {p_name} to {sx:.1f}, {sy:.1f}, {sz:.1f} to prevent suffocation.")
                        except Exception as e:
                            self.plugin.logger.error(f"Post-teleport safety check error: {e}")

                    self.plugin.server.scheduler.run_task(self.plugin, post_teleport_check, delay=2)

                    if portal.message:
                        p.send_message(f"§a{portal.message}")
                    else:
                        p.send_message(f"§aTeleported via §f{portal.name}§a!")
                except Exception as e:
                    self.plugin.logger.error(f"Deferred teleport error: {e}")

            self.plugin.server.scheduler.run_task(self.plugin, do_teleport, delay=1)

        except Exception as e:
            self.plugin.logger.error(f"Local teleport error: {e}")
            player.send_message("§cTeleportation failed!")

    def _get_dimension(self, dim_name: str):
        """Get a dimension object by name."""
        try:
            dim_name = dim_name.lower().strip()
            level = self.plugin.server.level
            for dim in level.dimensions:
                name = getattr(dim, 'name', str(dim)).lower()
                if ":" in name:
                    name = name.split(":")[-1]
                if name == dim_name or name.replace("the_", "") == dim_name.replace("the_", ""):
                    return dim
        except Exception:
            pass
        return None
