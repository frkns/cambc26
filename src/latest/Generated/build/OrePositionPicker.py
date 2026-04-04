# ---=== IMPORT
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
from itertools import chain
from Awubot.Globals import Globals
from Awubot.MoveManager import MoveManager
from Awubot.Util import Util
from Generated.bbot.Attacker import Attacker
from Generated.bbot.Builder import Builder
from Generated.bbot.HarvesterAdjacent import AdjacentInfo, HarvesterAdjacent
from Generated.bbot.HealExecutor import HealExecutor
from Generated.bbot.HealTargeter import HealTargetInfo, HealTargeter
from Generated.bbot.PatrolTargeter import PatrolTargeter
from Generated.bbot.RushTargeter import RushTargeter
from Generated.bbot.ShieldTargeter import ShieldTargetInfo, ShieldTargeter
from Generated.bbot.StalkTargeter import StalkTargeter
from Generated.bbot.States import StateBuildHarvester, StateBuildHarvesterAx, StateAttackTransporter, StateRoute, StateMoveTo, StateBuildTurret, StateBuildBarrier
from Generated.bbot.VisionTracker import TransporterInfo, ConnectManager, BotInfo, VisionTracker
from Generated.build.BuildManager import BuildManager
from Generated.build.OreExecutive import OreExecutive
from Generated.build.OrePositionPicker import OrePositionPicker
from Generated.build.RouteToCore import RouteToCore
from Generated.build.SuicideExecutor import SuicideExecutor
from Generated.comms.Comms import Comms
from Generated.comms.Marker import Marker
from Generated.comms.MarkerPositionPicker import MarkerPositionPicker
from Generated.Constants import Constants
from Generated.core.Core import Core
from Generated.core.CoreHistory import CoreHistory
from Generated.core.SpawnManager import SpawnManager
from Generated.debug.Debug import Color, Debug
from Generated.debug.Profiler import Profiler
from Generated.explore.Explore import Explore
from Generated.map.DarkForest import TreeNode, DarkForest
from Generated.map.Map import TileInfo, Map
from Generated.map.Symmetry import Sym, Symmetry
from Generated.MarketMaker import MarketMaker
from Generated.nav.BfsBureau import BfsBureau
from Generated.nav.Pathfinder import Pathfinder
from Generated.RobotPlayer import Entrypoint, Player
from Generated.sentinel.Sentinel import Sentinel
from Generated.sentinel.SentinelSupervisor import SentinelTargetInfo, SentinelSupervisor
from Generated.units.Unit import Unit
# ===--- IMPORT



class OrePositionPicker:
    class Candidate(NamedTuple):
        position: Position
        ti: TileInfo | None  # if None, it is outside map
        build_metric: int  # manhattan, but if directly on top, need to ~take a step back~

    cand: list[Candidate | None] = [None] * 4

    @classmethod
    def precompute(cls, ore_pos: Position):
        my_pos = Globals.my_pos
        me_x, me_y = my_pos.x, my_pos.y

        x, y = ore_pos.x, ore_pos.y


        nx, ny = x , y -1

        build_metric = max(abs(nx - me_x), abs(ny - me_y)) 
        if build_metric == 0:
            build_metric += 2

        cls.cand[0] = cls.Candidate(
            Position(nx, ny),
            Map.tile_info[nx][ny],
            build_metric,
        )

        nx, ny = x +1, y 

        build_metric = max(abs(nx - me_x), abs(ny - me_y)) 
        if build_metric == 0:
            build_metric += 2

        cls.cand[1] = cls.Candidate(
            Position(nx, ny),
            Map.tile_info[nx][ny],
            build_metric,
        )

        nx, ny = x , y +1

        build_metric = max(abs(nx - me_x), abs(ny - me_y)) 
        if build_metric == 0:
            build_metric += 2

        cls.cand[2] = cls.Candidate(
            Position(nx, ny),
            Map.tile_info[nx][ny],
            build_metric,
        )

        nx, ny = x -1, y 

        build_metric = max(abs(nx - me_x), abs(ny - me_y)) 
        if build_metric == 0:
            build_metric += 2

        cls.cand[3] = cls.Candidate(
            Position(nx, ny),
            Map.tile_info[nx][ny],
            build_metric,
        )

    @classmethod
    def is_better_than(cls, a: Candidate, b: Candidate) -> bool:
        # prio:
        # 1. on map
        # 2. empty
        # 3. no building
        # 4. has ally building AND is road
        # 5. no builder bot
        # 6. build metric
        # 7. arbitrary

        if a.ti is None and (b.ti is not None):
            return False
        if (a.ti is not None) and b.ti is None:
            return True

        EMPTY = Environment.EMPTY

        if a.ti.env == EMPTY and b.ti.env != EMPTY:
            return True
        if a.ti.env != EMPTY and b.ti.env == EMPTY:
            return False

        if a.ti.has_building and (not b.ti.has_building):
            return False
        if (not a.ti.has_building) and b.ti.has_building:
            return True

        if a.ti.has_building and b.ti.has_building:
            ROAD = EntityType.ROAD
            a_cond = a.ti.is_building_ally and a.ti.entity_type == ROAD
            b_cond = b.ti.is_building_ally and b.ti.entity_type == ROAD

            if a_cond and (not b_cond):
                return True
            if (not a_cond) and b_cond:
                return False

        if a.ti.has_bot and (not b.ti.has_bot):
            return False
        if (not a.ti.has_bot) and b.ti.has_bot:
            return True

        if a.build_metric != b.build_metric:
            return a.build_metric < b.build_metric

        return True  # arbitrary

    @classmethod
    def pick_best_candidate(cls, ore_pos: Position) -> Candidate:
        cls.precompute(ore_pos)

        best = cls.cand[3]
        if cls.is_better_than(cls.cand[2], best):
            best = cls.cand[2]
        if cls.is_better_than(cls.cand[1], best):
            best = cls.cand[1]
        if cls.is_better_than(cls.cand[0], best):
            best = cls.cand[0]

        return best










