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
import traceback
from Awubot.Constants import Constants
from Awubot.Globals import Globals
from Awubot.Map import TileInfo, Map
from Awubot.MoveManager import MoveManager
from Awubot.Util import Util
from Awubot.build.Builder import BuilderState, Builder
from Awubot.core.Core import Core
from Awubot.debug.Profiler import Profiler
from Awubot.explore.Explore import Explore
from Awubot.nav.Pathfinder import Pathfinder
from Generated.MarketMaker import MarketMaker
from Generated.RobotPlayer import Entrypoint, Player
from Generated.Unit import Unit
from Generated.build.BuildManager import BuildManager
from Generated.build.OreExecutive import OreExecutive
from Generated.build.OrePositionPicker import OrePositionPicker
from Generated.build.RouteToCore import RouteToCore
from Generated.build.SuicideExecutor import SuicideExecutor
from Generated.debug.Debug import Color, Debug
from Generated.heal.HealExecutor import HealExecutor
from Generated.nav.ClaudeGlobalBfs import ClaudeGlobalBfs
from Generated.nav.DialDijkstra import DialDijkstra
from Generated.nav.DirectionPicker import DirectionPicker
from Generated.nav.EgoBridgeBfs import EgoBridgeBfs
from Generated.nav.MyGlobalBfs import MyGlobalBfs


class EgoBridgeBfs:
    # also unrolled

    @classmethod
    def find_bridge_route(cls, start: Position, core_pos_list: list[tuple[int, int]]):
        W, H = Map.W, Map.H
        WALL = Environment.WALL
        EMPTY = Environment.EMPTY

        tile_info = Map.tile_info
        PW = W + 2 * 3
        PH = H + 2 * 3

        blocked = [[True] * PH for _ in range(PW)]
        for x in range(W):
            col = tile_info[x]
            brow = blocked[x + 3]
            for y in range(H):
                ti = col[y]
                brow[y + 3] = (ti is not None) and (
                    ti.env != EMPTY or
                    (
                        ti.has_building and ti.entity_type != EntityType.MARKER and 
                        (
                            (not ti.easily_passable) or
                            (not ti.is_building_ally)
                        )
                    )
                )

        dist = [[1000000] * PH for _ in range(PW)]
        first_hop = [[None] * PH for _ in range(PW)]

        sx, sy = start.x + 3, start.y + 3
        dist[sx][sy] = 0

        core_set = set()
        for cx, cy in core_pos_list:
            core_set.add((cx + 3, cy + 3))

        # First hop: knight moves + diagonal jumps + straight jumps (all bridge-range offsets we care about)

        q = deque()

        nx, ny = sx +3, sy 
        if dist[nx][ny] == 1000000 and not blocked[nx][ny]:
            dist[nx][ny] = 1
            first_hop[nx][ny] = (nx - 3, ny - 3)
            if (nx, ny) in core_set:
                return 1, first_hop[nx][ny]
            q.append((nx, ny))
        nx, ny = sx -3, sy 
        if dist[nx][ny] == 1000000 and not blocked[nx][ny]:
            dist[nx][ny] = 1
            first_hop[nx][ny] = (nx - 3, ny - 3)
            if (nx, ny) in core_set:
                return 1, first_hop[nx][ny]
            q.append((nx, ny))
        nx, ny = sx , sy +3
        if dist[nx][ny] == 1000000 and not blocked[nx][ny]:
            dist[nx][ny] = 1
            first_hop[nx][ny] = (nx - 3, ny - 3)
            if (nx, ny) in core_set:
                return 1, first_hop[nx][ny]
            q.append((nx, ny))
        nx, ny = sx , sy -3
        if dist[nx][ny] == 1000000 and not blocked[nx][ny]:
            dist[nx][ny] = 1
            first_hop[nx][ny] = (nx - 3, ny - 3)
            if (nx, ny) in core_set:
                return 1, first_hop[nx][ny]
            q.append((nx, ny))
        nx, ny = sx +2, sy +2
        if dist[nx][ny] == 1000000 and not blocked[nx][ny]:
            dist[nx][ny] = 1
            first_hop[nx][ny] = (nx - 3, ny - 3)
            if (nx, ny) in core_set:
                return 1, first_hop[nx][ny]
            q.append((nx, ny))
        nx, ny = sx +2, sy -2
        if dist[nx][ny] == 1000000 and not blocked[nx][ny]:
            dist[nx][ny] = 1
            first_hop[nx][ny] = (nx - 3, ny - 3)
            if (nx, ny) in core_set:
                return 1, first_hop[nx][ny]
            q.append((nx, ny))
        nx, ny = sx -2, sy -2
        if dist[nx][ny] == 1000000 and not blocked[nx][ny]:
            dist[nx][ny] = 1
            first_hop[nx][ny] = (nx - 3, ny - 3)
            if (nx, ny) in core_set:
                return 1, first_hop[nx][ny]
            q.append((nx, ny))
        nx, ny = sx -2, sy +2
        if dist[nx][ny] == 1000000 and not blocked[nx][ny]:
            dist[nx][ny] = 1
            first_hop[nx][ny] = (nx - 3, ny - 3)
            if (nx, ny) in core_set:
                return 1, first_hop[nx][ny]
            q.append((nx, ny))
        nx, ny = sx +1, sy +2
        if dist[nx][ny] == 1000000 and not blocked[nx][ny]:
            dist[nx][ny] = 1
            first_hop[nx][ny] = (nx - 3, ny - 3)
            if (nx, ny) in core_set:
                return 1, first_hop[nx][ny]
            q.append((nx, ny))
        nx, ny = sx +2, sy +1
        if dist[nx][ny] == 1000000 and not blocked[nx][ny]:
            dist[nx][ny] = 1
            first_hop[nx][ny] = (nx - 3, ny - 3)
            if (nx, ny) in core_set:
                return 1, first_hop[nx][ny]
            q.append((nx, ny))
        nx, ny = sx +2, sy -1
        if dist[nx][ny] == 1000000 and not blocked[nx][ny]:
            dist[nx][ny] = 1
            first_hop[nx][ny] = (nx - 3, ny - 3)
            if (nx, ny) in core_set:
                return 1, first_hop[nx][ny]
            q.append((nx, ny))
        nx, ny = sx +1, sy -2
        if dist[nx][ny] == 1000000 and not blocked[nx][ny]:
            dist[nx][ny] = 1
            first_hop[nx][ny] = (nx - 3, ny - 3)
            if (nx, ny) in core_set:
                return 1, first_hop[nx][ny]
            q.append((nx, ny))
        nx, ny = sx -1, sy -2
        if dist[nx][ny] == 1000000 and not blocked[nx][ny]:
            dist[nx][ny] = 1
            first_hop[nx][ny] = (nx - 3, ny - 3)
            if (nx, ny) in core_set:
                return 1, first_hop[nx][ny]
            q.append((nx, ny))
        nx, ny = sx -2, sy -1
        if dist[nx][ny] == 1000000 and not blocked[nx][ny]:
            dist[nx][ny] = 1
            first_hop[nx][ny] = (nx - 3, ny - 3)
            if (nx, ny) in core_set:
                return 1, first_hop[nx][ny]
            q.append((nx, ny))
        nx, ny = sx -2, sy +1
        if dist[nx][ny] == 1000000 and not blocked[nx][ny]:
            dist[nx][ny] = 1
            first_hop[nx][ny] = (nx - 3, ny - 3)
            if (nx, ny) in core_set:
                return 1, first_hop[nx][ny]
            q.append((nx, ny))
        nx, ny = sx -1, sy +2
        if dist[nx][ny] == 1000000 and not blocked[nx][ny]:
            dist[nx][ny] = 1
            first_hop[nx][ny] = (nx - 3, ny - 3)
            if (nx, ny) in core_set:
                return 1, first_hop[nx][ny]
            q.append((nx, ny))

        # Subsequent hops: (±2,±2) diagonals + (±3,0) and (0,±3) straights

        while q:
            x, y = q.popleft()
            d = dist[x][y] + 1

            nx, ny = x +3, y 
            if dist[nx][ny] == 1000000 and not blocked[nx][ny]:
                dist[nx][ny] = d
                first_hop[nx][ny] = first_hop[x][y]

                if (nx, ny) in core_set:
                    return d, first_hop[nx][ny]

                q.append((nx, ny))
            nx, ny = x -3, y 
            if dist[nx][ny] == 1000000 and not blocked[nx][ny]:
                dist[nx][ny] = d
                first_hop[nx][ny] = first_hop[x][y]

                if (nx, ny) in core_set:
                    return d, first_hop[nx][ny]

                q.append((nx, ny))
            nx, ny = x , y +3
            if dist[nx][ny] == 1000000 and not blocked[nx][ny]:
                dist[nx][ny] = d
                first_hop[nx][ny] = first_hop[x][y]

                if (nx, ny) in core_set:
                    return d, first_hop[nx][ny]

                q.append((nx, ny))
            nx, ny = x , y -3
            if dist[nx][ny] == 1000000 and not blocked[nx][ny]:
                dist[nx][ny] = d
                first_hop[nx][ny] = first_hop[x][y]

                if (nx, ny) in core_set:
                    return d, first_hop[nx][ny]

                q.append((nx, ny))
            nx, ny = x +2, y +2
            if dist[nx][ny] == 1000000 and not blocked[nx][ny]:
                dist[nx][ny] = d
                first_hop[nx][ny] = first_hop[x][y]

                if (nx, ny) in core_set:
                    return d, first_hop[nx][ny]

                q.append((nx, ny))
            nx, ny = x +2, y -2
            if dist[nx][ny] == 1000000 and not blocked[nx][ny]:
                dist[nx][ny] = d
                first_hop[nx][ny] = first_hop[x][y]

                if (nx, ny) in core_set:
                    return d, first_hop[nx][ny]

                q.append((nx, ny))
            nx, ny = x -2, y -2
            if dist[nx][ny] == 1000000 and not blocked[nx][ny]:
                dist[nx][ny] = d
                first_hop[nx][ny] = first_hop[x][y]

                if (nx, ny) in core_set:
                    return d, first_hop[nx][ny]

                q.append((nx, ny))
            nx, ny = x -2, y +2
            if dist[nx][ny] == 1000000 and not blocked[nx][ny]:
                dist[nx][ny] = d
                first_hop[nx][ny] = first_hop[x][y]

                if (nx, ny) in core_set:
                    return d, first_hop[nx][ny]

                q.append((nx, ny))

        return 1000000, None