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
from Awubot.Constants import Constants
from Awubot.Globals import Globals
from Awubot.MoveManager import MoveManager
from Awubot.Util import Util
from Awubot.debug.Profiler import Profiler
from Generated.MarketMaker import MarketMaker
from Generated.RobotPlayer import Entrypoint, Player
from Generated.bbot.Attacker import Attacker
from Generated.bbot.Builder import Builder
from Generated.bbot.States import StateBuildHarvester, StateAttackTransporter, StateRoute, StateExplore
from Generated.bbot.VisionTracker import TransporterInfo, VisionTracker
from Generated.build.BuildManager import BuildManager
from Generated.build.OreExecutive import OreExecutive
from Generated.build.OrePositionPicker import OrePositionPicker
from Generated.build.RouteToCore import RouteToCore
from Generated.build.SuicideExecutor import SuicideExecutor
from Generated.comms.Comms import Comms
from Generated.comms.Marker import Marker
from Generated.comms.MarkerPositionPicker import MarkerPositionPicker
from Generated.debug.Debug import Color, Debug
from Generated.explore.Explore import Explore
from Generated.heal.HealExecutor import HealExecutor
from Generated.map.DarkForest import TreeNode, DarkForest
from Generated.map.Map import TileInfo, Map
from Generated.map.Symmetry import Sym, Symmetry
from Generated.nav.BfsBureau import BfsBureau
from Generated.nav.Pathfinder import Pathfinder
from Generated.units.Core import Core
from Generated.units.Unit import Unit
# ===--- IMPORT



class HealExecutor:

    class Candidate(NamedTuple):
        position: Position
        score: int

    cand: list[Candidate | None] = [None] * 9

    max_hp_map: dict = {
        EntityType.BUILDER_BOT: 30,
        EntityType.CORE: 500,
        EntityType.GUNNER: 40,
        EntityType.SENTINEL: 30,
        EntityType.BREACH: 60,
        EntityType.LAUNCHER: 30,
        EntityType.CONVEYOR: 20,
        EntityType.SPLITTER: 20,
        EntityType.ARMOURED_CONVEYOR: 50,
        EntityType.BRIDGE: 20,
        EntityType.HARVESTER: 30,
        EntityType.FOUNDRY: 50,
        EntityType.ROAD: 10,
        EntityType.BARRIER: 30,
        EntityType.MARKER: 1,
    }

    @classmethod
    def precompute(cls):
        my_pos = Globals.my_pos


        nx, ny = my_pos.x , my_pos.y -1
        npos = Position(nx, ny)

        if Globals.ct.can_heal(npos):
            ti = Map.tile_info[nx][ny]
            score = 0

            if ti.has_building:
                heal_hp = min(
                    4,  # should be 10
                    cls.max_hp_map[ti.entity_type] - ti.building_hp
                )
                score += heal_hp * 2 * (1 if ti.is_building_ally else -1)

            if ti.has_bot:
                heal_hp = min(
                    4,
                    30 - ti.bot_hp
                )
                score += heal_hp * (1 if ti.is_bot_ally else -1)

            cls.cand[0] = cls.Candidate(
                npos,
                score,
            )

        else:
            # cannot heal
            cls.cand[0] = cls.Candidate(
                npos,
                0,
            )

        nx, ny = my_pos.x +1, my_pos.y -1
        npos = Position(nx, ny)

        if Globals.ct.can_heal(npos):
            ti = Map.tile_info[nx][ny]
            score = 0

            if ti.has_building:
                heal_hp = min(
                    4,  # should be 10
                    cls.max_hp_map[ti.entity_type] - ti.building_hp
                )
                score += heal_hp * 2 * (1 if ti.is_building_ally else -1)

            if ti.has_bot:
                heal_hp = min(
                    4,
                    30 - ti.bot_hp
                )
                score += heal_hp * (1 if ti.is_bot_ally else -1)

            cls.cand[1] = cls.Candidate(
                npos,
                score,
            )

        else:
            # cannot heal
            cls.cand[1] = cls.Candidate(
                npos,
                0,
            )

        nx, ny = my_pos.x +1, my_pos.y 
        npos = Position(nx, ny)

        if Globals.ct.can_heal(npos):
            ti = Map.tile_info[nx][ny]
            score = 0

            if ti.has_building:
                heal_hp = min(
                    4,  # should be 10
                    cls.max_hp_map[ti.entity_type] - ti.building_hp
                )
                score += heal_hp * 2 * (1 if ti.is_building_ally else -1)

            if ti.has_bot:
                heal_hp = min(
                    4,
                    30 - ti.bot_hp
                )
                score += heal_hp * (1 if ti.is_bot_ally else -1)

            cls.cand[2] = cls.Candidate(
                npos,
                score,
            )

        else:
            # cannot heal
            cls.cand[2] = cls.Candidate(
                npos,
                0,
            )

        nx, ny = my_pos.x +1, my_pos.y +1
        npos = Position(nx, ny)

        if Globals.ct.can_heal(npos):
            ti = Map.tile_info[nx][ny]
            score = 0

            if ti.has_building:
                heal_hp = min(
                    4,  # should be 10
                    cls.max_hp_map[ti.entity_type] - ti.building_hp
                )
                score += heal_hp * 2 * (1 if ti.is_building_ally else -1)

            if ti.has_bot:
                heal_hp = min(
                    4,
                    30 - ti.bot_hp
                )
                score += heal_hp * (1 if ti.is_bot_ally else -1)

            cls.cand[3] = cls.Candidate(
                npos,
                score,
            )

        else:
            # cannot heal
            cls.cand[3] = cls.Candidate(
                npos,
                0,
            )

        nx, ny = my_pos.x , my_pos.y +1
        npos = Position(nx, ny)

        if Globals.ct.can_heal(npos):
            ti = Map.tile_info[nx][ny]
            score = 0

            if ti.has_building:
                heal_hp = min(
                    4,  # should be 10
                    cls.max_hp_map[ti.entity_type] - ti.building_hp
                )
                score += heal_hp * 2 * (1 if ti.is_building_ally else -1)

            if ti.has_bot:
                heal_hp = min(
                    4,
                    30 - ti.bot_hp
                )
                score += heal_hp * (1 if ti.is_bot_ally else -1)

            cls.cand[4] = cls.Candidate(
                npos,
                score,
            )

        else:
            # cannot heal
            cls.cand[4] = cls.Candidate(
                npos,
                0,
            )

        nx, ny = my_pos.x -1, my_pos.y +1
        npos = Position(nx, ny)

        if Globals.ct.can_heal(npos):
            ti = Map.tile_info[nx][ny]
            score = 0

            if ti.has_building:
                heal_hp = min(
                    4,  # should be 10
                    cls.max_hp_map[ti.entity_type] - ti.building_hp
                )
                score += heal_hp * 2 * (1 if ti.is_building_ally else -1)

            if ti.has_bot:
                heal_hp = min(
                    4,
                    30 - ti.bot_hp
                )
                score += heal_hp * (1 if ti.is_bot_ally else -1)

            cls.cand[5] = cls.Candidate(
                npos,
                score,
            )

        else:
            # cannot heal
            cls.cand[5] = cls.Candidate(
                npos,
                0,
            )

        nx, ny = my_pos.x -1, my_pos.y 
        npos = Position(nx, ny)

        if Globals.ct.can_heal(npos):
            ti = Map.tile_info[nx][ny]
            score = 0

            if ti.has_building:
                heal_hp = min(
                    4,  # should be 10
                    cls.max_hp_map[ti.entity_type] - ti.building_hp
                )
                score += heal_hp * 2 * (1 if ti.is_building_ally else -1)

            if ti.has_bot:
                heal_hp = min(
                    4,
                    30 - ti.bot_hp
                )
                score += heal_hp * (1 if ti.is_bot_ally else -1)

            cls.cand[6] = cls.Candidate(
                npos,
                score,
            )

        else:
            # cannot heal
            cls.cand[6] = cls.Candidate(
                npos,
                0,
            )

        nx, ny = my_pos.x -1, my_pos.y -1
        npos = Position(nx, ny)

        if Globals.ct.can_heal(npos):
            ti = Map.tile_info[nx][ny]
            score = 0

            if ti.has_building:
                heal_hp = min(
                    4,  # should be 10
                    cls.max_hp_map[ti.entity_type] - ti.building_hp
                )
                score += heal_hp * 2 * (1 if ti.is_building_ally else -1)

            if ti.has_bot:
                heal_hp = min(
                    4,
                    30 - ti.bot_hp
                )
                score += heal_hp * (1 if ti.is_bot_ally else -1)

            cls.cand[7] = cls.Candidate(
                npos,
                score,
            )

        else:
            # cannot heal
            cls.cand[7] = cls.Candidate(
                npos,
                0,
            )

        nx, ny = my_pos.x , my_pos.y 
        npos = Position(nx, ny)

        if Globals.ct.can_heal(npos):
            ti = Map.tile_info[nx][ny]
            score = 0

            if ti.has_building:
                heal_hp = min(
                    4,  # should be 10
                    cls.max_hp_map[ti.entity_type] - ti.building_hp
                )
                score += heal_hp * 2 * (1 if ti.is_building_ally else -1)

            if ti.has_bot:
                heal_hp = min(
                    4,
                    30 - ti.bot_hp
                )
                score += heal_hp * (1 if ti.is_bot_ally else -1)

            cls.cand[8] = cls.Candidate(
                npos,
                score,
            )

        else:
            # cannot heal
            cls.cand[8] = cls.Candidate(
                npos,
                0,
            )
    

    @classmethod
    def execute_heal_attempt(cls):
        if Globals.ct.get_action_cooldown() != 0:
            return

        cls.precompute()

        cand: HealExecutor.Candidate = max(cls.cand, key=lambda c: c.score)
        if cand.score <= 1:
            return

        Debug.line(cand.position, Color.LIME)
        Globals.ct.heal(cand.position)
    
        









