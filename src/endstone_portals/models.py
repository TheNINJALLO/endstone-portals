"""Data models for entity portals and block portals."""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional, List


@dataclass
class EntityPortal:
    """A portal triggered by interacting with or hitting a specific entity."""

    name: str
    entity_type: str = ""  # e.g. "minecraft:npc" — empty means match by tag only
    entity_tag: str = ""  # scoreboard tag to match
    trigger: str = "interact"  # "interact", "hit", or "both"
    action: str = "teleport"  # "teleport" or "form" (show confirmation)
    dest_type: str = "location"  # "location" or "server"
    dest_x: float = 0.0
    dest_y: float = 64.0
    dest_z: float = 0.0
    dest_dim: str = "overworld"
    dest_host: str = ""
    dest_port: int = 19132
    message: str = ""

    def matches_actor(self, actor_type: str, actor_tags: list[str]) -> bool:
        """Check if an actor matches this portal's criteria."""
        type_match = True
        tag_match = True

        if self.entity_type:
            normalized = self.entity_type.lower().replace("minecraft:", "")
            actor_normalized = actor_type.lower().replace("minecraft:", "")
            type_match = normalized == actor_normalized

        if self.entity_tag:
            tag_match = self.entity_tag in actor_tags

        # Must match ALL specified criteria
        if self.entity_type and self.entity_tag:
            return type_match and tag_match
        elif self.entity_type:
            return type_match
        elif self.entity_tag:
            return tag_match
        return False


@dataclass
class BlockPortal:
    """A portal defined by a rectangular frame of blocks with particle effects."""

    name: str
    frame_blocks: list[list[int]] = field(default_factory=list)  # [[x,y,z], ...]
    inner_blocks: list[list[int]] = field(default_factory=list)  # [[x,y,z], ...]
    border_block_type: str = "minecraft:obsidian"
    particle_type: List[str] = field(default_factory=lambda: ["minecraft:basic_portal_particle"])
    particle_radius: int = 16  # blocks — distance at which particles become visible
    dest_type: str = "location"  # "location" or "server"
    dest_x: float = 0.0
    dest_y: float = 64.0
    dest_z: float = 0.0
    dest_dim: str = "overworld"
    dest_host: str = ""
    dest_port: int = 19132
    dimension: str = "overworld"  # the dimension this portal is in
    message: str = ""
    cooldown: float = 5.0  # seconds between uses
    # ── Inner-block fill ──────────────────────────────────────────────────
    inner_block_type: Optional[str] = None   # None → particles only; set → place this block inside
    inner_block_facing: str = "north"        # cardinal direction auto-detected from frame geometry

    def get_center(self) -> tuple[float, float, float]:
        """Calculate the geometric center of the inner blocks."""
        if not self.inner_blocks:
            if not self.frame_blocks:
                return (0.0, 0.0, 0.0)
            blocks = self.frame_blocks
        else:
            blocks = self.inner_blocks

        avg_x = sum(b[0] for b in blocks) / len(blocks)
        avg_y = sum(b[1] for b in blocks) / len(blocks)
        avg_z = sum(b[2] for b in blocks) / len(blocks)
        return (avg_x + 0.5, avg_y, avg_z + 0.5)

    def get_orientation(self) -> str:
        """
        Determine the cardinal orientation of this portal from its frame geometry.

        Returns one of: "north", "south", "east", "west", "up".

        Logic:
          - If all frame blocks share the same Z → vertical portal facing north/south.
            Pick north if Z <= median_z, south otherwise (arbitrary split — consumers
            can flip if needed, but the important thing is the axis).
          - If all frame blocks share the same X → vertical portal facing east/west.
          - Otherwise (horizontal frame, same Y) → facing up.
        """
        if not self.frame_blocks:
            return self.inner_block_facing

        z_vals = set(b[2] for b in self.frame_blocks)
        x_vals = set(b[0] for b in self.frame_blocks)
        y_vals = set(b[1] for b in self.frame_blocks)

        if len(z_vals) == 1:
            # All blocks share one Z → portal plane is perpendicular to the Z axis
            return "north"
        if len(x_vals) == 1:
            # All blocks share one X → portal plane is perpendicular to the X axis
            return "west"
        if len(y_vals) == 1:
            # Flat / horizontal frame
            return "up"

        # Mixed geometry — fall back to stored value
        return self.inner_block_facing

    def player_in_portal(self, px: float, py: float, pz: float) -> bool:
        """Check if a player position is inside any inner block (with a 0.3 block margin)."""
        margin = 0.3
        for block in self.inner_blocks:
            bx, by, bz = block
            if (bx - margin <= px < bx + 1 + margin and
                    by - margin <= py < by + 2 + margin and
                    bz - margin <= pz < bz + 1 + margin):
                return True
        return False

    def player_near(self, px: float, py: float, pz: float) -> bool:
        """Check if a player is within particle render distance."""
        cx, cy, cz = self.get_center()
        dist_sq = (px - cx) ** 2 + (py - cy) ** 2 + (pz - cz) ** 2
        return dist_sq <= self.particle_radius ** 2


class PortalStore:
    """Manages loading and saving portal data to JSON."""

    def __init__(self, data_folder: str):
        self.data_path = Path(data_folder) / "portals.json"
        self.entity_portals: dict[str, EntityPortal] = {}
        self.block_portals: dict[str, BlockPortal] = {}

    def load(self) -> None:
        """Load portal data from disk."""
        if not self.data_path.exists():
            return

        try:
            with open(self.data_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            for name, ep_data in data.get("entity_portals", {}).items():
                self.entity_portals[name] = EntityPortal(**ep_data)

            for name, bp_data in data.get("block_portals", {}).items():
                # Backward compat: old saves store particle_type as a string
                if "particle_type" in bp_data and isinstance(bp_data["particle_type"], str):
                    bp_data["particle_type"] = [bp_data["particle_type"]]
                # Backward compat: strip unknown keys so old saves don't crash
                known = {f.name for f in BlockPortal.__dataclass_fields__.values()}
                bp_data = {k: v for k, v in bp_data.items() if k in known}
                self.block_portals[name] = BlockPortal(**bp_data)
        except Exception:
            pass  # graceful fallback — start with empty data

    def save(self) -> None:
        """Save portal data to disk."""
        self.data_path.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "entity_portals": {
                name: asdict(ep) for name, ep in self.entity_portals.items()
            },
            "block_portals": {
                name: asdict(bp) for name, bp in self.block_portals.items()
            },
        }

        try:
            with open(self.data_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception:
            pass

    def add_entity_portal(self, portal: EntityPortal) -> None:
        """Add or update an entity portal."""
        self.entity_portals[portal.name] = portal
        self.save()

    def add_block_portal(self, portal: BlockPortal) -> None:
        """Add or update a block portal."""
        self.block_portals[portal.name] = portal
        self.save()

    def remove_portal(self, name: str) -> bool:
        """Remove a portal by name. Returns True if found."""
        if name in self.entity_portals:
            del self.entity_portals[name]
            self.save()
            return True
        if name in self.block_portals:
            del self.block_portals[name]
            self.save()
            return True
        return False

    def get_all_names(self) -> list[str]:
        """Get all portal names."""
        return list(self.entity_portals.keys()) + list(self.block_portals.keys())
