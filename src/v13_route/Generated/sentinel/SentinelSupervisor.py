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
from Generated.bbot.States import StateBuildHarvester, StateAttackTransporter, StateRoute, StateExplore, StateBuildTurret
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



class SentinelTargetInfo:
    position: Position

    # enemy
    has_bot: bool
    has_building: bool
    has_turret: bool  # subset of building
    has_launcher: bool
    can_shoot_me: bool
    is_road: bool

    bot_hp: int
    building_hp: int
    iscore: int  # probably won't be used
    ally_connected: bool

    rand_key: float  # for sake of beauty, should almost never matter
    entity_type: EntityType

    is_harvester_feeding_ally: bool
    harvester_adjacent: bool


    @staticmethod
    def is_better_than(a: SentinelTargetInfo, b: SentinelTargetInfo):

        if a.is_harvester_feeding_ally: return False
        if b.is_harvester_feeding_ally: return True

        if a.has_turret and (not b.has_turret): return True
        if (not a.has_turret) and b.has_turret: return False

        if a.has_turret and b.has_turret:
            if a.can_shoot_me and (not b.can_shoot_me): return True
            if (not a.can_shoot_me) and b.can_shoot_me: return False

        # if there is a bot on top of the tile, nothing underneath gets hit
        if a.has_bot and (not b.has_bot): return True
        if (not a.has_bot) and b.has_bot: return False

        if a.has_bot and b.has_bot:
            if a.bot_hp != b.bot_hp:
                return a.bot_hp < b.bot_hp

        if a.ally_connected and (not b.ally_connected): return False  # don't target allied routes
        if (not a.ally_connected) and b.ally_connected: return True

        if a.has_building and (not b.has_building): return True
        if (not a.has_building) and b.has_building: return False

        if a.harvester_adjacent and (not b.harvester_adjacent): return True
        if (not a.harvester_adjacent) and b.harvester_adjacent: return False

        if a.is_road and (not b.is_road): return False  # prefer non-roads
        if (not a.is_road) and b.is_road: return True

        if a.has_building and b.has_building:
            if a.building_hp != b.building_hp:
                return a.building_hp < b.building_hp
            return a.rand_key < b.rand_key

        return a.rand_key < b.rand_key



class SentinelSupervisor:
    targets: list[SentinelTargetInfo]

# ---===

    importance_score: dict[EntityType, int] = {
        None: 0,
        EntityType.BUILDER_BOT: 
            0,
        EntityType.CORE: 
            96,
        EntityType.GUNNER: 
            0,
        EntityType.SENTINEL: 
            0,
        EntityType.BREACH: 
            0,
        EntityType.LAUNCHER: 
            0,
        EntityType.CONVEYOR: 
            97,
        EntityType.SPLITTER: 
            100,
        EntityType.ARMOURED_CONVEYOR: 
            95,
        EntityType.BRIDGE: 
            98,
        EntityType.HARVESTER: 
            0,
        EntityType.FOUNDRY: 
            99,
        EntityType.ROAD: 
            0,
        EntityType.BARRIER: 
            0,
        EntityType.MARKER: 
            0,
    }
# ===---

    @classmethod
    def try_fire(cls):
        pos = cls.get_best_target()
        if pos is None:
            return

        print(f'attempt fire @ {pos}')
        Debug.line(pos, Color.TEAL)

        if Globals.ct.can_fire(pos):
            Globals.ct.fire(pos)


    @classmethod
    def get_best_target(cls) -> Position | None:
        targets = cls.targets
        if not targets:
            return None

        best = targets[0]
        for target in targets[1:]:
            if SentinelTargetInfo.is_better_than(target, best):
                best = target

        if not best.has_bot and not best.has_building:
            return None

        if not best.has_bot and best.ally_connected:
            return None

        if best.is_harvester_feeding_ally:
            return None

        return best.position


    @classmethod
    def fill(cls):
        ct = Globals.ct
        cls.targets = []
        tile_info = Map.tile_info

        for pos in ct.get_attackable_tiles():
            x, y = pos.x, pos.y
            idx = (((x) + 3) * 56 + ((y) + 3))
            ti = tile_info[x][y]
            
            info = SentinelTargetInfo()
            info.position = pos
            info.has_bot = False
            info.has_turret = False
            info.has_building = False
            info.has_launcher = False
            info.can_shoot_me = False
            info.iscore = cls.importance_score[ti.entity_type]
            info.entity_type = ti.entity_type
            info.is_road = ti.entity_type == EntityType.ROAD
            info.rand_key = random.random()
            info.ally_connected = DarkForest.node_kind[idx] in \
                (1, 3)

            info.is_harvester_feeding_ally = False
            info.harvester_adjacent = ti.harvester_adjacent

            if ti.entity_type == EntityType.HARVESTER:
                nidx = idx -1
                if DarkForest.node_kind[nidx] in (1, 3):
                    info.is_harvester_feeding_ally = True
                nidx = idx +1
                if DarkForest.node_kind[nidx] in (1, 3):
                    info.is_harvester_feeding_ally = True
                nidx = idx -56
                if DarkForest.node_kind[nidx] in (1, 3):
                    info.is_harvester_feeding_ally = True
                nidx = idx +56
                if DarkForest.node_kind[nidx] in (1, 3):
                    info.is_harvester_feeding_ally = True

            if ti.has_bot and not ti.is_bot_ally:
                info.has_bot = True
                info.bot_hp = ti.bot_hp

            # can't shoot building underneath if there's a bot on top
            if not ti.has_bot and ti.has_building and not ti.is_building_ally:
                info.has_building = True
                info.building_hp = ti.building_hp
                if ti.has_turret:
                    info.has_turret = True
                    info.can_shoot_me = ct.can_fire_from(
                        pos, 
                        ti.turret_direction, 
                        ti.entity_type,
                        Globals.my_pos
                    )

                elif info.entity_type == EntityType.LAUNCHER:
                    info.has_launcher = True

            cls.targets.append(info)
