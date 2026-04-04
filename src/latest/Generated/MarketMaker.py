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



class MarketMaker:
    ti: int
    ax: int
    scale_ratio: float

    ti_hist: list[int] = [GameConstants.STARTING_TITANIUM] * 20
    ti_diff_hist: list[int] = [0] * 20
    est_income: int

    @classmethod
    def refresh(cls):
        cls.scale_ratio = Globals.ct.get_scale_percent() / 100.0
        cls.ti, MarketMaker.ax = Globals.ct.get_global_resources()

        idx = Globals.round % 20
        cls.ti_hist[idx] = cls.ti
        cls.ti_diff_hist[idx] = cls.ti - cls.ti_hist[
            idx-1 if idx-1 >= 0 else idx-1+20
        ]
        cls.est_income = max(cls.ti_diff_hist)




    @staticmethod
    def harvester_cost(apos: Position) -> int:
        
        bridges, _ = BfsBureau.find_bridge_route(apos, DarkForest.sink_set)
        
        h_cost, _ = Globals.ct.get_harvester_cost()
        b_cost, _ = Globals.ct.get_bridge_cost()
        return h_cost + b_cost * bridges

    @staticmethod
    def harvester_payback(apos: Position, cost: int = None) -> int:
        l1 = abs(apos.x - Unit.core_pos.x) + abs(apos.y - Unit.core_pos.y)
        if cost is None:
            cost = MarketMaker.harvester_cost(apos)
        return int(cost / 2.5) + (2 * l1)


    @staticmethod
    def should_build_harvester(apos: Position) -> int:
        if Globals.round < 500 and \
                apos.distance_squared(Symmetry.enemy_core_pos) < apos.distance_squared(Unit.core_pos):
            return False

        pbt = MarketMaker.harvester_payback(apos)
        

        if int(pbt * 1.5 + 100) < Util.get_rounds_left():
            return True
        return False
