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
from Generated.bbot.ShieldTargeter import ShieldTargetInfo, ShieldTargeter
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



class RouteToCore:
    is_active: bool = False
    from_pos: Position
    killed: set[Position] = set()

    @classmethod
    def set_pos(cls, pos: Position):
        if (((pos.x) + 3) * 56 + ((pos.y) + 3)) in DarkForest.sink_set:
            cls.is_active = False
            return

        cls.is_active = True
        cls.from_pos = pos

    @classmethod
    def try_build_route(cls):
        assert cls.is_active

        bridge_dist, first_target = BfsBureau.find_bridge_route(
            cls.from_pos,
            Unit.core_pos_set,
            max_iter=0,
        )
        if first_target is None:
            bridge_dist, first_target = BfsBureau.find_bridge_route(
                cls.from_pos,
                DarkForest.sink_set,
            )

        

        if first_target is None:
            Debug.tee("first_target is None: giving up")
            cls.give_up()
            StateMoveTo.run(Explore.get_target()) # new
            return

        target = Position(*first_target)
        Debug.diline(cls.from_pos, target, Color.GREEN)

        if cls.from_pos.distance_squared(target) == 1:
            if BuildManager.can_dbuild_conveyor(cls.from_pos):
                BuildManager.dbuild_conveyor(cls.from_pos, cls.from_pos.direction_to(target))
                cls.set_pos(target)
        elif BuildManager.can_dbuild_bridge(cls.from_pos):
            BuildManager.dbuild_bridge(cls.from_pos, target)
            cls.set_pos(target)

    @classmethod
    def move_to_next(cls):
        Pathfinder.move_to(cls.from_pos, ban_target_pos=True)

    @classmethod
    def should_give_up(cls):
        x, y = cls.from_pos
        ti = Map.tile_info[x][y]
        if ti is None:
            return False

        if ti.has_building:
            if not ti.is_building_ally:
                return True
            if ti.entity_type in Constants.TRANSPORTERS_SET:
                return True
            if ti.entity_type != EntityType.ROAD:  # redundant
                return True
        return False


    @classmethod
    def give_up(cls):
        cls.is_active = False
        cls.killed.add(cls.from_pos)
        Debug.diamond(Color.PURPLE)


    @classmethod
    def do_routing(cls):
        if cls.should_give_up():
            cls.give_up()
            StateMoveTo.run(Explore.get_target()) # new
            return

        dsq = Globals.my_pos.distance_squared(cls.from_pos)
        if Globals.ct.get_action_cooldown() == 0 \
                and (dsq == 1 or dsq == 2):
            cls.try_build_route()
            cls.move_to_next()
        else:
            cls.move_to_next()