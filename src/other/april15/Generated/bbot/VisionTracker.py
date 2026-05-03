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
from Awubot import *
from Generated import *

class TransporterInfo:
    ti: TileInfo
    position: Position
    target: Position
    easily_reachable: bool
    bfs_dist: int
    bfs_dist_target: int
    flow: int
    entity_type: EntityType
    harvester_adjacent: bool
    is_ally: bool
    node_kind: int
    flowing_into_ally: bool

    @staticmethod
    def is_better_trans_atk_target_than(a: TransporterInfo, b: TransporterInfo) -> bool:
        if a.flowing_into_ally: return False
        if b.flowing_into_ally: return True

        if not a.easily_reachable: return False
        if not b.easily_reachable: return True

        if a.ti.has_bot and (not b.ti.has_bot): return False
        if (not a.ti.has_bot) and b.ti.has_bot: return True

        if a.harvester_adjacent and (not b.harvester_adjacent): return True
        if (not a.harvester_adjacent) and b.harvester_adjacent: return False

        if a.ti.building_hp != b.ti.building_hp:
            return a.ti.building_hp < b.ti.building_hp

        if a.flow != b.flow:
            return a.flow > b.flow

        return a.bfs_dist < b.bfs_dist


    @staticmethod
    def is_better_connect_than(a: TransporterInfo, b: TransporterInfo) -> bool:
        a_reach = a.easily_reachable and a.easily_buildable
        b_reach = b.easily_reachable and b.easily_buildable
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


class RoadInfo:
    position: Position
    hp: int
    bfs_dist: int

    def is_better_road_atk_target_than(a: RoadInfo, b: RoadInfo) -> bool:
        if a.bfs_dist != b.bfs_dist:
            return a.bfs_dist < b.bfs_dist
        return a.hp < b.hp


class VisionTracker:
    enemy_roads_harvester: list[RoadInfo]  # roads adjacent to ti harvester
    enemy_transporters: list[TransporterInfo]
    disconnected_roots: list[TransporterInfo]
    allies: list[BotInfo]


    @classmethod
    def fill(cls):
        cls.enemy_transporters = []
        cls.enemy_roads_harvester = []
        cls.disconnected_roots = []
        cls.allies = [BotInfo(Globals.my_pos, Globals.my_id)]

        tile_info = Map.tile_info

        for pos, x, y, idx, ti in Map.proc_nearby_tiles:
            ti: TileInfo
            if ti.has_bot and ti.is_bot_ally:
                cls.allies.append(BotInfo(pos, ti.bot_id))

            if ti.harvester_adjacent and ti.entity_type == EntityType.ROAD and not ti.is_building_ally:
                info = RoadInfo()
                info.position = pos
                info.hp = ti.building_hp
                info.bfs_dist = BfsBureau.bfs20_dist[idx]
                cls.enemy_roads_harvester.append(info)


            if ti.target is not None:
                trans = TransporterInfo()
                trans.ti = ti
                trans.position = pos
                trans.target = ti.target
                trans.easily_reachable = BfsBureau.bfs20_dist[idx] < 20
                trans.bfs_dist = BfsBureau.bfs20_dist[idx]
                trans.flow = DarkForest.flow[idx]
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
                        if Globals.ct.get_stored_resource(trans.ti.building_id) in (ResourceType.TITANIUM, ResourceType.REFINED_AXIONITE):
                            cls.disconnected_roots.append(trans)


    @classmethod
    def canonical_ally(cls, from_pos: Position) -> BotInfo:
        
        ret = min(cls.allies, key=
            lambda x: (Util.linf(from_pos, x.position) << 16) + x.id
        )
        
        return ret
    
    @classmethod
    def canonical_ally_index(cls, from_pos: Position) -> int:
        
        allyIndex = list(map(lambda x: x.position, sorted(cls.allies, key=
            lambda x: (Util.linf(from_pos, x.position) << 16) + x.id
        )))
        if Globals.my_pos in allyIndex:
            i = allyIndex.index(Globals.my_pos)
        else:
            Debug.warn("my_pos not found in canonical ally list!")
            i = 0
        
        return i


    canon_map: dict[Position, int] = {}

    @classmethod
    def me_is_canonical_ally(cls, from_pos: Position) -> bool:

        canon_map = cls.canon_map
        round = Globals.round
        ret = VisionTracker.canonical_ally(from_pos).id == Globals.my_id

        if not ret:
            canon_map[from_pos] = round
            return False

        if from_pos not in canon_map:
            return True

        stored_round = canon_map[from_pos]
        if stored_round == round or round - stored_round >= 2:
            return True

        return False


    @classmethod
    def get_best_trans_atk_target(cls) -> TransporterInfo | None:
        enemy_transporters = cls.enemy_transporters
        if not enemy_transporters:
            return None

        best: TransporterInfo = enemy_transporters[0]

        for cand in enemy_transporters[1:]:
            if TransporterInfo.is_better_trans_atk_target_than(cand, best):
                best = cand
        return best 


    @classmethod
    def get_best_road_atk_target(cls) -> RoadInfo | None:
        roads = cls.enemy_roads_harvester
        if not roads:
            return None

        best: RoadInfo = roads[0]

        for cand in roads[1:]:
            if RoadInfo.is_better_road_atk_target_than(cand, best):
                best = cand
        return best 

