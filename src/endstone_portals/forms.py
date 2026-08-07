"""Operator setup forms and player-facing confirmation forms."""

from .particle_effects import PARTICLE_LIST, PARTICLE_DISPLAY_NAMES, normalize_dimension
from .frame_detector import detect_vertical_frame, detect_horizontal_frame




# Common border block options
BORDER_BLOCK_OPTIONS = [
    "minecraft:obsidian",
    "minecraft:end_portal_frame",
    "minecraft:stone",
    "minecraft:deepslate",
    "minecraft:crying_obsidian",
    "minecraft:purpur_block",
    "minecraft:prismarine",
    "minecraft:dark_prismarine",
    "minecraft:blackstone",
    "minecraft:gilded_blackstone",
    "minecraft:quartz_block",
    "minecraft:iron_block",
    "minecraft:gold_block",
    "minecraft:diamond_block",
    "minecraft:emerald_block",
    "minecraft:netherite_block",
    "minecraft:amethyst_block",
    "minecraft:glowstone",
    "minecraft:sea_lantern",
]

BORDER_BLOCK_DISPLAY = [
    "Obsidian",
    "End Portal Frame",
    "Stone",
    "Deepslate",
    "Crying Obsidian",
    "Purpur Block",
    "Prismarine",
    "Dark Prismarine",
    "Blackstone",
    "Gilded Blackstone",
    "Quartz Block",
    "Iron Block",
    "Gold Block",
    "Diamond Block",
    "Emerald Block",
    "Netherite Block",
    "Amethyst Block",
    "Glowstone",
    "Sea Lantern",
]

# Inner filler block preset options
# Index 0 is always "None" (no filler block — particles only)
INNER_BLOCK_OPTIONS = [
    None,                              # 0 — No fill block
    "minecraft:glass",
    "minecraft:tinted_glass",
    "minecraft:ice",
    "minecraft:blue_ice",
    "minecraft:packed_ice",
    "minecraft:amethyst_block",
    "minecraft:crying_obsidian",
    "minecraft:end_stone",
    "minecraft:end_stone_brick",
    "minecraft:nether_portal",
    "minecraft:end_portal",
    "minecraft:black_stained_glass",
    "minecraft:purple_stained_glass",
    "minecraft:magenta_stained_glass",
    "minecraft:cyan_stained_glass",
    "minecraft:lime_stained_glass",
    "minecraft:pink_stained_glass",
    "minecraft:red_stained_glass",
    "minecraft:blue_stained_glass",
    "minecraft:white_stained_glass",
    "minecraft:yellow_stained_glass",
    "minecraft:orange_stained_glass",
    "minecraft:green_stained_glass",
    "minecraft:brown_stained_glass",
    "minecraft:gray_stained_glass",
    "minecraft:light_gray_stained_glass",
    "minecraft:light_blue_stained_glass",
]

INNER_BLOCK_DISPLAY = [
    "None (Particles Only)",
    "Glass",
    "Tinted Glass",
    "Ice",
    "Blue Ice",
    "Packed Ice",
    "Amethyst Block",
    "Crying Obsidian",
    "End Stone",
    "End Stone Bricks",
    "Nether Portal (purple)",
    "End Portal",
    "Black Stained Glass",
    "Purple Stained Glass",
    "Magenta Stained Glass",
    "Cyan Stained Glass",
    "Lime Stained Glass",
    "Pink Stained Glass",
    "Red Stained Glass",
    "Blue Stained Glass",
    "White Stained Glass",
    "Yellow Stained Glass",
    "Orange Stained Glass",
    "Green Stained Glass",
    "Brown Stained Glass",
    "Gray Stained Glass",
    "Light Gray Stained Glass",
    "Light Blue Stained Glass",
]

DIMENSION_OPTIONS = ["overworld", "nether", "the_end"]
DIMENSION_DISPLAY = ["Overworld", "Nether", "The End"]



def show_main_menu(plugin, player, store):
    """Show the main portal management menu."""
    try:
        from endstone.form import ActionForm, Button

        portal_count = len(store.entity_portals) + len(store.block_portals)

        form = ActionForm(
            title="§l§5✦ Portal Manager ✦",
            content=f"§7Manage your server's portals.\n§8Active portals: §f{portal_count}",
            buttons=[
                Button(text="§a§lCreate Entity Portal\n§r§7Set up an entity as a portal"),
                Button(text="§b§lCreate Block Portal\n§r§7Build a portal with particles"),
                Button(text="§e§lManage Portals\n§r§7Edit or delete existing portals"),
            ],
            on_submit=lambda p, i: _on_main_menu(plugin, p, i, store),
        )
        player.send_form(form)
    except Exception as e:
        plugin.logger.error(f"Main menu error: {e}")
        player.send_message("§cFailed to open portal menu.")


def _on_main_menu(plugin, player, index, store):
    """Handle main menu button clicks."""
    if index == 0:
        _show_entity_portal_form(plugin, player, store)
    elif index == 1:
        _show_block_portal_step1(plugin, player, store)
    elif index == 2:
        _show_manage_portals(plugin, player, store)


# ── Entity Portal Creation ──────────────────────────────────────────────


def _show_entity_portal_form(plugin, player, store):
    """Show the entity portal creation form."""
    try:
        from endstone.form import ModalForm, TextInput, Dropdown, Toggle

        form = ModalForm(
            title="§l§aCreate Entity Portal",
            controls=[
                TextInput(
                    label="§fPortal Name",
                    placeholder="e.g. Hub NPC",
                ),
                TextInput(
                    label="§fEntity Type §7(leave empty to match by tag only)",
                    placeholder="e.g. minecraft:npc",
                ),
                TextInput(
                    label="§fEntity Scoreboard Tag §7(leave empty to match by type only)",
                    placeholder="e.g. portal_hub",
                ),
                Dropdown(
                    label="§fTrigger Type",
                    options=["Interact (Right-Click)", "Hit (Left-Click)", "Both"],
                ),
                Dropdown(
                    label="§fAction",
                    options=["Teleport Directly", "Show Confirmation Form"],
                ),
                Dropdown(
                    label="§fDestination Type",
                    options=["Location (Coordinates)", "Server Transfer"],
                ),
                TextInput(
                    label="§fCoordinates §7(x y z — for location destinations)",
                    placeholder="e.g. 100 64 200",
                ),
                Dropdown(
                    label="§fDimension §7(for location destinations)",
                    options=DIMENSION_DISPLAY,
                ),
                TextInput(
                    label="§fServer Address §7(host:port — for server transfers)",
                    placeholder="e.g. play.myserver.com:19132",
                ),
                TextInput(
                    label="§fWelcome Message §7(optional)",
                    placeholder="e.g. Welcome to the hub!",
                ),
            ],
            submit_button="§a§lCreate Portal",
            on_submit=lambda p, data: _on_entity_portal_submit(plugin, p, data, store),
        )
        player.send_form(form)
    except Exception as e:
        plugin.logger.error(f"Entity portal form error: {e}")
        player.send_message("§cFailed to open entity portal form.")


def _on_entity_portal_submit(plugin, player, data, store):
    """Process entity portal form submission."""
    try:
        import json
        values = json.loads(data)

        name = str(values[0]).strip()
        if not name:
            player.send_message("§cPortal name is required!")
            return

        if name in store.entity_portals or name in store.block_portals:
            player.send_message(f"§cA portal named '{name}' already exists!")
            return

        entity_type = str(values[1]).strip()
        entity_tag = str(values[2]).strip()

        if not entity_type and not entity_tag:
            player.send_message("§cYou must specify either an entity type or a tag!")
            return

        trigger_map = {0: "interact", 1: "hit", 2: "both"}
        trigger = trigger_map.get(values[3], "interact")

        action_map = {0: "teleport", 1: "form"}
        action = action_map.get(values[4], "teleport")

        dest_type_map = {0: "location", 1: "server"}
        dest_type = dest_type_map.get(values[5], "location")

        # Parse coordinates
        dest_x, dest_y, dest_z = 0.0, 64.0, 0.0
        coords_str = str(values[6]).strip()
        if coords_str and dest_type == "location":
            parts = coords_str.split()
            if len(parts) >= 3:
                try:
                    dest_x = float(parts[0])
                    dest_y = float(parts[1])
                    dest_z = float(parts[2])
                except ValueError:
                    player.send_message("§cInvalid coordinates! Use: x y z")
                    return
            else:
                player.send_message("§cCoordinates need 3 values: x y z")
                return

        dest_dim = DIMENSION_OPTIONS[values[7]] if values[7] < len(DIMENSION_OPTIONS) else "overworld"

        # Parse server address
        dest_host = ""
        dest_port = 19132
        server_str = str(values[8]).strip()
        if server_str and dest_type == "server":
            if ":" in server_str:
                parts = server_str.rsplit(":", 1)
                dest_host = parts[0]
                try:
                    dest_port = int(parts[1])
                except ValueError:
                    dest_port = 19132
            else:
                dest_host = server_str

            if not dest_host:
                player.send_message("§cServer address is required for server transfers!")
                return

        message = str(values[9]).strip()

        from .models import EntityPortal

        portal = EntityPortal(
            name=name,
            entity_type=entity_type,
            entity_tag=entity_tag,
            trigger=trigger,
            action=action,
            dest_type=dest_type,
            dest_x=dest_x,
            dest_y=dest_y,
            dest_z=dest_z,
            dest_dim=dest_dim,
            dest_host=dest_host,
            dest_port=dest_port,
            message=message,
        )

        store.add_entity_portal(portal)

        player.send_message(f"§a§lEntity portal '{name}' created!")
        player.send_message(f"§7Type: §f{entity_type or 'Any'} §7Tag: §f{entity_tag or 'None'}")
        if dest_type == "server":
            player.send_message(f"§7Destination: §f{dest_host}:{dest_port}")
        else:
            player.send_message(f"§7Destination: §f{dest_x:.0f}, {dest_y:.0f}, {dest_z:.0f} ({dest_dim})")

    except Exception as e:
        plugin.logger.error(f"Entity portal creation error: {e}")
        player.send_message("§cFailed to create entity portal. Check server logs.")


# ── Block Portal Creation (Multi-Step Wizard) ───────────────────────────


def _show_block_portal_step1(plugin, player, store):
    """Step 1: Configure block portal name, border type, particles, and inner fill."""
    try:
        from endstone.form import ModalForm, TextInput, Dropdown, Slider, Toggle

        controls = [
            TextInput(                          # 0
                label="§fPortal Name",
                placeholder="e.g. Spawn Portal",
            ),
            Dropdown(                           # 1
                label="§fBorder Block Type §7(preset list)",
                options=BORDER_BLOCK_DISPLAY,
            ),
            TextInput(                          # 2
                label="§fCustom Border Block ID §7(overrides dropdown if filled)",
                placeholder="e.g. minecraft:custom_block or mypack:frame",
            ),
            Slider(                             # 3
                label="§fParticle Render Distance (blocks)",
                min=4.0,
                max=48.0,
                step=4.0,
                default_value=16.0,
            ),
            Dropdown(                           # 4  ← NEW: inner block preset
                label="§fInner Fill Block §7(placed inside portal opening)",
                options=INNER_BLOCK_DISPLAY,
            ),
            TextInput(                          # 5  ← NEW: custom inner block
                label="§fCustom Inner Block ID §7(overrides preset if filled — supports any namespace)",
                placeholder="e.g. mypack:magic_glass or minecraft:barrier",
            ),
        ]

        # Add a Toggle for every available particle effect (indices 6 .. 6+N-1)
        for i, display_name in enumerate(PARTICLE_DISPLAY_NAMES):
            controls.append(
                Toggle(
                    label=f"§f{display_name}",
                    default_value=(i == 0),  # default: first particle on
                )
            )

        form = ModalForm(
            title="§l§bCreate Block Portal §7(1/2)",
            controls=controls,
            submit_button="§b§lScan for Frame →",
            on_submit=lambda p, data: _on_block_step1_submit(plugin, p, data, store),
        )
        player.send_form(form)
    except Exception as e:
        plugin.logger.error(f"Block portal step 1 error: {e}")
        player.send_message("§cFailed to open block portal form.")


def _on_block_step1_submit(plugin, player, data, store):
    """Process step 1 and scan for portal frame."""
    try:
        import json
        values = json.loads(data)

        name = str(values[0]).strip()
        if not name:
            player.send_message("§cPortal name is required!")
            return

        if name in store.entity_portals or name in store.block_portals:
            player.send_message(f"§cA portal named '{name}' already exists!")
            return

        border_idx = values[1] if isinstance(values[1], int) else 0
        border_block = BORDER_BLOCK_OPTIONS[border_idx] if border_idx < len(BORDER_BLOCK_OPTIONS) else BORDER_BLOCK_OPTIONS[0]

        # Custom border block ID overrides the dropdown if filled
        custom_border = str(values[2]).strip()
        if custom_border:
            if ":" not in custom_border:
                custom_border = f"minecraft:{custom_border}"
            border_block = custom_border

        radius = int(values[3]) if values[3] else 16

        # ── Inner fill block (index 4 = preset dropdown, index 5 = custom text) ──
        inner_idx = values[4] if isinstance(values[4], int) else 0
        inner_block_type = INNER_BLOCK_OPTIONS[inner_idx] if inner_idx < len(INNER_BLOCK_OPTIONS) else None

        custom_inner = str(values[5]).strip()
        if custom_inner:
            if ":" not in custom_inner:
                custom_inner = f"minecraft:{custom_inner}"
            inner_block_type = custom_inner

        # ── Collect selected particles from toggles (indices 6 .. 6+N-1) ──
        selected_particles = []
        for i in range(len(PARTICLE_LIST)):
            toggle_idx = 6 + i
            if toggle_idx < len(values) and values[toggle_idx]:
                selected_particles.append(PARTICLE_LIST[i])

        # Require at least one particle OR a fill block
        if not selected_particles and not inner_block_type:
            player.send_message("§cYou must enable at least one particle effect OR choose a fill block!")
            return

        # Scan for frame near the player
        player.send_message("§7Scanning for portal frame...")

        loc = player.location
        cx = int(loc.x)
        cy = int(loc.y)
        cz = int(loc.z)
        dim = loc.dimension

        # Try vertical frame first, then horizontal
        result = detect_vertical_frame(dim, cx, cy, cz, border_block)
        if not result:
            result = detect_horizontal_frame(dim, cx, cy, cz, border_block)

        if not result:
            player.send_message("§c§lNo valid portal frame found!")
            player.send_message(f"§7Build a frame using §f{border_block.replace('minecraft:', '')}§7 blocks,")
            player.send_message("§7then stand next to it and try again.")
            return

        frame_blocks = result["frame_blocks"]
        inner_blocks = result["inner_blocks"]
        orientation  = result.get("orientation", "north")

        player.send_message(f"§a§lFrame detected! §r§7{len(frame_blocks)} border blocks, {len(inner_blocks)} inner blocks")
        player.send_message(f"§7Orientation: §f{orientation} §7| Particles: §f{len(selected_particles)}")
        if inner_block_type:
            player.send_message(f"§7Fill block: §f{inner_block_type.replace('minecraft:', '')}")

        # Store temporary data and show step 2
        _show_block_portal_step2(
            plugin, player, store,
            name=name,
            border_block=border_block,
            particle=selected_particles,
            radius=radius,
            frame_blocks=frame_blocks,
            inner_blocks=inner_blocks,
            dimension=normalize_dimension(dim),
            inner_block_type=inner_block_type,
            inner_block_facing=orientation,
        )

    except Exception as e:
        plugin.logger.error(f"Block portal step 1 processing error: {e}")
        player.send_message("§cFailed to process portal frame. Check server logs.")


def _show_block_portal_step2(
    plugin, player, store,
    name, border_block, particle, radius,
    frame_blocks, inner_blocks, dimension,
    inner_block_type=None, inner_block_facing="north",
):
    """Step 2: Configure destination."""
    try:
        from endstone.form import ModalForm, TextInput, Dropdown, Slider

        form = ModalForm(
            title="§l§bCreate Block Portal §7(2/2)",
            controls=[
                Dropdown(
                    label="§fDestination Type",
                    options=["Location (Coordinates)", "Server Transfer"],
                ),
                TextInput(
                    label="§fCoordinates §7(x y z — for location destinations)",
                    placeholder="e.g. 100 64 200",
                ),
                Dropdown(
                    label="§fDestination Dimension §7(for location destinations)",
                    options=DIMENSION_DISPLAY,
                ),
                TextInput(
                    label="§fServer Address §7(host:port — for server transfers)",
                    placeholder="e.g. play.myserver.com:19132",
                ),
                Slider(
                    label="§fCooldown (seconds)",
                    min=1.0,
                    max=30.0,
                    step=1.0,
                    default_value=5.0,
                ),
                TextInput(
                    label="§fWelcome Message §7(optional)",
                    placeholder="e.g. Welcome to spawn!",
                ),
            ],
            submit_button="§a§lCreate Portal",
            on_submit=lambda p, data: _on_block_step2_submit(
                plugin, p, data, store,
                name, border_block, particle, radius,
                frame_blocks, inner_blocks, dimension,
                inner_block_type, inner_block_facing,
            ),
        )
        player.send_form(form)
    except Exception as e:
        plugin.logger.error(f"Block portal step 2 error: {e}")
        player.send_message("§cFailed to open destination form.")


def _on_block_step2_submit(
    plugin, player, data, store,
    name, border_block, particle, radius,
    frame_blocks, inner_blocks, dimension,
    inner_block_type=None, inner_block_facing="north",
):
    """Process step 2 and create the block portal."""
    try:
        import json
        values = json.loads(data)

        dest_type_map = {0: "location", 1: "server"}
        dest_type = dest_type_map.get(values[0], "location")

        # Parse coordinates
        dest_x, dest_y, dest_z = 0.0, 64.0, 0.0
        coords_str = str(values[1]).strip()
        if coords_str and dest_type == "location":
            parts = coords_str.split()
            if len(parts) >= 3:
                try:
                    dest_x = float(parts[0])
                    dest_y = float(parts[1])
                    dest_z = float(parts[2])
                except ValueError:
                    player.send_message("§cInvalid coordinates! Use: x y z")
                    return
            else:
                player.send_message("§cCoordinates need 3 values: x y z")
                return

        dest_dim = DIMENSION_OPTIONS[values[2]] if values[2] < len(DIMENSION_OPTIONS) else "overworld"

        # Parse server address
        dest_host = ""
        dest_port = 19132
        server_str = str(values[3]).strip()
        if server_str and dest_type == "server":
            if ":" in server_str:
                parts = server_str.rsplit(":", 1)
                dest_host = parts[0]
                try:
                    dest_port = int(parts[1])
                except ValueError:
                    dest_port = 19132
            else:
                dest_host = server_str

            if not dest_host:
                player.send_message("§cServer address is required for server transfers!")
                return

        cooldown = float(values[4]) if values[4] else 5.0
        message = str(values[5]).strip()

        from .models import BlockPortal

        portal = BlockPortal(
            name=name,
            frame_blocks=frame_blocks,
            inner_blocks=inner_blocks,
            border_block_type=border_block,
            particle_type=particle,
            particle_radius=radius,
            dest_type=dest_type,
            dest_x=dest_x,
            dest_y=dest_y,
            dest_z=dest_z,
            dest_dim=dest_dim,
            dest_host=dest_host,
            dest_port=dest_port,
            dimension=dimension,
            message=message,
            cooldown=cooldown,
            inner_block_type=inner_block_type,
            inner_block_facing=inner_block_facing,
        )

        store.add_block_portal(portal)

        # Place inner fill blocks in the world immediately after saving
        if inner_block_type:
            try:
                from .portal_handler import place_inner_blocks
                place_inner_blocks(plugin, player.location.dimension, portal)
            except Exception as e:
                plugin.logger.warning(f"Inner block placement failed: {e}")

        player.send_message(f"§a§lBlock portal '{name}' created!")
        player.send_message(f"§7Frame: §f{len(frame_blocks)} border blocks, {len(inner_blocks)} inner blocks")
        player.send_message(f"§7Orientation: §f{inner_block_facing}")
        if isinstance(particle, list) and particle:
            names = ", ".join(p.replace('minecraft:', '') for p in particle)
            player.send_message(f"§7Particles: §f{names}")
        if inner_block_type:
            player.send_message(f"§7Fill block: §f{inner_block_type.replace('minecraft:', '')}")
        if dest_type == "server":
            player.send_message(f"§7Destination: §f{dest_host}:{dest_port}")
        else:
            player.send_message(f"§7Destination: §f{dest_x:.0f}, {dest_y:.0f}, {dest_z:.0f} ({dest_dim})")
        player.send_message(f"§7Cooldown: §f{cooldown:.0f}s")

    except Exception as e:
        plugin.logger.error(f"Block portal creation error: {e}")
        player.send_message("§cFailed to create block portal. Check server logs.")


# ── Portal Management ──────────────────────────────────────────────────


def _show_manage_portals(plugin, player, store):
    """Show the portal management list."""
    try:
        from endstone.form import ActionForm, Button

        if not store.entity_portals and not store.block_portals:
            player.send_message("§7No portals configured yet.")
            return

        buttons = []
        portal_keys = []

        for name, ep in store.entity_portals.items():
            dest = ep.dest_host if ep.dest_type == "server" else f"{ep.dest_x:.0f}, {ep.dest_y:.0f}, {ep.dest_z:.0f}"
            buttons.append(Button(text=f"§a⬡ §f{name}\n§7Entity → {dest}"))
            portal_keys.append(("entity", name))

        for name, bp in store.block_portals.items():
            dest = bp.dest_host if bp.dest_type == "server" else f"{bp.dest_x:.0f}, {bp.dest_y:.0f}, {bp.dest_z:.0f}"
            buttons.append(Button(text=f"§b◈ §f{name}\n§7Block → {dest}"))
            portal_keys.append(("block", name))

        form = ActionForm(
            title="§l§eManage Portals",
            content=f"§7Select a portal to manage.\n§8Total: {len(buttons)} portals",
            buttons=buttons,
            on_submit=lambda p, i: _on_manage_select(plugin, p, i, store, portal_keys),
        )
        player.send_form(form)
    except Exception as e:
        plugin.logger.error(f"Manage portals error: {e}")
        player.send_message("§cFailed to open portal manager.")


def _on_manage_select(plugin, player, index, store, portal_keys):
    """Handle portal selection from the management list."""
    if index < 0 or index >= len(portal_keys):
        return

    portal_type, portal_name = portal_keys[index]
    _show_portal_actions(plugin, player, store, portal_type, portal_name)


def _show_portal_actions(plugin, player, store, portal_type, portal_name):
    """Show action options for a selected portal."""
    try:
        from endstone.form import ActionForm, Button

        # Build info string
        info = ""
        if portal_type == "entity" and portal_name in store.entity_portals:
            ep = store.entity_portals[portal_name]
            info = (
                f"§7Type: §aEntity Portal\n"
                f"§7Entity: §f{ep.entity_type or 'Any'}\n"
                f"§7Tag: §f{ep.entity_tag or 'None'}\n"
                f"§7Trigger: §f{ep.trigger}\n"
                f"§7Action: §f{ep.action}\n"
            )
            if ep.dest_type == "server":
                info += f"§7Dest: §f{ep.dest_host}:{ep.dest_port}"
            else:
                info += f"§7Dest: §f{ep.dest_x:.0f}, {ep.dest_y:.0f}, {ep.dest_z:.0f} ({ep.dest_dim})"
        elif portal_type == "block" and portal_name in store.block_portals:
            bp = store.block_portals[portal_name]
            if isinstance(bp.particle_type, list) and bp.particle_type:
                p_names = ", ".join(p.replace('minecraft:', '') for p in bp.particle_type)
            elif bp.particle_type:
                p_names = bp.particle_type.replace('minecraft:', '')
            else:
                p_names = "None"
            fill_name = bp.inner_block_type.replace('minecraft:', '') if bp.inner_block_type else "None"
            info = (
                f"§7Type: §bBlock Portal\n"
                f"§7Border: §f{bp.border_block_type.replace('minecraft:', '')}\n"
                f"§7Fill Block: §f{fill_name} §8(facing {bp.inner_block_facing})\n"
                f"§7Particles: §f{p_names}\n"
                f"§7Dim: §f{bp.dimension}\n"
                f"§7Cooldown: §f{bp.cooldown:.0f}s\n"
            )
            if bp.dest_type == "server":
                info += f"§7Dest: §f{bp.dest_host}:{bp.dest_port}"
            else:
                info += f"§7Dest: §f{bp.dest_x:.0f}, {bp.dest_y:.0f}, {bp.dest_z:.0f} ({bp.dest_dim})"

        form = ActionForm(
            title=f"§l§e{portal_name}",
            content=info,
            buttons=[
                Button(text="§e§lEdit Settings\n§r§7Modify destination, particles, etc."),
                Button(text="§c§lDelete Portal\n§r§7Remove this portal permanently"),
                Button(text="§7§lBack\n§r§7Return to portal list"),
            ],
            on_submit=lambda p, i: _on_portal_action(plugin, p, i, store, portal_name, portal_type),
        )
        player.send_form(form)
    except Exception as e:
        plugin.logger.error(f"Portal actions error: {e}")


def _on_portal_action(plugin, player, index, store, portal_name, portal_type):
    """Handle portal action selection."""
    if index == 0:
        # Edit settings
        if portal_type == "entity":
            _show_edit_entity_portal(plugin, player, store, portal_name)
        else:
            _show_edit_block_portal(plugin, player, store, portal_name)
    elif index == 1:
        # Delete — remove fill blocks first, then unregister
        portal = store.block_portals.get(portal_name)
        if portal and portal.inner_block_type:
            try:
                from .portal_handler import clear_inner_blocks
                # Resolve the dimension object for block placement
                dim_obj = _resolve_dimension(plugin, portal.dimension)
                if dim_obj:
                    clear_inner_blocks(plugin, dim_obj, portal)
            except Exception as e:
                plugin.logger.warning(f"Inner block cleanup failed for '{portal_name}': {e}")

        if store.remove_portal(portal_name):
            player.send_message(f"§c§lPortal '{portal_name}' deleted!")
        else:
            player.send_message(f"§cPortal '{portal_name}' not found.")
    elif index == 2:
        # Back
        _show_manage_portals(plugin, player, store)


def _show_edit_entity_portal(plugin, player, store, portal_name):
    """Show the pre-filled entity portal editing form."""
    try:
        from endstone.form import ModalForm, TextInput, Dropdown
        portal = store.entity_portals.get(portal_name)
        if not portal:
            player.send_message("§cPortal not found.")
            return

        trigger_map = {"interact": 0, "hit": 1, "both": 2}
        trigger_idx = trigger_map.get(portal.trigger, 0)

        action_map = {"teleport": 0, "form": 1}
        action_idx = action_map.get(portal.action, 0)

        dest_type_map = {"location": 0, "server": 1}
        dest_type_idx = dest_type_map.get(portal.dest_type, 0)

        coords_str = f"{portal.dest_x} {portal.dest_y} {portal.dest_z}"
        dim_idx = DIMENSION_OPTIONS.index(portal.dest_dim) if portal.dest_dim in DIMENSION_OPTIONS else 0
        server_str = f"{portal.dest_host}:{portal.dest_port}" if portal.dest_host else ""

        form = ModalForm(
            title=f"§l§eEdit: {portal_name}",
            controls=[
                TextInput(
                    label="§fPortal Name",
                    default_value=portal.name,
                ),
                TextInput(
                    label="§fEntity Type",
                    default_value=portal.entity_type,
                ),
                TextInput(
                    label="§fEntity Scoreboard Tag",
                    default_value=portal.entity_tag,
                ),
                Dropdown(
                    label="§fTrigger Type",
                    options=["Interact (Right-Click)", "Hit (Left-Click)", "Both"],
                    default_index=trigger_idx,
                ),
                Dropdown(
                    label="§fAction",
                    options=["Teleport Directly", "Show Confirmation Form"],
                    default_index=action_idx,
                ),
                Dropdown(
                    label="§fDestination Type",
                    options=["Location (Coordinates)", "Server Transfer"],
                    default_index=dest_type_idx,
                ),
                TextInput(
                    label="§fCoordinates (x y z)",
                    default_value=coords_str,
                ),
                Dropdown(
                    label="§fDimension",
                    options=DIMENSION_DISPLAY,
                    default_index=dim_idx,
                ),
                TextInput(
                    label="§fServer Address",
                    default_value=server_str,
                ),
                TextInput(
                    label="§fWelcome Message",
                    default_value=portal.message,
                ),
            ],
            submit_button="§a§lSave Changes",
            on_submit=lambda p, data: _on_edit_entity_portal_submit(plugin, p, data, store, portal_name),
        )
        player.send_form(form)
    except Exception as e:
        plugin.logger.error(f"Edit entity form error: {e}")


def _on_edit_entity_portal_submit(plugin, player, data, store, old_name):
    """Process editing submission for entity portals."""
    try:
        import json
        values = json.loads(data)

        new_name = str(values[0]).strip()
        if not new_name:
            player.send_message("§cPortal name is required!")
            return

        if new_name != old_name and (new_name in store.entity_portals or new_name in store.block_portals):
            player.send_message(f"§cA portal named '{new_name}' already exists!")
            return

        entity_type = str(values[1]).strip()
        entity_tag = str(values[2]).strip()

        if not entity_type and not entity_tag:
            player.send_message("§cYou must specify either an entity type or a tag!")
            return

        trigger_map = {0: "interact", 1: "hit", 2: "both"}
        trigger = trigger_map.get(values[3], "interact")

        action_map = {0: "teleport", 1: "form"}
        action = action_map.get(values[4], "teleport")

        dest_type_map = {0: "location", 1: "server"}
        dest_type = dest_type_map.get(values[5], "location")

        dest_x, dest_y, dest_z = 0.0, 64.0, 0.0
        coords_str = str(values[6]).strip()
        if coords_str and dest_type == "location":
            parts = coords_str.split()
            if len(parts) >= 3:
                try:
                    dest_x = float(parts[0])
                    dest_y = float(parts[1])
                    dest_z = float(parts[2])
                except ValueError:
                    player.send_message("§cInvalid coordinates! Use: x y z")
                    return

        dest_dim = DIMENSION_OPTIONS[values[7]] if values[7] < len(DIMENSION_OPTIONS) else "overworld"

        dest_host = ""
        dest_port = 19132
        server_str = str(values[8]).strip()
        if server_str and dest_type == "server":
            if ":" in server_str:
                parts = server_str.rsplit(":", 1)
                dest_host = parts[0]
                try:
                    dest_port = int(parts[1])
                except ValueError:
                    dest_port = 19132
            else:
                dest_host = server_str

        message = str(values[9]).strip()

        if new_name != old_name:
            store.remove_portal(old_name)

        from .models import EntityPortal
        portal = EntityPortal(
            name=new_name,
            entity_type=entity_type,
            entity_tag=entity_tag,
            trigger=trigger,
            action=action,
            dest_type=dest_type,
            dest_x=dest_x,
            dest_y=dest_y,
            dest_z=dest_z,
            dest_dim=dest_dim,
            dest_host=dest_host,
            dest_port=dest_port,
            message=message,
        )
        store.add_entity_portal(portal)
        player.send_message(f"§a§lPortal '{new_name}' updated successfully!")
    except Exception as e:
        plugin.logger.error(f"Edit entity submit error: {e}")


def _show_edit_block_portal(plugin, player, store, portal_name):
    """Show the pre-filled block portal editing form."""
    try:
        from endstone.form import ModalForm, TextInput, Dropdown, Slider, Toggle
        portal = store.block_portals.get(portal_name)
        if not portal:
            player.send_message("§cPortal not found.")
            return

        dest_type_map = {"location": 0, "server": 1}
        dest_type_idx = dest_type_map.get(portal.dest_type, 0)

        coords_str = f"{portal.dest_x} {portal.dest_y} {portal.dest_z}"
        dim_idx = DIMENSION_OPTIONS.index(portal.dest_dim) if portal.dest_dim in DIMENSION_OPTIONS else 0
        server_str = f"{portal.dest_host}:{portal.dest_port}" if portal.dest_host else ""

        try:
            inner_idx = INNER_BLOCK_OPTIONS.index(portal.inner_block_type)
        except ValueError:
            inner_idx = 0

        controls = [
            TextInput(
                label="§fPortal Name",
                default_value=portal.name,
            ),
            Dropdown(
                label="§fDestination Type",
                options=["Location (Coordinates)", "Server Transfer"],
                default_index=dest_type_idx,
            ),
            TextInput(
                label="§fCoordinates (x y z)",
                default_value=coords_str,
            ),
            Dropdown(
                label="§fDestination Dimension",
                options=DIMENSION_DISPLAY,
                default_index=dim_idx,
            ),
            TextInput(
                label="§fServer Address",
                default_value=server_str,
            ),
            Slider(
                label="§fCooldown (seconds)",
                min=1.0,
                max=30.0,
                step=1.0,
                default_value=portal.cooldown,
            ),
            TextInput(
                label="§fWelcome Message",
                default_value=portal.message,
            ),
            Slider(
                label="§fParticle Render Distance (blocks)",
                min=4.0,
                max=48.0,
                step=4.0,
                default_value=float(portal.particle_radius),
            ),
            Dropdown(
                label="§fInner Fill Block",
                options=INNER_BLOCK_DISPLAY,
                default_index=inner_idx,
            ),
            TextInput(
                label="§fCustom Inner Block ID",
                default_value=portal.inner_block_type if portal.inner_block_type not in INNER_BLOCK_OPTIONS else "",
            ),
        ]

        p_list = portal.particle_type if isinstance(portal.particle_type, list) else [portal.particle_type]
        for i, display_name in enumerate(PARTICLE_DISPLAY_NAMES):
            particle_id = PARTICLE_LIST[i]
            is_enabled = (particle_id in p_list)
            controls.append(
                Toggle(
                    label=f"§f{display_name}",
                    default_value=is_enabled,
                )
            )

        form = ModalForm(
            title=f"§l§eEdit: {portal_name}",
            controls=controls,
            submit_button="§a§lSave Changes",
            on_submit=lambda p, data: _on_edit_block_portal_submit(plugin, p, data, store, portal_name),
        )
        player.send_form(form)
    except Exception as e:
        plugin.logger.error(f"Edit block form error: {e}")


def _on_edit_block_portal_submit(plugin, player, data, store, old_name):
    """Process editing submission for block portals."""
    try:
        import json
        values = json.loads(data)

        portal = store.block_portals.get(old_name)
        if not portal:
            player.send_message("§cPortal not found.")
            return

        new_name = str(values[0]).strip()
        if not new_name:
            player.send_message("§cPortal name is required!")
            return

        if new_name != old_name and (new_name in store.entity_portals or new_name in store.block_portals):
            player.send_message(f"§cA portal named '{new_name}' already exists!")
            return

        dest_type_map = {0: "location", 1: "server"}
        dest_type = dest_type_map.get(values[1], "location")

        dest_x, dest_y, dest_z = 0.0, 64.0, 0.0
        coords_str = str(values[2]).strip()
        if coords_str and dest_type == "location":
            parts = coords_str.split()
            if len(parts) >= 3:
                try:
                    dest_x = float(parts[0])
                    dest_y = float(parts[1])
                    dest_z = float(parts[2])
                except ValueError:
                    player.send_message("§cInvalid coordinates! Use: x y z")
                    return

        dest_dim = DIMENSION_OPTIONS[values[3]] if values[3] < len(DIMENSION_OPTIONS) else "overworld"

        dest_host = ""
        dest_port = 19132
        server_str = str(values[4]).strip()
        if server_str and dest_type == "server":
            if ":" in server_str:
                parts = server_str.rsplit(":", 1)
                dest_host = parts[0]
                try:
                    dest_port = int(parts[1])
                except ValueError:
                    dest_port = 19132
            else:
                dest_host = server_str

        cooldown = float(values[5]) if values[5] else 5.0
        message = str(values[6]).strip()
        radius = int(values[7]) if values[7] else 16

        inner_idx = values[8] if isinstance(values[8], int) else 0
        new_inner_type = INNER_BLOCK_OPTIONS[inner_idx] if inner_idx < len(INNER_BLOCK_OPTIONS) else None

        custom_inner = str(values[9]).strip()
        if custom_inner:
            if ":" not in custom_inner:
                custom_inner = f"minecraft:{custom_inner}"
            new_inner_type = custom_inner

        selected_particles = []
        for i in range(len(PARTICLE_LIST)):
            toggle_idx = 10 + i
            if toggle_idx < len(values) and values[toggle_idx]:
                selected_particles.append(PARTICLE_LIST[i])

        if not selected_particles and not new_inner_type:
            player.send_message("§cYou must enable at least one particle effect OR choose a fill block!")
            return

        old_inner_type = portal.inner_block_type
        dim_obj = _resolve_dimension(plugin, portal.dimension)

        if dim_obj:
            from .portal_handler import place_inner_blocks, clear_inner_blocks
            if old_inner_type and old_inner_type != new_inner_type:
                try:
                    clear_inner_blocks(plugin, dim_obj, portal)
                except Exception as e:
                    plugin.logger.warning(f"Failed to clear old inner blocks: {e}")

        portal.name = new_name
        portal.dest_type = dest_type
        portal.dest_x = dest_x
        portal.dest_y = dest_y
        portal.dest_z = dest_z
        portal.dest_dim = dest_dim
        portal.dest_host = dest_host
        portal.dest_port = dest_port
        portal.cooldown = cooldown
        portal.message = message
        portal.particle_radius = radius
        portal.particle_type = selected_particles
        portal.inner_block_type = new_inner_type

        if new_name != old_name:
            store.remove_portal(old_name)

        store.add_block_portal(portal)

        if dim_obj and new_inner_type:
            try:
                place_inner_blocks(plugin, dim_obj, portal)
            except Exception as e:
                plugin.logger.warning(f"Failed to place new inner blocks: {e}")

        player.send_message(f"§a§lPortal '{new_name}' updated successfully!")
    except Exception as e:
        plugin.logger.error(f"Edit block submit error: {e}")


def _resolve_dimension(plugin, dim_name: str):
    """Resolve a dimension name to a dimension object via the server level."""
    try:
        dim_name = dim_name.lower().strip()
        level = plugin.server.level
        for dim in level.dimensions:
            name = getattr(dim, 'name', str(dim)).lower()
            if ":" in name:
                name = name.split(":")[-1]
            if name == dim_name or name.replace("the_", "") == dim_name.replace("the_", ""):
                return dim
    except Exception:
        pass
    return None
