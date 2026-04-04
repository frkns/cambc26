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
from Generated.bbot.RushTargeter import RushTargeter
from Generated.bbot.States import StateBuildHarvester, StateBuildHarvesterAx, StateAttackTransporter, StateRoute, StateMoveTo, StateBuildTurret
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



# for choosing build position

class AdjacentInfo:
    position: Position
    enemy_hadj: int  # enemy harvesters adjacent
    ally_hadj: int   # ally  "          "
    dist_enemy_core: int

    @staticmethod
    def is_better_than(a: AdjacentInfo, b: AdjacentInfo):
        if a.enemy_hadj != b.enemy_hadj:
            return a.enemy_hadj > b.enemy_hadj
        if a.ally_hadj != b.ally_hadj:
            return a.ally_hadj > b.ally_hadj
        return a.dist_enemy_core < b.dist_enemy_core


class HarvesterAdjacent:
    cand: list[AdjacentInfo]  # adjacent candidate build positions


    @classmethod
    def get_best_hijack_position(cls) -> Position | None:
        if not cls.cand:
            return None

        best = cls.cand[0]
        for c in cls.cand[1:]:
            if AdjacentInfo.is_better_than(c, best):
                best = c

        if best.enemy_hadj == 0:
            return None

        if not VisionTracker.me_is_canonical_ally(best.position):
            return None

        return best.position


    @classmethod
    def fill(cls):
        cls.cand = []
        tile_info = Map.tile_info

        for pos, x, y, idx, ti in Map.proc_nearby_tiles:
            if not ti.harvester_adjacent: 
                continue

            if ti.has_building:
                if not ti.is_building_ally:
                    continue
                if ti.entity_type != EntityType.ROAD:
                    continue

            info = AdjacentInfo()
            cls.cand.append(info)
            info.position = pos
            info.dist_enemy_core = Util.dist_sq(pos, Symmetry.enemy_core_pos)
            info.has_ally_road = ti.entity_type == EntityType.ROAD
            info.enemy_hadj = 0
            info.ally_hadj = 0


            nti = tile_info[x ][y -1]
            if nti is not None and nti.has_building and nti.entity_type == EntityType.HARVESTER:
                if nti.is_building_ally:
                    info.ally_hadj += 1
                else:
                    info.enemy_hadj += 1

            nti = tile_info[x +1][y ]
            if nti is not None and nti.has_building and nti.entity_type == EntityType.HARVESTER:
                if nti.is_building_ally:
                    info.ally_hadj += 1
                else:
                    info.enemy_hadj += 1

            nti = tile_info[x ][y +1]
            if nti is not None and nti.has_building and nti.entity_type == EntityType.HARVESTER:
                if nti.is_building_ally:
                    info.ally_hadj += 1
                else:
                    info.enemy_hadj += 1

            nti = tile_info[x -1][y ]
            if nti is not None and nti.has_building and nti.entity_type == EntityType.HARVESTER:
                if nti.is_building_ally:
                    info.ally_hadj += 1
                else:
                    info.enemy_hadj += 1
            
