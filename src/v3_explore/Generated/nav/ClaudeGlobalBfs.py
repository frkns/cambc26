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
from Generated.nav.DirectionPicker import DirectionPicker
from Generated.nav.EgoBridgeBfs import EgoBridgeBfs


class ClaudeGlobalBfs:
    @classmethod
    def dists_from_pos(cls, pos: Position):
        W, H = Map.W, Map.H
        tile_info = Map.tile_info
        cur_round = Globals.ct.get_current_round()

        PH = H + 2
        INF = 1000000

        dist = [1000001] * ((W + 2) * PH)

        for x in range(W):
            col = tile_info[x]
            b = (x + 1) * PH + 1
            for y in range(H):
                ti = col[y]
                if ti is None or (
                    ti.env != Environment.WALL
                    and not (ti.has_bot and ti.round == cur_round)
                    and not (ti.has_building and ti.entity_type not in Constants.PASSABLE_SET)
                ):
                    # passable
                    dist[b + y] = 1000000

        si = (pos.x + 1) * PH + (pos.y + 1)
        dist[si] = 0

        _o0 = -1
        _o1 = PH-1
        _o2 = PH
        _o3 = PH+1
        _o4 = +1
        _o5 = -PH+1
        _o6 = -PH
        _o7 = -PH-1

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

        result = [[0] * (H + 1) for _ in range(W + 1)]
        for x in range(W + 1):
            row = result[x]
            base = (x + 1) * PH + 1
            for y in range(H + 1):
                v = dist[base + y]
                row[y] = 1000000 if v >= 1000000 else v
        return result