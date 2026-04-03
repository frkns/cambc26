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


class MyGlobalBfs:
    dist: list[int]  # (x,y) -> (x + 1) * (H + 2) + (y + 1)
    PH: int

    @classmethod
    def init(cls):
        W, H = Map.W, Map.H
        cls.PH = H + 2
        cls.dist = [1000000] * ((W + 2) * (cls.PH))  # assume passable to start

        # set OOB
        # Border columns: padded x=0 and padded x=W+1
        for i in range(cls.PH):
            cls.dist[i] = 1000001                    # padded x=0
            cls.dist[(W + 1) * cls.PH + i] = 1000001     # padded x=W+1

        # Border rows: padded y=0 and padded y=H+1
        for x in range(1, W + 1):
            base = x * cls.PH
            cls.dist[base] = 1000001                  # padded y=0
            cls.dist[base + H + 1] = 1000001          # padded y=H+1


    @classmethod
    def update(cls):
        tile_info = Map.tile_info
        for pos in Map.nearby_tiles:
            ti = tile_info[pos.x][pos.y]
            idx = (pos.x + 1) * cls.PH + (pos.y + 1)

            # ti cannot possibly be None
            if (
                ti.env != Environment.WALL
                # and not (ti.has_bot and ti.round == cur_round)
                and not (ti.has_building and ti.entity_type not in Constants.PASSABLE_SET)
            ):
                # passable
                cls.dist[idx] = 1000000
            else:
                cls.dist[idx] = 1000001


    @classmethod
    def dists_from_pos(cls, pos: Position):
        dist = cls.dist[:]

        _o0 = -1
        _o1 = cls.PH-1
        _o2 = cls.PH
        _o3 = cls.PH+1
        _o4 = +1
        _o5 = -cls.PH+1
        _o6 = -cls.PH
        _o7 = -cls.PH-1


        si = (pos.x + 1) * cls.PH + (pos.y + 1)
        dist[si] = 0

        frontier = [si]
        d = 1
        while frontier:
            nxt = []
            _a = nxt.append
            for idx in frontier:
                ni = idx + _o0
                if dist[ni] == 1000000:
                    dist[ni] = d
                    _a(ni)
                ni = idx + _o1
                if dist[ni] == 1000000:
                    dist[ni] = d
                    _a(ni)
                ni = idx + _o2
                if dist[ni] == 1000000:
                    dist[ni] = d
                    _a(ni)
                ni = idx + _o3
                if dist[ni] == 1000000:
                    dist[ni] = d
                    _a(ni)
                ni = idx + _o4
                if dist[ni] == 1000000:
                    dist[ni] = d
                    _a(ni)
                ni = idx + _o5
                if dist[ni] == 1000000:
                    dist[ni] = d
                    _a(ni)
                ni = idx + _o6
                if dist[ni] == 1000000:
                    dist[ni] = d
                    _a(ni)
                ni = idx + _o7
                if dist[ni] == 1000000:
                    dist[ni] = d
                    _a(ni)
            frontier = nxt
            d += 1

        Profiler.start()
        result = [[0] * (Map.H + 1) for _ in range(Map.W + 1)]
        for x in range(Map.W + 1):
            row = result[x]
            base = (x + 1) * cls.PH + 1
            for y in range(Map.H + 1):
                v = dist[base + y]
                row[y] = 1000000 if v >= 1000000 else v
        Profiler.end("results_comp")

        return result