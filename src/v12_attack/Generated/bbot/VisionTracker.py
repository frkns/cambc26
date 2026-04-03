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



class TransporterInfo:
    position: Position
    target: Position
    reachable: bool
    bfs_dist: int
    pressure: int
    is_bridge: bool
    entity_type: EntityType


    @staticmethod
    def is_better_target_than(a: TransporterInfo, b: TransporterInfo) -> bool:
        if a.reachable and (not b.reachable): return True
        if (not a.reachable) and b.reachable: return False

        if a.pressure != b.pressure:
            return a.pressure > b.pressure

        if a.is_bridge and (not b.is_bridge): return True
        if (not a.is_bridge) and b.is_bridge: return False

        return a.bfs_dist < b.bfs_dist


class VisionTracker:
    enemy_transporters: list[TransporterInfo] = []


    @classmethod
    def fill(cls):
        cls.enemy_transporters = []

        tile_info = Map.tile_info
        for pos in Map.nearby_tiles:
            x, y = pos.x, pos.y
            ti = tile_info[x][y]

            if ti.target is not None:
                idx = (((x) + 3) * 56 + ((y) + 3))
                trans = TransporterInfo()
                trans.position = pos
                trans.target = ti.target
                trans.reachable = BfsBureau.bfs20_dist[idx] < 1000000
                trans.bfs_dist = BfsBureau.bfs20_dist[idx]
                trans.pressure = DarkForest.pressure[idx]
                trans.is_bridge = ti.entity_type == EntityType.BRIDGE
                trans.entity_type = ti.entity_type

                if not ti.is_building_ally:
                    cls.enemy_transporters.append(trans)


    @classmethod
    def get_best_trans_atk_target(cls) -> TransporterInfo:
        enemy_transporters = cls.enemy_transporters
        if not enemy_transporters:
            return None

        best: TransporterInfo = enemy_transporters[0]

        for cand in enemy_transporters[1:]:
            if TransporterInfo.is_better_target_than(cand, best):
                best = cand
        return best