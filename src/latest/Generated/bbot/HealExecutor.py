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
from Generated.Constants import Constants
from Generated.MarketMaker import MarketMaker
from Generated.RobotPlayer import Entrypoint, Player
from Generated.bbot.Attacker import Attacker
from Generated.bbot.Builder import Builder
from Generated.bbot.HarvesterAdjacent import AdjacentInfo, HarvesterAdjacent
from Generated.bbot.HealExecutor import HealExecutor
from Generated.bbot.HealTargeter import HealTargetInfo, HealTargeter
from Generated.bbot.States import StateBuildHarvester, StateBuildHarvesterAx, StateAttackTransporter, StateRoute, StateRouteFoundry, StateMoveTo, StateBuildTurret
from Generated.bbot.VisionTracker import TransporterInfo, ConnectManager, BotInfo, VisionTracker
from Generated.build.BuildManager import BuildManager
from Generated.build.OreExecutive import OreExecutive
from Generated.build.OrePositionPicker import OrePositionPicker
from Generated.build.RouteToCore import RouteToCore
from Generated.build.RouteToFoundry import RouteToFoundry
from Generated.build.SuicideExecutor import SuicideExecutor
from Generated.comms.Comms import Comms
from Generated.comms.Marker import Marker
from Generated.comms.MarkerPositionPicker import MarkerPositionPicker
from Generated.core.Core import Core
from Generated.core.CoreHistory import CoreHistory
from Generated.core.SpawnManager import SpawnManager
from Generated.debug.Debug import Color, Debug
from Generated.debug.Profiler import Profiler
from Generated.explore.Explore import Explore
from Generated.map.DarkForest import TreeNode, DarkForest
from Generated.map.Map import TileInfo, Map
from Generated.map.Symmetry import Sym, Symmetry
from Generated.nav.BfsBureau import BfsBureau
from Generated.nav.Pathfinder import Pathfinder
from Generated.sentinel.Sentinel import Sentinel
from Generated.sentinel.SentinelSupervisor import SentinelTargetInfo, SentinelSupervisor
from Generated.units.Unit import Unit
# ===--- IMPORT



class HealExecutor:
    class Candidate:
        position: Position
        is_accessible: bool
        building_heal: int
        building_hp: int
        bot_heal: int
        bot_hp: int

    cand: list[Candidate | None] = [None] * 9


    @classmethod
    def precompute(cls):
        my_pos = Globals.my_pos


        nx, ny = my_pos.x , my_pos.y -1
        npos = Position(nx, ny)

        cand = cls.Candidate()
        cls.cand[0] = cand

        if Globals.ct.can_heal(npos):
            cand.is_accessible = True
            cand.position = npos
            cand.building_heal = 0
            cand.bot_heal = 0
            cand.building_hp = 1000000
            cand.bot_hp = 1000000

            ti = Map.tile_info[nx][ny]

            if ti.has_building and ti.is_building_ally:
                cand.building_heal = min(
                    4,
                    Constants.MAX_HP_MAP[ti.entity_type] - ti.building_hp
                )
                cand.building_hp = ti.building_hp

            if ti.has_bot and ti.is_bot_ally:
                cand.bot_heal = min(
                    4,
                    30 - ti.bot_hp
                )
                cand.bot_hp = ti.bot_hp
        else:
            cand.is_accessible = False

        nx, ny = my_pos.x +1, my_pos.y -1
        npos = Position(nx, ny)

        cand = cls.Candidate()
        cls.cand[1] = cand

        if Globals.ct.can_heal(npos):
            cand.is_accessible = True
            cand.position = npos
            cand.building_heal = 0
            cand.bot_heal = 0
            cand.building_hp = 1000000
            cand.bot_hp = 1000000

            ti = Map.tile_info[nx][ny]

            if ti.has_building and ti.is_building_ally:
                cand.building_heal = min(
                    4,
                    Constants.MAX_HP_MAP[ti.entity_type] - ti.building_hp
                )
                cand.building_hp = ti.building_hp

            if ti.has_bot and ti.is_bot_ally:
                cand.bot_heal = min(
                    4,
                    30 - ti.bot_hp
                )
                cand.bot_hp = ti.bot_hp
        else:
            cand.is_accessible = False

        nx, ny = my_pos.x +1, my_pos.y 
        npos = Position(nx, ny)

        cand = cls.Candidate()
        cls.cand[2] = cand

        if Globals.ct.can_heal(npos):
            cand.is_accessible = True
            cand.position = npos
            cand.building_heal = 0
            cand.bot_heal = 0
            cand.building_hp = 1000000
            cand.bot_hp = 1000000

            ti = Map.tile_info[nx][ny]

            if ti.has_building and ti.is_building_ally:
                cand.building_heal = min(
                    4,
                    Constants.MAX_HP_MAP[ti.entity_type] - ti.building_hp
                )
                cand.building_hp = ti.building_hp

            if ti.has_bot and ti.is_bot_ally:
                cand.bot_heal = min(
                    4,
                    30 - ti.bot_hp
                )
                cand.bot_hp = ti.bot_hp
        else:
            cand.is_accessible = False

        nx, ny = my_pos.x +1, my_pos.y +1
        npos = Position(nx, ny)

        cand = cls.Candidate()
        cls.cand[3] = cand

        if Globals.ct.can_heal(npos):
            cand.is_accessible = True
            cand.position = npos
            cand.building_heal = 0
            cand.bot_heal = 0
            cand.building_hp = 1000000
            cand.bot_hp = 1000000

            ti = Map.tile_info[nx][ny]

            if ti.has_building and ti.is_building_ally:
                cand.building_heal = min(
                    4,
                    Constants.MAX_HP_MAP[ti.entity_type] - ti.building_hp
                )
                cand.building_hp = ti.building_hp

            if ti.has_bot and ti.is_bot_ally:
                cand.bot_heal = min(
                    4,
                    30 - ti.bot_hp
                )
                cand.bot_hp = ti.bot_hp
        else:
            cand.is_accessible = False

        nx, ny = my_pos.x , my_pos.y +1
        npos = Position(nx, ny)

        cand = cls.Candidate()
        cls.cand[4] = cand

        if Globals.ct.can_heal(npos):
            cand.is_accessible = True
            cand.position = npos
            cand.building_heal = 0
            cand.bot_heal = 0
            cand.building_hp = 1000000
            cand.bot_hp = 1000000

            ti = Map.tile_info[nx][ny]

            if ti.has_building and ti.is_building_ally:
                cand.building_heal = min(
                    4,
                    Constants.MAX_HP_MAP[ti.entity_type] - ti.building_hp
                )
                cand.building_hp = ti.building_hp

            if ti.has_bot and ti.is_bot_ally:
                cand.bot_heal = min(
                    4,
                    30 - ti.bot_hp
                )
                cand.bot_hp = ti.bot_hp
        else:
            cand.is_accessible = False

        nx, ny = my_pos.x -1, my_pos.y +1
        npos = Position(nx, ny)

        cand = cls.Candidate()
        cls.cand[5] = cand

        if Globals.ct.can_heal(npos):
            cand.is_accessible = True
            cand.position = npos
            cand.building_heal = 0
            cand.bot_heal = 0
            cand.building_hp = 1000000
            cand.bot_hp = 1000000

            ti = Map.tile_info[nx][ny]

            if ti.has_building and ti.is_building_ally:
                cand.building_heal = min(
                    4,
                    Constants.MAX_HP_MAP[ti.entity_type] - ti.building_hp
                )
                cand.building_hp = ti.building_hp

            if ti.has_bot and ti.is_bot_ally:
                cand.bot_heal = min(
                    4,
                    30 - ti.bot_hp
                )
                cand.bot_hp = ti.bot_hp
        else:
            cand.is_accessible = False

        nx, ny = my_pos.x -1, my_pos.y 
        npos = Position(nx, ny)

        cand = cls.Candidate()
        cls.cand[6] = cand

        if Globals.ct.can_heal(npos):
            cand.is_accessible = True
            cand.position = npos
            cand.building_heal = 0
            cand.bot_heal = 0
            cand.building_hp = 1000000
            cand.bot_hp = 1000000

            ti = Map.tile_info[nx][ny]

            if ti.has_building and ti.is_building_ally:
                cand.building_heal = min(
                    4,
                    Constants.MAX_HP_MAP[ti.entity_type] - ti.building_hp
                )
                cand.building_hp = ti.building_hp

            if ti.has_bot and ti.is_bot_ally:
                cand.bot_heal = min(
                    4,
                    30 - ti.bot_hp
                )
                cand.bot_hp = ti.bot_hp
        else:
            cand.is_accessible = False

        nx, ny = my_pos.x -1, my_pos.y -1
        npos = Position(nx, ny)

        cand = cls.Candidate()
        cls.cand[7] = cand

        if Globals.ct.can_heal(npos):
            cand.is_accessible = True
            cand.position = npos
            cand.building_heal = 0
            cand.bot_heal = 0
            cand.building_hp = 1000000
            cand.bot_hp = 1000000

            ti = Map.tile_info[nx][ny]

            if ti.has_building and ti.is_building_ally:
                cand.building_heal = min(
                    4,
                    Constants.MAX_HP_MAP[ti.entity_type] - ti.building_hp
                )
                cand.building_hp = ti.building_hp

            if ti.has_bot and ti.is_bot_ally:
                cand.bot_heal = min(
                    4,
                    30 - ti.bot_hp
                )
                cand.bot_hp = ti.bot_hp
        else:
            cand.is_accessible = False

        nx, ny = my_pos.x , my_pos.y 
        npos = Position(nx, ny)

        cand = cls.Candidate()
        cls.cand[8] = cand

        if Globals.ct.can_heal(npos):
            cand.is_accessible = True
            cand.position = npos
            cand.building_heal = 0
            cand.bot_heal = 0
            cand.building_hp = 1000000
            cand.bot_hp = 1000000

            ti = Map.tile_info[nx][ny]

            if ti.has_building and ti.is_building_ally:
                cand.building_heal = min(
                    4,
                    Constants.MAX_HP_MAP[ti.entity_type] - ti.building_hp
                )
                cand.building_hp = ti.building_hp

            cand.bot_heal = min(
                4,
                30 - Globals.ct.get_hp()
            )
            cand.bot_hp = Globals.ct.get_hp() 
        else:
            cand.is_accessible = False


    @classmethod
    def is_better_than(cls, a: HealExecutor.Candidate, b: HealExecutor.Candidate) -> bool:
        if not a.is_accessible: return False
        if not b.is_accessible: return True

        if a.building_heal != b.building_heal:
            return a.building_heal > b.building_heal

        if a.building_hp != b.building_hp:
            return a.building_hp < b.building_hp

        if a.bot_heal != b.bot_heal:
            return a.bot_heal > b.bot_heal

        if a.bot_hp != b.bot_hp:
            return a.bot_hp < b.bot_hp

        return False


    @classmethod
    def execute_heal_attempt(cls):
        if Globals.ct.get_action_cooldown() != 0:
            return

        cls.precompute()

        best = cls.cand[8]
        if cls.is_better_than(cls.cand[7], best):
            best = cls.cand[7]
        if cls.is_better_than(cls.cand[6], best):
            best = cls.cand[6]
        if cls.is_better_than(cls.cand[5], best):
            best = cls.cand[5]
        if cls.is_better_than(cls.cand[4], best):
            best = cls.cand[4]
        if cls.is_better_than(cls.cand[3], best):
            best = cls.cand[3]
        if cls.is_better_than(cls.cand[2], best):
            best = cls.cand[2]
        if cls.is_better_than(cls.cand[1], best):
            best = cls.cand[1]
        if cls.is_better_than(cls.cand[0], best):
            best = cls.cand[0]

        if not best.is_accessible:
            return
        
        if best.building_heal + best.bot_heal < 4:
            return

        Debug.line(best.position, Color.LIME)
        Globals.ct.heal(best.position)
    
        









