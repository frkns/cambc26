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
from Generated.bbot.ShieldTargeterExecutor import ShieldTargetInfo, ShieldTargeterExecutor
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

class ShieldTargetInfo:
    position: Position
    harvester_adjacent: bool
    dist_ally_core: int

    @staticmethod
    def is_better_than(a: ShieldTargetInfo, b: ShieldTargetInfo):
        if a.harvester_adjacent != b.harvester_adjacent:
            return a.harvester_adjacent > b.harvester_adjacent
        return a.dist_ally_core < b.dist_ally_core


class ShieldTargeterExecutor:
    cand: list[ShieldTargetInfo] = []# adjacent candidate build positions


    @classmethod
    def execute_shield_attempt(cls) -> Position | None:
        if not cls.cand:
            return None
        
        if MarketMaker.est_income < 5:
            return None
        
        if not BuildManager.can_afford_bridge():
            return None

        best = cls.cand[0]
        for c in cls.cand[1:]:
            if ShieldTargetInfo.is_better_than(c, best):
                best = c

        if BuildManager.can_build_road(best.position):
            BuildManager.build_road(best.position)

    @classmethod
    def fill(cls):
        cls.cand = []
        tile_info = Map.tile_info

        for pos, x, y, idx, ti in Map.proc_nearby_tiles:
            if ti.has_building:
                continue

            if pos.distance_squared(Globals.my_pos) > 2:
                continue

            info = ShieldTargetInfo()
            cls.cand.append(info)
            info.position = pos
            info.dist_ally_core = Util.dist_sq(pos, Unit.core_pos)
            info.harvester_adjacent = ti.harvester_adjacent