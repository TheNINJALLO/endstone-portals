"""Main plugin class — registers commands, events, and starts scheduled tasks."""

from endstone.plugin import Plugin
from endstone.event import (
    event_handler,
    PlayerInteractActorEvent,
    PlayerJoinEvent,
    PlayerQuitEvent,
    PlayerTeleportEvent,
    ActorKnockbackEvent,
    BlockBreakEvent,
)

from .models import PortalStore
from .entity_handler import EntityPortalHandler
from .portal_handler import BlockPortalHandler
from .particle_effects import ParticleManager


class PortalsPlugin(Plugin):
    """Endstone portals plugin — entity and block portal system."""

    # Plugin metadata — name MUST be lowercase with underscores, MUST NOT start with "endstone"
    name = "portals"
    version = "1.1.10"
    api_version = "0.11"

    commands = {
        "portal": {
            "description": "Portal management commands",
            "usages": [
                "/portal",
                "/portal reload",
                "/portal list",
                "/portal delete <name: str>",
            ],
            "permissions": ["portals.admin"],
        },
    }

    permissions = {
        "portals.admin": {
            "description": "Access to portal management commands",
            "default": "op",
        },
    }

    def __init__(self):
        super().__init__()
        self.store = None
        self.entity_handler = None
        self.block_handler = None
        self.particle_mgr = None

    def on_enable(self):
        """Initialize the plugin, load data, start tasks, register events."""
        try:
            self.logger.info("Portals plugin enabling...")

            # Initialize data store
            self.store = PortalStore(self.data_folder)
            self.store.load()

            # Initialize handlers
            self.entity_handler = EntityPortalHandler(self, self.store)
            self.block_handler = BlockPortalHandler(self, self.store)
            self.particle_mgr = ParticleManager(self, self.store)

            # Register events — CRITICAL: without this, event handlers won't fire
            self.register_events(self)

            # Start scheduled tasks
            self.block_handler.start()
            self.particle_mgr.start()

            ep_count = len(self.store.entity_portals)
            bp_count = len(self.store.block_portals)
            self.logger.info(
                f"Portals plugin enabled! "
                f"Loaded {ep_count} entity portals, {bp_count} block portals."
            )

        except Exception as e:
            self.logger.error(f"Failed to enable portals plugin: {e}")

    def on_disable(self):
        """Cleanup on shutdown — cancel tasks, save data."""
        try:
            if self.block_handler:
                self.block_handler.stop()
            if self.particle_mgr:
                self.particle_mgr.stop()
            if self.store:
                self.store.save()
            self.logger.info("Portals plugin disabled.")
        except Exception as e:
            self.logger.error(f"Error during disable: {e}")

    # ── Command Handler ──────────────────────────────────────────────────

    def on_command(self, sender, command, args):
        """Handle /portal commands."""
        try:
            from endstone import Player

            if command.name.lower() != "portal":
                return False

            if not isinstance(sender, Player):
                sender.send_message("§cThis command can only be used in-game.")
                return True

            player = sender

            if not args:
                # Open the main menu form
                from .forms import show_main_menu
                show_main_menu(self, player, self.store)
                return True

            subcmd = args[0].lower()

            if subcmd == "reload":
                self.store.load()
                ep_count = len(self.store.entity_portals)
                bp_count = len(self.store.block_portals)
                player.send_message(
                    f"§aPortals reloaded! "
                    f"§f{ep_count} entity, {bp_count} block portals."
                )
                return True

            elif subcmd == "list":
                if not self.store.entity_portals and not self.store.block_portals:
                    player.send_message("§7No portals configured.")
                    return True

                player.send_message("§l§5━━━ Portals ━━━")

                for name, ep in self.store.entity_portals.items():
                    dest = ep.dest_host if ep.dest_type == "server" else f"{ep.dest_x:.0f},{ep.dest_y:.0f},{ep.dest_z:.0f}"
                    player.send_message(f"  §a⬡ §f{name} §7(entity → {dest})")

                for name, bp in self.store.block_portals.items():
                    dest = bp.dest_host if bp.dest_type == "server" else f"{bp.dest_x:.0f},{bp.dest_y:.0f},{bp.dest_z:.0f}"
                    player.send_message(f"  §b◈ §f{name} §7(block → {dest})")

                return True

            elif subcmd == "delete":
                if len(args) < 2:
                    player.send_message("§cUsage: /portal delete <name>")
                    return True

                portal_name = " ".join(args[1:])
                if self.store.remove_portal(portal_name):
                    player.send_message(f"§cPortal '{portal_name}' deleted.")
                else:
                    player.send_message(f"§cPortal '{portal_name}' not found.")
                return True

            else:
                player.send_message("§cUnknown subcommand. Use /portal, /portal reload, /portal list, /portal delete <name>")
                return True

        except Exception as e:
            self.logger.error(f"Command error: {e}")
            try:
                sender.send_message("§cAn error occurred. Check server logs.")
            except Exception:
                pass
            return True

    # ── Event Handlers ───────────────────────────────────────────────────

    @event_handler
    def on_player_interact_actor(self, ev: PlayerInteractActorEvent):
        """Handle player right-clicking an entity."""
        try:
            if self.entity_handler and self.entity_handler.handle_interact(ev.player, ev.actor):
                ev.cancel()
        except Exception as e:
            self.logger.error(f"Interact actor event error: {e}")

    @event_handler
    def on_player_join(self, ev: PlayerJoinEvent):
        """Handle player join for transfer loop protection."""
        try:
            if self.block_handler:
                self.block_handler.on_player_join(ev.player)
        except Exception as e:
            self.logger.error(f"Player join event error: {e}")

    @event_handler
    def on_player_quit(self, ev: PlayerQuitEvent):
        if self.block_handler:
            self.block_handler.on_player_quit(ev.player)

    @event_handler
    def on_player_teleport(self, ev: PlayerTeleportEvent):
        if self.block_handler:
            self.block_handler.on_player_teleport(ev.player, ev.to_location)

    @event_handler
    def on_actor_knockback(self, ev: ActorKnockbackEvent):
        """Handle player hitting an entity (left-click detection)."""
        try:
            source = getattr(ev, 'source', None)
            if source and self.entity_handler:
                self.entity_handler.handle_hit(source, ev.actor)
        except Exception as e:
            self.logger.error(f"Knockback event error: {e}")

    @event_handler
    def on_block_break(self, ev: BlockBreakEvent):
        """Protect portal frame blocks from being broken by non-ops.
        If an op breaks a frame block, auto-remove the portal."""
        try:
            if not self.store:
                return

            block = ev.block
            bx, by, bz = int(block.x), int(block.y), int(block.z)

            # Check if this block belongs to any portal frame
            for name, portal in list(self.store.block_portals.items()):
                for fb in portal.frame_blocks:
                    if fb[0] == bx and fb[1] == by and fb[2] == bz:
                        player = ev.player
                        if not player.is_op:
                            # Non-op: cancel the break
                            ev.cancel()
                            player.send_message("§cThis block is part of a portal and cannot be broken.")
                        else:
                            # Op: allow break and auto-remove the portal
                            self.store.remove_portal(name)
                            player.send_message(
                                f"§ePortal '§f{name}§e' has been removed because you broke its frame."
                            )
                            self.logger.info(
                                f"Portal '{name}' auto-removed — frame block broken by {player.name}"
                            )
                        return  # block found, no need to check further
        except Exception as e:
            self.logger.error(f"Block break event error: {e}")
