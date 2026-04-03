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



class MarkerPositionPicker:
    class Candidate:
        position: Position
        is_accessible: bool
        has_ally_marker: bool
        has_enemy_marker: bool
        rand_key: float

    cand: list[Candidate | None] = [None] * 8

    @classmethod
    def precompute(cls):
        my_pos = Globals.my_pos


        nx, ny = my_pos.x , my_pos.y -1
        npos = Position(nx, ny)

        cand = cls.Candidate()
        cls.cand[0] = cand
        cand.position = npos

        if Globals.ct.can_place_marker(npos):
            cand.is_accessible = True
            cand.rand_key = random.random()
            ti = Map.tile_info[nx][ny]

            if ti.entity_type == EntityType.MARKER:
                if ti.is_building_ally:
                    cand.has_ally_marker = True
                    cand.has_enemy_marker = False
                else:
                    cand.has_ally_marker = False
                    cand.has_enemy_marker = True
            else:
                cand.has_ally_marker = False
                cand.has_enemy_marker = False
        else:
            cand.is_accessible = False

        if cand.is_accessible and cand.has_enemy_marker:
            assert False

        nx, ny = my_pos.x +1, my_pos.y -1
        npos = Position(nx, ny)

        cand = cls.Candidate()
        cls.cand[1] = cand
        cand.position = npos

        if Globals.ct.can_place_marker(npos):
            cand.is_accessible = True
            cand.rand_key = random.random()
            ti = Map.tile_info[nx][ny]

            if ti.entity_type == EntityType.MARKER:
                if ti.is_building_ally:
                    cand.has_ally_marker = True
                    cand.has_enemy_marker = False
                else:
                    cand.has_ally_marker = False
                    cand.has_enemy_marker = True
            else:
                cand.has_ally_marker = False
                cand.has_enemy_marker = False
        else:
            cand.is_accessible = False

        if cand.is_accessible and cand.has_enemy_marker:
            assert False

        nx, ny = my_pos.x +1, my_pos.y 
        npos = Position(nx, ny)

        cand = cls.Candidate()
        cls.cand[2] = cand
        cand.position = npos

        if Globals.ct.can_place_marker(npos):
            cand.is_accessible = True
            cand.rand_key = random.random()
            ti = Map.tile_info[nx][ny]

            if ti.entity_type == EntityType.MARKER:
                if ti.is_building_ally:
                    cand.has_ally_marker = True
                    cand.has_enemy_marker = False
                else:
                    cand.has_ally_marker = False
                    cand.has_enemy_marker = True
            else:
                cand.has_ally_marker = False
                cand.has_enemy_marker = False
        else:
            cand.is_accessible = False

        if cand.is_accessible and cand.has_enemy_marker:
            assert False

        nx, ny = my_pos.x +1, my_pos.y +1
        npos = Position(nx, ny)

        cand = cls.Candidate()
        cls.cand[3] = cand
        cand.position = npos

        if Globals.ct.can_place_marker(npos):
            cand.is_accessible = True
            cand.rand_key = random.random()
            ti = Map.tile_info[nx][ny]

            if ti.entity_type == EntityType.MARKER:
                if ti.is_building_ally:
                    cand.has_ally_marker = True
                    cand.has_enemy_marker = False
                else:
                    cand.has_ally_marker = False
                    cand.has_enemy_marker = True
            else:
                cand.has_ally_marker = False
                cand.has_enemy_marker = False
        else:
            cand.is_accessible = False

        if cand.is_accessible and cand.has_enemy_marker:
            assert False

        nx, ny = my_pos.x , my_pos.y +1
        npos = Position(nx, ny)

        cand = cls.Candidate()
        cls.cand[4] = cand
        cand.position = npos

        if Globals.ct.can_place_marker(npos):
            cand.is_accessible = True
            cand.rand_key = random.random()
            ti = Map.tile_info[nx][ny]

            if ti.entity_type == EntityType.MARKER:
                if ti.is_building_ally:
                    cand.has_ally_marker = True
                    cand.has_enemy_marker = False
                else:
                    cand.has_ally_marker = False
                    cand.has_enemy_marker = True
            else:
                cand.has_ally_marker = False
                cand.has_enemy_marker = False
        else:
            cand.is_accessible = False

        if cand.is_accessible and cand.has_enemy_marker:
            assert False

        nx, ny = my_pos.x -1, my_pos.y +1
        npos = Position(nx, ny)

        cand = cls.Candidate()
        cls.cand[5] = cand
        cand.position = npos

        if Globals.ct.can_place_marker(npos):
            cand.is_accessible = True
            cand.rand_key = random.random()
            ti = Map.tile_info[nx][ny]

            if ti.entity_type == EntityType.MARKER:
                if ti.is_building_ally:
                    cand.has_ally_marker = True
                    cand.has_enemy_marker = False
                else:
                    cand.has_ally_marker = False
                    cand.has_enemy_marker = True
            else:
                cand.has_ally_marker = False
                cand.has_enemy_marker = False
        else:
            cand.is_accessible = False

        if cand.is_accessible and cand.has_enemy_marker:
            assert False

        nx, ny = my_pos.x -1, my_pos.y 
        npos = Position(nx, ny)

        cand = cls.Candidate()
        cls.cand[6] = cand
        cand.position = npos

        if Globals.ct.can_place_marker(npos):
            cand.is_accessible = True
            cand.rand_key = random.random()
            ti = Map.tile_info[nx][ny]

            if ti.entity_type == EntityType.MARKER:
                if ti.is_building_ally:
                    cand.has_ally_marker = True
                    cand.has_enemy_marker = False
                else:
                    cand.has_ally_marker = False
                    cand.has_enemy_marker = True
            else:
                cand.has_ally_marker = False
                cand.has_enemy_marker = False
        else:
            cand.is_accessible = False

        if cand.is_accessible and cand.has_enemy_marker:
            assert False

        nx, ny = my_pos.x -1, my_pos.y -1
        npos = Position(nx, ny)

        cand = cls.Candidate()
        cls.cand[7] = cand
        cand.position = npos

        if Globals.ct.can_place_marker(npos):
            cand.is_accessible = True
            cand.rand_key = random.random()
            ti = Map.tile_info[nx][ny]

            if ti.entity_type == EntityType.MARKER:
                if ti.is_building_ally:
                    cand.has_ally_marker = True
                    cand.has_enemy_marker = False
                else:
                    cand.has_ally_marker = False
                    cand.has_enemy_marker = True
            else:
                cand.has_ally_marker = False
                cand.has_enemy_marker = False
        else:
            cand.is_accessible = False

        if cand.is_accessible and cand.has_enemy_marker:
            assert False


    @staticmethod
    def is_better_than(a: Marker.Candidate, b: Marker.Candidate):
        if not a.is_accessible: return False
        if not b.is_accessible: return True

        if a.has_enemy_marker and (not b.has_enemy_marker): return True
        if (not a.has_enemy_marker) and b.has_enemy_marker: return False

        if a.has_ally_marker and (not b.has_ally_marker): return False
        if (not a.has_ally_marker) and b.has_ally_marker: return True

        return a.rand_key < b.rand_key
    

    @classmethod
    def get_marker_pos(cls) -> Position | None:
        cls.precompute()

        best = cls.cand[0]
        if cls.is_better_than(cls.cand[1], best):
            best = cls.cand[1]
        if cls.is_better_than(cls.cand[2], best):
            best = cls.cand[2]
        if cls.is_better_than(cls.cand[3], best):
            best = cls.cand[3]
        if cls.is_better_than(cls.cand[4], best):
            best = cls.cand[4]
        if cls.is_better_than(cls.cand[5], best):
            best = cls.cand[5]
        if cls.is_better_than(cls.cand[6], best):
            best = cls.cand[6]
        if cls.is_better_than(cls.cand[7], best):
            best = cls.cand[7]

        if not best.is_accessible:
            return None

        return best.position
    
        










