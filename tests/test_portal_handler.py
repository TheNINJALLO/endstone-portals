"""Portal-loop regressions using a deterministic scheduler and a flat test world.

Run without an Endstone server: python -m unittest discover -s tests -v
"""

import heapq
import importlib
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import Mock, patch


# Load the pure Python handlers without importing the Endstone plugin entry point.
package = types.ModuleType("_portal_tests")
package.__path__ = [str(Path(__file__).resolve().parents[1] / "src" / "endstone_portals")]
sys.modules[package.__name__] = package
handler_module = importlib.import_module("_portal_tests.portal_handler")
BlockPortal = importlib.import_module("_portal_tests.models").BlockPortal


class Location:
    def __init__(self, dimension, x, y, z, pitch=0.0, yaw=0.0):
        self.dimension = dimension
        self.x, self.y, self.z = x, y, z
        self.pitch, self.yaw = pitch, yaw


class Dimension:
    name = "minecraft:overworld"

    def __init__(self):
        self.loaded = True
        self.floor = "minecraft:stone"
        self.blocks = {}

    def get_block_at(self, x, y, z):
        if not self.loaded:
            return None
        return types.SimpleNamespace(type=self.blocks.get(
            (x, y, z), self.floor if y <= 63 else "minecraft:air",
        ))

    def get_highest_block_y_at(self, x, z):
        return 63


class Scheduler:
    def __init__(self):
        self.tick = 0
        self.queue = []
        self.sequence = 0
        self.cancelled = set()

    def run_task(self, plugin, callback, delay=0, period=0):
        self.sequence += 1
        heapq.heappush(self.queue, (self.tick + delay, self.sequence, callback, period))
        return types.SimpleNamespace(task_id=self.sequence)

    def cancel_task(self, task_id):
        self.cancelled.add(task_id)

    def advance(self, ticks):
        until = self.tick + ticks
        while self.queue and self.queue[0][0] <= until:
            self.tick, sequence, callback, period = heapq.heappop(self.queue)
            if sequence in self.cancelled:
                continue
            callback()
            if period and sequence not in self.cancelled:
                heapq.heappush(self.queue, (self.tick + period, sequence, callback, period))
        self.tick = until


class Player:
    name = "ReturningPlayer"

    def __init__(self, dimension, scheduler):
        self.location = Location(dimension, 10.5, 64.0, 10.5, 12.0, 34.0)
        self.scheduler = scheduler
        self.messages = []
        self.events = []
        self.teleport_ok = True
        self.teleport_moves = True
        self.teleport_hook = None

    def send_message(self, message):
        self.messages.append(message)

    def teleport(self, location):
        self.events.append(("teleport", self.scheduler.tick, location))
        if self.teleport_ok and self.teleport_moves:
            if self.teleport_hook:
                self.teleport_hook(self, location)
            self.location = location
        return self.teleport_ok

    def transfer(self, host, port):
        self.events.append(("transfer", self.scheduler.tick, self.location, host, port))


class PortalSafetyTests(unittest.TestCase):
    def setUp(self):
        self.scheduler = Scheduler()
        self.dimension = Dimension()
        self.player = Player(self.dimension, self.scheduler)
        self.server = types.SimpleNamespace(
            scheduler=self.scheduler, online_players=[self.player],
            get_player=lambda name: next((p for p in self.server.online_players if p.name == name), None),
        )
        self.plugin = types.SimpleNamespace(server=self.server, logger=Mock())
        # The previous center + 3 offset is still inside this horizontal portal.
        self.portal = BlockPortal(
            name="Large portal", inner_blocks=[[x, 64, z] for x in range(21) for z in range(21)],
            frame_blocks=[[-1, 64, -1], [21, 64, 21]],
            dest_type="server", dest_host="destination.example", dest_port=19132,
        )
        self.store = types.SimpleNamespace(block_portals={self.portal.name: self.portal})
        self.handler = handler_module.BlockPortalHandler(self.plugin, self.store)
        self.level_patch = patch.dict(sys.modules, {
            "endstone.level": types.SimpleNamespace(Location=Location),
        })
        self.level_patch.start()
        self.addCleanup(self.level_patch.stop)
        self.clock_patch = patch.object(handler_module.time, "time", lambda: 1000 + self.scheduler.tick / 20)
        self.clock_patch.start()
        self.addCleanup(self.clock_patch.stop)

    def transfers(self, player=None):
        return [e for e in (player or self.player).events if e[0] == "transfer"]

    def test_large_portal_moves_before_transfer_and_waits_three_seconds(self):
        cx, cy, cz = self.portal.get_center()
        self.assertTrue(self.portal.player_in_portal(cx + 3, cy, cz + 3))
        self.handler._transfer_to_server(self.player, self.portal)
        self.assertFalse(self.player.events)
        self.scheduler.advance(1)
        self.assertIsNone(self.handler._portal_at(self.player.location))
        loc = self.player.location
        self.assertFalse(-1.3 <= loc.x < 22.3 and -1.3 <= loc.z < 22.3)
        self.assertEqual((self.player.location.pitch, self.player.location.yaw), (12.0, 34.0))
        self.scheduler.advance(59)
        self.assertFalse(self.transfers())
        self.scheduler.advance(1)
        self.assertEqual(len(self.transfers()), 1)
        self.assertIsNone(self.handler._portal_at(self.transfers()[0][2]))

    def test_exit_does_not_land_in_a_neighbouring_portal(self):
        neighbour = BlockPortal(name="Neighbour", inner_blocks=[
            [x, 64, z] for x in range(-6, 1) for z in range(7, 15)
        ])
        self.store.block_portals[neighbour.name] = neighbour
        self.handler._transfer_to_server(self.player, self.portal)
        self.scheduler.advance(61)
        self.assertEqual(len(self.transfers()), 1)
        self.assertIsNone(self.handler._portal_at(self.player.location))

    def test_cancelled_teleport_cannot_transfer(self):
        self.player.teleport_ok = False
        self.handler._transfer_to_server(self.player, self.portal)
        self.scheduler.advance(100)
        self.assertFalse(self.transfers())
        self.assertNotIn(self.player.name, self.handler._pending_transfers)

    def test_reported_success_without_position_change_cannot_transfer(self):
        self.player.teleport_moves = False
        self.handler._transfer_to_server(self.player, self.portal)
        self.scheduler.advance(100)
        self.assertFalse(self.transfers())

    def test_unloaded_terrain_cannot_transfer_using_a_guessed_heightmap(self):
        self.dimension.loaded = False
        self.handler._transfer_to_server(self.player, self.portal)
        self.scheduler.advance(100)
        self.assertFalse(self.player.events)
        self.assertNotIn(self.player.name, self.handler._pending_transfers)

    def test_no_solid_floor_or_hazardous_floor_cannot_transfer(self):
        for floor in ("minecraft:air", "minecraft:lava", "minecraft:cactus", "minecraft:magma"):
            with self.subTest(floor=floor):
                self.dimension.floor = floor
                self.handler._transfer_to_server(self.player, self.portal)
                self.scheduler.advance(100)
                self.assertFalse(self.player.events)

    def test_reentry_during_transfer_delay_cancels_transfer(self):
        self.handler._transfer_to_server(self.player, self.portal)
        self.scheduler.advance(1)
        self.player.location = Location(self.dimension, 10.5, 64, 10.5)
        self.scheduler.advance(60)
        self.assertFalse(self.transfers())
        self.assertIn(self.player.name, self.handler._must_exit)

    def test_duplicate_trigger_schedules_only_one_transfer(self):
        self.handler._transfer_to_server(self.player, self.portal)
        self.handler._transfer_to_server(self.player, self.portal)
        self.scheduler.advance(61)
        self.assertEqual(len(self.transfers()), 1)

    def test_disconnect_and_rejoin_cannot_inherit_pending_transfer(self):
        self.handler._transfer_to_server(self.player, self.portal)
        self.scheduler.advance(1)
        self.handler.on_player_quit(self.player)
        replacement = Player(self.dimension, self.scheduler)
        self.server.online_players = [replacement]
        self.handler.on_player_join(replacement)
        self.scheduler.advance(100)
        self.assertFalse(self.transfers(replacement))
        self.assertIsNone(self.handler._portal_at(replacement.location))

    def test_join_moves_out_on_first_tick_without_transferring(self):
        self.handler.on_player_join(self.player)
        self.scheduler.advance(1)
        self.assertIsNone(self.handler._portal_at(self.player.location))
        self.scheduler.advance(600)
        self.handler._tick()
        self.assertFalse(self.transfers())

    def test_join_safety_failure_stays_blocked_after_cooldown_expires(self):
        self.dimension.loaded = False
        self.handler.on_player_join(self.player)
        self.scheduler.advance(1000)
        for _ in range(3):
            self.handler._tick()
        self.scheduler.advance(100)
        self.assertFalse(self.player.events)
        self.assertIn(self.player.name, self.handler._must_exit)

    def test_late_login_restore_is_moved_out_during_join_protection(self):
        self.handler.on_player_join(self.player)
        self.scheduler.advance(100)
        self.player.location = Location(self.dimension, 10.5, 64, 10.5)
        self.handler._tick()
        self.assertIsNone(self.handler._portal_at(self.player.location))
        self.assertFalse(self.transfers())

    def test_teleport_arrival_after_join_grace_cannot_bounce_back(self):
        self.handler.on_player_join(self.player)
        self.scheduler.advance(500)
        self.handler._tick()
        arrival = Location(self.dimension, 10.5, 64, 10.5)
        self.handler.on_player_teleport(self.player, arrival)
        self.player.location = arrival
        for _ in range(3):
            self.handler._tick()
        self.scheduler.advance(100)
        self.assertFalse(self.transfers())

    def test_failed_use_requires_exit_before_portal_can_be_used_again(self):
        self.player.teleport_ok = False
        self.handler._tick()
        self.scheduler.advance(1000)
        self.handler._tick()
        self.assertEqual(len(self.player.events), 1)
        self.player.teleport_ok = True
        self.player.location = Location(self.dimension, -10, 64, -10)
        self.handler._tick()
        self.player.location = Location(self.dimension, 10.5, 64, 10.5)
        self.handler._tick()
        self.scheduler.advance(61)
        self.assertEqual(len(self.transfers()), 1)

    def test_local_portal_landing_does_not_loop_after_cooldown(self):
        self.portal.dest_type = "location"
        self.portal.dest_x, self.portal.dest_y, self.portal.dest_z = 10.5, 64, 10.5
        self.server.level = types.SimpleNamespace(dimensions=[self.dimension])
        self.player.teleport_hook = self.handler.on_player_teleport
        self.handler._tick()
        self.scheduler.advance(1)
        self.assertEqual(len(self.player.events), 1)
        self.scheduler.advance(1000)
        self.handler._tick()
        self.scheduler.advance(100)
        self.assertEqual(len(self.player.events), 1)

    def test_stop_invalidates_pending_transfer(self):
        self.handler._transfer_to_server(self.player, self.portal)
        self.scheduler.advance(1)
        self.handler.stop()
        self.scheduler.advance(100)
        self.assertFalse(self.transfers())

    def test_hot_enable_protects_already_online_players(self):
        self.handler.start()
        self.scheduler.advance(600)
        self.assertIsNone(self.handler._portal_at(self.player.location))
        self.assertFalse(self.transfers())

    def test_portal_in_another_dimension_does_not_block_a_safe_exit(self):
        self.store.block_portals["Nether"] = BlockPortal(
            name="Nether", dimension="nether",
            inner_blocks=[[x, 64, z] for x in range(-6, 1) for z in range(7, 15)],
        )
        self.handler._transfer_to_server(self.player, self.portal)
        self.scheduler.advance(61)
        self.assertEqual(len(self.transfers()), 1)


if __name__ == "__main__":
    unittest.main()
