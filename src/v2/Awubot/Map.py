from cambc import Team, EntityType, Direction, Position, ResourceType, Environment, GameConstants, GameError, Controller
import random
import heapq
import array
import time
import math
import sys
from collections import deque, defaultdict
from typing import NamedTuple
from enum import Enum
from Awubot.Constants import Constants
from Awubot.Core import Core
from Awubot.Globals import Globals, Cache
from Awubot.MoveManager import MoveManager
from Awubot.RobotPlayer import Entrypoint, Player
from Awubot.Util import Util
from Awubot.build.Builder import BuilderState, Builder
from Awubot.debug.Profiler import Profiler
from Awubot.explore.Explore import Explore
from Awubot.nav.Pathfinder import Pathfinder
from Generated.Unit import Unit
from Generated.build.BuildManager import BuildManager
from Generated.build.OreExecutive import OreExecutive
from Generated.build.OrePositionPicker import OrePositionPicker
from Generated.build.RouteToCore import RouteToCore
from Generated.debug.Debug import Color, Debug
from Generated.nav.ClaudeGlobalBfs import ClaudeGlobalBfs
from Generated.nav.DirectionPicker import DirectionPicker
from Generated.nav.EgoBridgeBfs import EgoBridgeBfs


# ---===
class LocalMask:
    RADIUS: int
    WIDTH: int      # actual data columns (2*RADIUS+1)
    HEIGHT: int     # actual data rows   (2*RADIUS+1)
    STRIDE: int     # WIDTH + 1 (includes padding column)

    FULL: int

    wall: int = 0
    titanium: int = 0
    axionite: int = 0

    @staticmethod
    def init():
        LocalMask.RADIUS = 4
        LocalMask.WIDTH = 2 * LocalMask.RADIUS + 1
        LocalMask.HEIGHT = LocalMask.WIDTH
        LocalMask.STRIDE = LocalMask.WIDTH + 1

        row_bits = (1 << LocalMask.WIDTH) - 1
        LocalMask.FULL = 0
        for row in range(LocalMask.HEIGHT):
            LocalMask.FULL |= row_bits << (row * LocalMask.STRIDE)

    @staticmethod
    def encode_index(dx, dy) -> int:
        return (dy + LocalMask.RADIUS) * LocalMask.STRIDE + (dx + LocalMask.RADIUS)

    @staticmethod
    def encode_bit(dx, dy) -> int:
        return 1 << LocalMask.encode_index(dx, dy)

    @classmethod
    def set_pos(cls, pos: Position) -> int:
        my_pos = Globals.ct.get_position()
        return cls.encode_bit(pos.x - my_pos.x, pos.y - my_pos.y)

    @staticmethod
    def expand8(mask: int) -> int:
        # does not handle impassibles
        wide: int = mask | (mask << 1) | (mask >> 1)
        return (wide | (wide << LocalMask.STRIDE) | (wide >> LocalMask.STRIDE)) & LocalMask.FULL

    @staticmethod
    def expand4(mask: int) -> int:
        # does not handle impassibles
        return (mask | (mask << 1) | (mask >> 1)
                | (mask << LocalMask.STRIDE) | (mask >> LocalMask.STRIDE)) & LocalMask.FULL

# ---===
    @staticmethod
    def decode_index(idx: int) -> tuple[int, int]:
        dx = (idx % LocalMask.STRIDE) - LocalMask.RADIUS
        dy = (idx // LocalMask.STRIDE) - LocalMask.RADIUS
        return dx, dy
# ===---

# ---===
    @staticmethod
    def debug_mask(mask: int):
        center: Position = Globals.ct.get_position()
        for i in range(LocalMask.STRIDE * LocalMask.HEIGHT):
            if mask & (1 << i):
                dx, dy = LocalMask.decode_index(i)
                Debug.dot(Position(center.x + dx, center.y + dy))
# ===---

# ---===
    @staticmethod
    def debug_string(mask: int) -> str:
        lines = []
        for row in range(LocalMask.HEIGHT):
            data = []
            for col in range(LocalMask.WIDTH):
                idx = row * LocalMask.STRIDE + col
                data.append('#' if mask & (1 << idx) else '.')
            pad_idx = row * LocalMask.STRIDE + LocalMask.WIDTH
            pad = '#' if mask & (1 << pad_idx) else '.'
            dy = row - LocalMask.RADIUS
            lines.append(f"{''.join(data)}|{pad}  dy={dy:+d}")
        return '\n'.join(lines)
# ===---
# ===---


# ---===
class MapMask:
    STRIDE: int
    FULL: int

    wall: int = 0
    titanium: int = 0
    axionite: int = 0

    @staticmethod
    def init():
        MapMask.STRIDE = Map.W + 1

        row_bits = (1 << Map.W) - 1
        MapMask.FULL = 0
        for row in range(Map.H):
            MapMask.FULL |= row_bits << (row * MapMask.STRIDE)

    @staticmethod
    def encode_index(pos: Position) -> int:
        return pos.y * MapMask.STRIDE + pos.x

    @staticmethod
    def encode_bit(pos: Position) -> int:
        return 1 << MapMask.encode_index(pos)

    @staticmethod
    def decode_index(idx: int) -> Position:
        return Position(idx % MapMask.STRIDE, idx // MapMask.STRIDE)

    @staticmethod
    def debug_mask(mask: int):
        for i in range(MapMask.STRIDE * Map.H):
            if mask & (1 << i):
                Debug.dot(MapMask.decode_index(i))

    @staticmethod
    def debug_string(mask: int) -> str:
        lines = []
        for row in range(Map.H):
            data = []
            for col in range(Map.W):
                idx = row * MapMask.STRIDE + col
                data.append('#' if mask & (1 << idx) else '.')
            pad_idx = row * MapMask.STRIDE + Map.W
            pad = '#' if mask & (1 << pad_idx) else '.'
            lines.append(f"{''.join(data)}|{pad}  y={row}")
        return '\n'.join(lines)
# ===---


class TileInfo:
    env: Environment
    round: int
    has_builder_bot: bool  # non-self builder bot
    has_building: bool  # non-marker building
    is_building_ally: bool
    easily_passable: bool  # (allied core)/road/conveyor/bridge/splitter
    entity_type: EntityType | None


# ---===
class Map:
    W: int = 0
    H: int = 0
    maxX: int = 0
    maxY: int = 0

    tile_info: list[list[TileInfo | None]] = []  # [x][y], 1 None buffer on bot sides

    @staticmethod
    def init():
        Map.W = Globals.ct.get_map_width()
        Map.H = Globals.ct.get_map_height()
        Map.maxX = Map.W - 1
        Map.maxY = Map.H - 1

        Profiler.start()
        Map.tile_info = [[None] * (Map.H+1) for _ in range(Map.W+1)]
        Profiler.end('tile_info init')

        MapMask.init()
        LocalMask.init()

    @staticmethod
    def fill_tile_info():
        ct = Globals.ct
        round = ct.get_current_round()

        for pos in ct.get_nearby_tiles(20):
            tile_env: Environment = ct.get_tile_env(pos)

            ti: TileInfo | None = Map.tile_info[pos.x][pos.y]
            if ti is None:
                ti = TileInfo()
                Map.tile_info[pos.x][pos.y] = ti

            ti.env = tile_env
            ti.round = round

            building_id: int | None = ct.get_tile_building_id(pos)
            builder_bot_id: int | None = ct.get_tile_builder_bot_id(pos)

            ti.has_building = building_id is not None and ct.get_entity_type(
                building_id) != EntityType.MARKER
            ti.has_builder_bot = builder_bot_id is not None and builder_bot_id != Globals.my_id
            ti.entity_type = ct.get_entity_type(
                building_id) if ti.has_building else None

            ti.easily_passable = False

            if building_id is not None:
                ti.is_building_ally = ct.get_team(
                    building_id) == Globals.my_team

                etype: EntityType = ct.get_entity_type(building_id)
                if (etype == EntityType.ROAD or
                        etype == EntityType.BRIDGE or
                        etype == EntityType.SPLITTER or
                        etype == EntityType.CONVEYOR or
                        etype == EntityType.ARMOURED_CONVEYOR or (
                            etype == EntityType.CORE
                            and ti.is_building_ally
                        )):
                    ti.easily_passable = True

    @staticmethod
    def fill():
        mypos: Position = Globals.ct.get_position()

        # reset local masks
        LocalMask.wall = 0
        LocalMask.titanium = 0
        LocalMask.axionite = 0

        pos: Position
        for pos in Globals.ct.get_nearby_tiles(20):
            tile_env: Environment = Globals.ct.get_tile_env(pos)
            dx: int = pos.x - mypos.x
            dy: int = pos.y - mypos.y
            global_bit: int = MapMask.encode_bit(pos)
            local_bit: int = LocalMask.encode_bit(dx, dy)

            if tile_env == Environment.WALL:
                MapMask.wall |= global_bit
                LocalMask.wall |= local_bit
            elif tile_env == Environment.ORE_TITANIUM:
                MapMask.titanium |= global_bit
                LocalMask.titanium |= local_bit
            elif tile_env == Environment.ORE_AXIONITE:
                MapMask.axionite |= global_bit
                LocalMask.axionite |= local_bit
            else:
                assert tile_env == Environment.EMPTY
# ===---
