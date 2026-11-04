# Endstone Portals — How to Use

> **Requirement:** You must be an **operator (OP)** to create, manage, or delete portals.  
> Players (non-ops) can walk through block portals and interact with entity portals, but cannot modify them.

---

## Quick Reference — Commands

| Command | What It Does |
|---|---|
| `/portal` | Opens the **Portal Manager** GUI menu |
| `/portal list` | Lists all portals with their destinations in chat |
| `/portal reload` | Reloads portal data from disk (hot-reload) |
| `/portal delete <name>` | Deletes a portal by name |

---

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
| **Action** | `Teleport Directly` — instant teleport, or `Show Confirmation Form` — asks the player first |
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
1. **Stand right next to your frame** (within 8 blocks).
2. Run `/portal` → **"Create Block Portal"**.
3. Fill out **Page 1**:

| Field | Description |
|---|---|
| **Portal Name** | A unique name (e.g. `Spawn Portal`) |
| **Border Block Type** | Pick from the dropdown (Obsidian, Diamond Block, etc.) |
| **Custom Block ID** | Overrides the dropdown. Type any block ID (e.g. `minecraft:custom_block`) |
| **Particle Render Distance** | How far away (in blocks) particles are visible. Range: 4–48, default: 16 |
| **Particle Toggles** | Turn on one or more particle effects. You must enable **at least one**. |

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

6. Click **"Create Portal"** — particles will start appearing and the portal is live!

> [!IMPORTANT]
> If the scan fails, you'll see **"No valid portal frame found!"** Make sure:
> - You built a **complete rectangular frame** (no gaps in the border)
> - The inside of the frame is **air** (empty)
> - You're **standing close** to the frame (within 8 blocks)
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
3. Click **"Delete Portal"** to remove it, or **"Back"** to return to the list.

### From Chat
- `/portal list` — Quick text list of all portals
- `/portal delete Hub NPC` — Delete by name directly

---

## How Block Portals Work for Players

1. A player walks into the inner area of a block portal.
2. The plugin detects them (checks every ~0.5 seconds).
3. They are teleported to the destination or transferred to another server.
4. A cooldown prevents re-use for the configured number of seconds (default: 5s).

### Server Transfer Protection
When a portal transfers a player to another server:
- The player is moved onto loaded, solid ground outside the full portal frame and every nearby portal before transfer.
- Transfer waits **3 seconds** after that move and checks the player's actual position again. If the move fails, no safe exit exists, or the player re-enters a portal, transfer is cancelled.
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
- **Use `/portal reload`** after manually editing the `portals.json` data file.
