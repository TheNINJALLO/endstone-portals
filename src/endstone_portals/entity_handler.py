"""Handles entity-based portal triggers (interact and hit)."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from endstone.plugin import Plugin
    from .models import PortalStore


class EntityPortalHandler:
    """Detects player interaction/hits with entities configured as portals."""

    def __init__(self, plugin: Plugin, store: PortalStore):
        self.plugin = plugin
        self.store = store
        self._cooldowns: dict[str, float] = {}  # player_name -> last_use timestamp
        self._debounce: dict[str, float] = {}  # player_name -> last_event timestamp

    def handle_interact(self, player, actor) -> bool:
        """Handle a player right-clicking an entity. Returns True if handled."""
        return self._try_trigger(player, actor, "interact")

    def handle_hit(self, player, actor) -> bool:
        """Handle a player hitting (left-click) an entity. Returns True if handled."""
        return self._try_trigger(player, actor, "hit")

    def _try_trigger(self, player, actor, trigger_type: str) -> bool:
        """Attempt to trigger a portal for the given player/actor interaction."""
        try:
            now = time.time()
            p_name = player.name

            # Debounce — prevent double-firing within 0.5s
            if now - self._debounce.get(p_name, 0) < 0.5:
                return False
            self._debounce[p_name] = now

            # Get actor info safely
            actor_type = getattr(actor, 'type', '')
            actor_tags = list(getattr(actor, 'scoreboard_tags', []))

            # Find matching portal
            for portal in self.store.entity_portals.values():
                # Check trigger type matches
                if portal.trigger != "both" and portal.trigger != trigger_type:
                    continue

                if not portal.matches_actor(str(actor_type), actor_tags):
                    continue

                # Check cooldown (3 second default for entity portals)
                if now - self._cooldowns.get(p_name, 0) < 3.0:
                    player.send_message("§cPlease wait before using this portal again.")
                    return True

                self._cooldowns[p_name] = now

                # Execute action
                if portal.action == "form":
                    self._show_confirmation(player, portal)
                else:
                    self._execute_teleport(player, portal)

                return True

        except Exception as e:
            try:
                self.plugin.logger.error(f"Entity portal error: {e}")
            except Exception:
                pass

        return False

    def _show_confirmation(self, player, portal) -> None:
        """Show a confirmation form before teleporting."""
        try:
            from endstone.form import ActionForm, Button

            dest_info = ""
            if portal.dest_type == "server":
                dest_info = f"§7Server: §f{portal.dest_host}:{portal.dest_port}"
            else:
                dest_info = f"§7Location: §f{portal.dest_x:.0f}, {portal.dest_y:.0f}, {portal.dest_z:.0f} ({portal.dest_dim})"

            content = f"§bTravel to §f{portal.name}§b?\n\n{dest_info}"
            if portal.message:
                content += f"\n\n§e{portal.message}"

            def on_submit(p, index):
                if index == 0:  # Confirm
                    self._execute_teleport(p, portal)

            form = ActionForm(
                title=f"§l§5Portal: {portal.name}",
                content=content,
                buttons=[
                    Button(text="§a§lConfirm"),
                    Button(text="§c§lCancel"),
                ],
                on_submit=on_submit,
            )
            player.send_form(form)
        except Exception as e:
            self.plugin.logger.error(f"Confirmation form error: {e}")

    def _execute_teleport(self, player, portal) -> None:
        """Teleport or transfer the player based on portal configuration."""
        try:
            p_name = player.name

            if portal.dest_type == "server":
                if portal.message:
                    player.send_message(f"§a{portal.message}")
                player.send_message(f"§7Transferring to §f{portal.dest_host}:{portal.dest_port}§7...")
                
                # Apply a longer cooldown (15 seconds) specifically for server transfers
                self._cooldowns[p_name] = time.time() + 15.0

                # Defer the transfer to 20 ticks delay (1.0s)
                def do_transfer():
                    try:
                        p = self.plugin.server.get_player(p_name)
                        if p:
                            p.transfer(portal.dest_host, portal.dest_port)
                    except Exception as e:
                        self.plugin.logger.error(f"Deferred transfer error: {e}")

                self.plugin.server.scheduler.run_task(self.plugin, do_transfer, delay=20)
            else:
                # Local teleport
                from endstone.level import Location
                from .portal_handler import find_safe_location

                dim = self._get_dimension(portal.dest_dim)
                if dim is None:
                    player.send_message("§cDestination dimension not found!")
                    return

                # Find safe location
                safe_x, safe_y, safe_z = find_safe_location(dim, portal.dest_x, portal.dest_y, portal.dest_z)

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
                            p.send_message(f"§aTeleported to §f{portal.name}§a!")
                    except Exception as e:
                        self.plugin.logger.error(f"Deferred teleport error: {e}")

                self.plugin.server.scheduler.run_task(self.plugin, do_teleport, delay=1)

        except Exception as e:
            self.plugin.logger.error(f"Teleport error: {e}")
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
