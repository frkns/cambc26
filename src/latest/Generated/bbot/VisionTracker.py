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



class TransporterInfo:
    ti: TileInfo
    position: Position
    target: Position
    reachable: bool
    bfs_dist: int
    bfs_dist_target: int
    flow: int
    is_bridge: bool
    entity_type: EntityType
    harvester_adjacent: bool
    is_ally: bool
    node_kind: int
    flowing_into_ally: bool

    @staticmethod
    def is_better_trans_atk_target_than(a: TransporterInfo, b: TransporterInfo) -> bool:
        if a.flowing_into_ally: return False
        if b.flowing_into_ally: return True

        if not a.reachable: return False
        if not b.reachable: return True

        if a.ti.has_bot and (not b.ti.has_bot): return False
        if (not a.ti.has_bot) and b.ti.has_bot: return True

        if a.harvester_adjacent and (not b.harvester_adjacent): return True
        if (not a.harvester_adjacent) and b.harvester_adjacent: return False

        if a.flow != b.flow:
            return a.flow > b.flow

        if a.is_bridge and (not b.is_bridge): return True
        if (not a.is_bridge) and b.is_bridge: return False

        return a.bfs_dist < b.bfs_dist


    @staticmethod
    def is_better_connect_than(a: TransporterInfo, b: TransporterInfo) -> bool:
        a_reach = a.reachable and a.easily_buildable
        b_reach = b.reachable and b.easily_buildable
        if a_reach and (not b_reach): return True
        if (not a_reach) and b_reach: return False

        if a.flow != b.flow:
            return a.flow > b.flow

        return a.bfs_dist_target < b.bfs_dist_target


class ConnectManager:
    @classmethod
    def get_connect_target_info(cls) -> TransporterInfo | None:
        roots = VisionTracker.disconnected_roots
        if not roots:
            return None

        best: TransporterInfo = roots[0]
        for cand in roots[1:]:
            if TransporterInfo.is_better_connect_than(cand, best):
                best = cand

        if best.bfs_dist_target >= 1000000:
            return None
        if not best.easily_buildable:
            return None
        if not VisionTracker.me_is_canonical_ally(best.target):
            return None

        return best


class BotInfo(NamedTuple):
    position: Position
    id: int


class VisionTracker:
    enemy_transporters: list[TransporterInfo]
    disconnected_roots: list[TransporterInfo]
    allies: list[BotInfo]


    @classmethod
    def fill(cls):
        cls.enemy_transporters = []
        cls.disconnected_roots = []
        cls.allies = [BotInfo(Globals.my_pos, Globals.my_id)]

        tile_info = Map.tile_info

        for pos, x, y, idx, ti in Map.proc_nearby_tiles:
            ti: TileInfo
            if ti.has_bot and ti.is_bot_ally:
                cls.allies.append(BotInfo(pos, ti.bot_id))

            if ti.target is not None:
                trans = TransporterInfo()
                trans.ti = ti
                trans.position = pos
                trans.target = ti.target
                trans.reachable = BfsBureau.bfs20_dist[idx] < 1000000
                trans.bfs_dist = BfsBureau.bfs20_dist[idx]
                trans.flow = DarkForest.flow[idx]
                trans.is_bridge = ti.entity_type == EntityType.BRIDGE
                trans.entity_type = ti.entity_type
                trans.harvester_adjacent = ti.harvester_adjacent
                trans.is_ally = ti.is_building_ally

                trans.node_kind = DarkForest.node_kind[idx]
                trans.flowing_into_ally = trans.node_kind in \
                    (1, 3)

                tx, ty = ti.target.x, ti.target.y
                tidx = (((tx) + 3) * 56 + ((ty) + 3))
                trans.bfs_dist_target = BfsBureau.bfs20_dist[tidx]

                target_ti = tile_info[tx][ty]
                trans.easily_buildable = \
                    target_ti is not None and \
                    not target_ti.has_bot and \
                    ((not target_ti.has_building) or 
                    (target_ti.entity_type == EntityType.ROAD and target_ti.is_building_ally))

                if not ti.is_building_ally:
                    cls.enemy_transporters.append(trans)

                if DarkForest.node_kind[idx] == 0 and DarkForest.flow[idx] > 0:
                    if DarkForest.nodes[idx].up is None:
                        cls.disconnected_roots.append(trans)


    @classmethod
    def canonical_ally(cls, from_pos: Position) -> BotInfo:
        
        ret = min(cls.allies, key=
            lambda x: (Util.linf(from_pos, x.position) << 16) + x.id
        )
        
        return ret


    @classmethod
    def me_is_canonical_ally(cls, from_pos: Position) -> bool:
        return VisionTracker.canonical_ally(from_pos).id == Globals.my_id


    @classmethod
    def get_best_trans_atk_target(cls) -> TransporterInfo | None:
        enemy_transporters = cls.enemy_transporters
        if not enemy_transporters:
            return None

        best: TransporterInfo = enemy_transporters[0]

        for cand in enemy_transporters[1:]:
            if TransporterInfo.is_better_trans_atk_target_than(cand, best):
                best = cand
        return best  # no checks..?