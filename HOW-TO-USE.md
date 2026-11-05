# Endstone Portals 1.1.10 - How to use

[README](README.md) | [Portals 1.1.10 release](https://github.com/TheNINJALLO/endstone-portals/releases/tag/v1.1.10)

> **Requirement:** You must be an **operator (OP)** to create, manage, or delete portals.  
> Players (non-ops) can walk through block portals and interact with entity portals, but cannot modify them.

---

## Install and upgrade

Stop the server, back up the world and the active Portals data folder (normally `plugins/portals/`), and replace the old wheel with `endstone_portals-1.1.10-py3-none-any.whl`. Keep only one Portals wheel installed. Preserve `portals.json`, then restart; no definition reset is required.

The package requires Python 3.10+ and Endstone >=0.11.9,<0.12 with API 0.11. For the intended 26.60 setup, use Endstone 0.11.15 with BDS 1.26.60.6 and Python 3.11+. All 18 safety regression tests passed on Linux CI; live server compatibility and transfers still need the checks at the end of this guide.

For linked servers, update every server where arriving players may spawn in a block portal. Put destination spawn positions outside portal openings and provide loaded, solid exit ground outside each frame. The move-before-transfer safeguards below describe block portals; entity portals use interaction/confirmation and a separate transfer path.

## Quick Reference — Commands

| Command | What It Does |
|---|---|
| `/portal` | Opens the **Portal Manager** GUI menu |
| `/portal list` | Lists all portals with their destinations in chat |
| `/portal reload` | Reloads portal data from disk (hot-reload) |
| `/portal delete <name>` | Removes a definition by name; inspect any remaining fill blocks |

---

Commands are in-game only, using `portals.admin` (operator by default). Frame protection and management forms require OP.

## Portal Types

There are **two** types of portals you can create:

### 1. Entity Portals
Turn any mob or NPC into a portal. When a player interacts with (right-clicks) or hits (left-clicks) the entity, they get teleported.

### 2. Block Portals
Build a frame out of blocks (like obsidian, diamond blocks, etc.) and the plugin will detect it, fill it with particle effects, and teleport anyone who walks through.

---

## Creating an Entity Portal

1. Run `/portal` to open the Portal Manager menu.
2. Click **"Create Entity Portal"**.
3. Fill out the form:

| Field | Description |
|---|---|
| **Portal Name** | A unique name for this portal (e.g. `Hub NPC`) |
| **Entity Type** | The entity type to match, like `minecraft:npc`. Leave blank to match by tag only. |
| **Entity Scoreboard Tag** | A scoreboard tag on the entity, like `portal_hub`. Leave blank to match by type only. |
| **Trigger Type** | `Interact (Right-Click)`, `Hit (Left-Click)`, or `Both` |
| **Action** | `Teleport Directly` — activate without a confirmation form, or `Show Confirmation Form` — asks the player first |
| **Destination Type** | `Location` for same-server coordinates, or `Server Transfer` to send them to another server |
| **Coordinates** | `x y z` for location destinations (e.g. `100 64 200`) |
| **Dimension** | Which dimension: Overworld, Nether, or The End |
| **Server Address** | `host:port` for server transfers (e.g. `play.myserver.com:19132`) |
| **Welcome Message** | Optional message shown to the player after teleporting |

4. Click **"Create Portal"** — done!

> [!TIP]
> You must specify **at least** an entity type OR a scoreboard tag. You can use both for extra-precise matching (e.g. only NPCs that also have the tag `portal_hub`).

### How Entity Matching Works

- **Type only** — Every entity of that type acts as this portal.
- **Tag only** — Any entity with that scoreboard tag acts as this portal.
- **Both** — The entity must be the correct type AND have the tag.

### Setting Up the Entity In-Game

1. Spawn or place your entity (e.g. `/summon minecraft:npc`).
2. If using tag matching, tag it: `/tag @e[type=npc,c=1] add portal_hub`
3. Create the entity portal in `/portal` pointing to that type/tag.
4. Players can now interact with the entity to teleport!

---

## Creating a Block Portal

Block portal creation is a **two-step wizard**.

### Step 1 — Build the Frame First!
Before opening the form, **build a rectangular frame** out of the block type you plan to use. The frame can be:

- **Vertical** (like a nether portal) — stand next to it
- **Horizontal** (like an end portal) — stand on or near it

The frame needs a solid border of the chosen block with an empty inside (air blocks).

### Step 2 — Open the Form

1. **Stand right next to your frame**, with the complete frame inside the scan volume (up to 8 blocks in each direction).
2. Run `/portal` → **"Create Block Portal"**.
3. Fill out **Page 1**:

| Field | Description |
|---|---|
| **Portal Name** | A unique name (e.g. `Spawn Portal`) |
| **Border Block Type** | Pick from the dropdown (Obsidian, Diamond Block, etc.) |
| **Custom Border Block ID** | Overrides the dropdown. Use a block already registered on the server, including custom namespaces. |
| **Inner Fill Block** | None (Particles Only), or a block to place in the opening. Start with None for a walk-through portal. |
| **Custom Inner Block ID** | Overrides the fill preset; the block must already be registered by its pack. |
| **Particle Render Distance** | How far away (in blocks) particles are visible. Range: 4–48, default: 16 |
| **Particle Toggles** | Choose effects. Enable at least one particle **or** select an inner fill block; fill-only portals are allowed. |

4. Click **"Scan for Frame →"** — the plugin scans nearby blocks to detect your frame.
5. If the frame is found, **Page 2** opens automatically:

| Field | Description |
|---|---|
| **Destination Type** | `Location` or `Server Transfer` |
| **Coordinates** | `x y z` for location destinations |
| **Destination Dimension** | Overworld, Nether, or The End |
| **Server Address** | `host:port` for server transfers |
| **Cooldown** | Seconds between uses per player (1–30, default: 5) |
| **Welcome Message** | Optional message shown to the player |

6. Click **"Create Portal"**. The selected particles/fill are applied and the definition is saved. A solid fill block can obstruct entry; use None (Particles Only) while testing walk-through behavior. Vanilla portal fill blocks can also have their own game behavior, so verify those separately.

> [!IMPORTANT]
> If the scan fails, you'll see **"No valid portal frame found!"** Make sure:
> - You built a **complete rectangular frame** (no gaps in the border)
> - The inside of the frame is **air** (empty)
> - The complete frame fits within the scan range (up to 8 blocks in each direction from you)
> - You selected the **correct border block type** that matches what you built

---

## Available Particle Effects

You can pick **multiple** particles for a block portal — the plugin randomly cycles through them per block each tick. There are **40** particles available including:

| Category | Examples |
|---|---|
| **Classic** | Portal (Purple Swirl), Ender Chest, End Rod, Mob Portal |
| **Fire** | Flame, Blue Flame (Soul), Candle Flame |
| **Nature** | Cherry Leaves, Pale Oak Leaves, Snowflake, Crop Growth |
| **Water** | Water Drip, Lava Drip, Honey Drip, Cauldron Splash |
| **Combat** | Dragon Breath, Critical Hit, Totem of Undying |
| **Misc** | Redstone Dust, Smoke, Campfire Smoke, Sculk Soul, Sparkler |
| **1.21+** | Trial Spawner, Wind Explosion, Vault Connection, Eyeblossom, Creaking Heart |

> [!NOTE]
> Some particles like Enchanting Table, Critical Hit, Sparkler, Wind Explosion, and Trial Spawner are flagged as **"heavy"** — they spawn fewer instances per block to prevent lag.

---

## Managing Portals

### From the GUI

1. `/portal` → **"Manage Portals"**
2. Click any portal in the list to see its details (type, destination, particles, cooldown, etc.)
3. Click **Edit Settings** to update the definition, **Delete Portal** to remove it, or **Back** to return.

Entity editing includes the name, matching type/tag, trigger, confirmation, destination and welcome message. Block editing includes name, destination, cooldown, particle range/effects and inner fill. It keeps the stored frame geometry; to move or change the border, delete and recreate the block portal at the new frame.

GUI deletion attempts to clear matching inner-fill blocks before removing the definition; it leaves the physical border in place. The chat delete command removes the definition without that fill cleanup. Prefer the GUI for filled portals and inspect the world after deletion.

### From Chat

- `/portal list` — Quick text list of all portals
- `/portal delete Hub NPC` — Delete by name directly

---

## How Block Portals Work for Players

1. A player walks into the inner area of a block portal.
2. The plugin detects them (checks every ~0.5 seconds).
3. Local destinations teleport them. Server transfers first move them out of the portal and verify that move before the delayed transfer.
4. Reuse requires both leaving the portal area and waiting for the cooldown (default: 5s for local block portals; server transfers extend protection to at least 20s).

### Server Transfer Protection
When a portal transfers a player to another server:

- The player is moved onto loaded, solid ground outside the full portal frame and every nearby portal before transfer.
- Transfer waits **60 ticks (about 3 seconds at normal server speed)** after that move and checks the player's actual position again. If the move fails, no safe exit exists, or the player re-enters a portal, transfer is cancelled.
- Joining players receive a **20-second cooldown**, with repeated checks to move them outside portals while their login position settles.
- Players arriving inside a portal or remaining inside after use must leave the portal area before it can activate again. Cooldown expiry cannot send them back automatically.
- Disconnecting cancels pending transfers so reconnecting cannot inherit an old transfer.

---

## Frame Block Protection

Block portal frames are **protected**:

- **Non-ops** cannot break frame blocks — they'll see *"This block is part of a portal and cannot be broken."*
- **Ops** can break frame blocks — doing so **automatically deletes** the portal and notifies the op.

---

## Tips & Best Practices

- **Name portals clearly** — names like `Spawn Portal` or `PvP Arena NPC` make managing easier.
- **Use confirmation forms** for entity portals in busy areas to prevent accidental teleports.
- **Set cooldowns higher** (10–15s) for server-transfer portals to prevent spam.
- **Keep particle render distance reasonable** — 16 blocks is a good default. Going to 48 on many portals may affect performance.
- **Combine multiple particles** for cool effects — e.g. Cherry Leaves + End Rod for a fantasy look.
- **Prefer the GUI for edits.** For manual edits, stop the server, back up and edit the active data folder's `portals.json`, then start and check `/portal list`. `/portal reload` reloads saved definitions but is not a deletion/reset command; use the GUI or `/portal delete` to remove a portal.


## Troubleshooting

| Symptom | What to check |
|---|---|
| Transfer cancelled: no safe exit | Provide loaded, solid ground with headroom outside the entire frame and every nearby portal. Avoid water, lava, fire, damaging floors and floating exits. Step clear, wait for cooldown and enter again. |
| Transfer cancelled after moving | Do not walk back into a portal during the 60-tick delay. A cancelled move from a protection plugin also prevents transfer. Check the server log. |
| Portal does nothing just after joining | Login protection lasts at least 20 seconds. The plugin tries to move an arriving player clear; an occupied destination stays blocked until the player is outside. Cooldown expiry alone never rearms it. |
| Return trip immediately comes back | Check both servers have the updated plugin, keep arrival positions outside portal openings, and test the login safeguards on each side. |
| Frame scan fails | Keep the entire rectangular border within scan range, choose the exact border block, remove gaps and leave the opening empty before scanning. Separate nearby frames while creating a definition. |
| Filled portal cannot be entered | Test with None (Particles Only). Solid fill blocks are physical obstacles; the plugin does not make arbitrary blocks passable. |
| Remote server does not connect | Check the configured host and port, server availability and the client's access to that address. The three-second safety delay is not a connection-success guarantee. |
| Manual removal from JSON reappears | Remove the definition through the GUI or delete command. Reload merges saved entries into memory; it is not a way to purge definitions missing from the file. |

Entity portals have a separate three-second activation cooldown and defer a server transfer by 20 ticks (about one second). Do not expect their timing or activation to match block portals. A local entity teleport can still arrive inside a block portal, where the block handler's arrival protection applies.

## Upgrade and in-game checks

1. Confirm version 1.1.10 loads with the original definitions, then check `/portal list` and edit one definition through Manage Portals.
2. Test a local block portal, including a destination inside another portal. Stay in the destination past the cooldown: it must not bounce back until you exit and deliberately re-enter.
3. Test a block server-transfer portal in both directions. The player must move outside the full frame before transfer, then wait about three seconds. Re-enter during that delay: transfer must be cancelled.
4. Join/reconnect with a stored position inside a destination portal. The player should be moved clear when an exit is available and remain protected during login. Remove the safe exit temporarily: the player must not be transferred from inside the portal.
5. Test large/horizontal frames and adjacent portals; the exit must be outside all of them. Disconnect during a pending transfer and reconnect: the old transfer must not run.
6. With an ordinary player, verify portal use and protected frame blocks. With an operator, test GUI editing, fill changes and deletion, then inspect physical fill/border blocks.
7. Test entity type/tag matching, interact/hit modes, confirmation and both destination types separately.

For the automated safety suite, run `python -m unittest discover -s tests -v` from the repository. It checks movement verification, delayed transfer cancellation, arrivals, reconnects, dimensions and safe terrain with a simulated server/scheduler. Keep the live checks above distinct from those 18 automated regression tests.
