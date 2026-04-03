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
from Generated.nav.BfsBureau import BfsBureau
from Generated.nav.ClaudeGlobalBfs import ClaudeGlobalBfs
from Generated.nav.DialDijkstra import DialDijkstra
from Generated.nav.DirectionPicker import DirectionPicker
from Generated.nav.EgoBridgeBfs import EgoBridgeBfs
from Generated.nav.MyGlobalBfs import MyGlobalBfs
from Generated.nav.MyGlobalBfs2 import MyGlobalBfs2


class MyGlobalBfs:
    dist: list[int]  # (x,y) -> (x + 1) * 52 + (y + 1)

    @classmethod
    def init(cls):
        W, H = Map.W, Map.H
        cls.dist = [1000000] * 2704

        # 1-thick border around game area: ~2*(W+H+2) ops
        for i in range(H + 2):
            cls.dist[i] = 1000001                       # x=-1 column
            cls.dist[(W + 1) * 52 + i] = 1000001  # x=W column
        for x in range(1, W + 1):
            base = x * 52
            cls.dist[base] = 1000001                     # y=-1 row
            cls.dist[base + H + 1] = 1000001             # y=H row

    @classmethod
    def update(cls):
        tile_info = Map.tile_info
        _dist = cls.dist
        for pos in Map.nearby_tiles:
            ti = tile_info[pos.x][pos.y]
            idx = (pos.x + 1) * 52 + (pos.y + 1)

            if (
                ti.env != Environment.WALL
                and not (ti.has_building and ti.entity_type not in Constants.PASSABLE_SET)
            ):
                _dist[idx] = 1000000
            else:
                _dist[idx] = 1000001

    @classmethod
    def dists_from_pos(cls, pos: Position):
        dist = cls.dist[:]

        si = (pos.x + 1) * 52 + (pos.y + 1)
        dist[si] = 0

        frontier = [si]
        d = 1
        while frontier:
            nxt = []
            _a = nxt.append
            for idx in frontier:
                ni = idx + -1
                if dist[ni] == 1000000:
                    dist[ni] = d
                    _a(ni)
                ni = idx + 51
                if dist[ni] == 1000000:
                    dist[ni] = d
                    _a(ni)
                ni = idx + 52
                if dist[ni] == 1000000:
                    dist[ni] = d
                    _a(ni)
                ni = idx + 53
                if dist[ni] == 1000000:
                    dist[ni] = d
                    _a(ni)
                ni = idx + 1
                if dist[ni] == 1000000:
                    dist[ni] = d
                    _a(ni)
                ni = idx + -51
                if dist[ni] == 1000000:
                    dist[ni] = d
                    _a(ni)
                ni = idx + -52
                if dist[ni] == 1000000:
                    dist[ni] = d
                    _a(ni)
                ni = idx + -53
                if dist[ni] == 1000000:
                    dist[ni] = d
                    _a(ni)
            frontier = nxt
            d += 1

        result = [[0] * (Map.H + 1) for _ in range(Map.W + 1)]
        for x in range(Map.W + 1):
            row = result[x]
            base = (x + 1) * 52 + 1
            for y in range(Map.H + 1):
                v = dist[base + y]
                row[y] = 1000000 if v >= 1000000 else v
        return result