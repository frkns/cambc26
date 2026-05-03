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

class Attacker:

    @classmethod
    def get_target(cls) -> Position | None:
        # if Builder.mode == 3 and Globals.my_pos.distance_squared(Unit.core_pos) > 16:
        #     return
        
        t = cls.get_road_shield_target()
        if t is not None: 
            return t
        return cls.get_trans_target()
    
    @classmethod        
    def get_secondary_target(cls) -> Position | None:
        return cls.get_road_target()

    @classmethod
    def get_trans_target(cls) -> Position | None:
        trans: TransporterInfo = VisionTracker.get_best_trans_atk_target()
        if trans is None:
            return None
        if not trans.bfs_dist < 10: 
            return None
        if trans.flowing_into_ally:
            return None
        if trans.is_ax:
            return None
        if not trans.probably_flowing:
            return None
        # if not trans.harvester_adjacent and trans.flow == 0 and not trans.sight_flowing:
        #     return None
        # if not cls.should_fire(trans.position):
        #     return None
        if trans.enemy_bot_dist_adj == 0:
            return None
        return trans.position


    @classmethod
    def get_road_shield_target(cls) -> Position | None:
        road: RoadInfo = VisionTracker.get_best_shield_atk_target()
        if road is None:
            return None
        if not road.bfs_dist < 10: 
            return None
        if not VisionTracker.me_is_canonical_ally(road.position):
            return None
        # if not cls.should_fire(road.position):
        #     return None
        return road.position


    @classmethod
    def get_road_target(cls) -> Position | None:
        road: RoadInfo = VisionTracker.get_best_road_atk_target()
        if road is None:
            return None
        if not road.bfs_dist < 10: 
            return None
        if not VisionTracker.me_is_canonical_ally(road.position):
            return None
        if not cls.should_fire(road.position):
            return None
        if Builder.min_dist_to_a_core >= 36 and MarketMaker.ti < BuildManager.scale(150):
            return None
        return road.position

    @classmethod
    def compute_readiness(cls):
        allies_ready = 0
        lst: tuple[int, int] = []

        for pos, x, y, idx, ti in Map.inner_proc_nearby_tiles:


            if (ti.has_bot and ti.is_bot_ally) and (ti.has_building and not ti.is_building_ally) and \
                    ((
                ti.entity_type in Constants.ATTACKABLE_TRANSPORTERS_SET
            ) or (
                ti.harvester_adjacent and ti.entity_type in Constants.PASSABLE_ATTACKABLE_SET  # fix
            )):
                allies_ready += 1
                lst.append((x, y))

        enemies_ready_set: set[int] = set()  # hashed pos
        tile_info = Map.tile_info

        for x, y in lst:

            nti = tile_info[(x )][(y -1)]
            if nti is not None and nti.has_bot and not nti.is_bot_ally:
                enemies_ready_set.add(((x ) << 6) | (y -1))

            nti = tile_info[(x +1)][(y -1)]
            if nti is not None and nti.has_bot and not nti.is_bot_ally:
                enemies_ready_set.add(((x +1) << 6) | (y -1))

            nti = tile_info[(x +1)][(y )]
            if nti is not None and nti.has_bot and not nti.is_bot_ally:
                enemies_ready_set.add(((x +1) << 6) | (y ))

            nti = tile_info[(x +1)][(y +1)]
            if nti is not None and nti.has_bot and not nti.is_bot_ally:
                enemies_ready_set.add(((x +1) << 6) | (y +1))

            nti = tile_info[(x )][(y +1)]
            if nti is not None and nti.has_bot and not nti.is_bot_ally:
                enemies_ready_set.add(((x ) << 6) | (y +1))

            nti = tile_info[(x -1)][(y +1)]
            if nti is not None and nti.has_bot and not nti.is_bot_ally:
                enemies_ready_set.add(((x -1) << 6) | (y +1))

            nti = tile_info[(x -1)][(y )]
            if nti is not None and nti.has_bot and not nti.is_bot_ally:
                enemies_ready_set.add(((x -1) << 6) | (y ))

            nti = tile_info[(x -1)][(y -1)]
            if nti is not None and nti.has_bot and not nti.is_bot_ally:
                enemies_ready_set.add(((x -1) << 6) | (y -1))

        return allies_ready, len(enemies_ready_set)


    @classmethod
    def should_fire(cls, pos):
        x, y = pos.x, pos.y
        tile_info = Map.tile_info
        ti = tile_info[x][y]
        idx = (((x) + 3) * 56 + ((y) + 3))
        etype = ti.entity_type

        # assume caller passes in position with enemy building
        if not ti.has_building or ti.is_building_ally or etype not in Constants.PASSABLE_ATTACKABLE_SET:        
            return False

        if DarkForest.ax_tagged[idx]:
            return False

        if etype in (EntityType.CONVEYOR, EntityType.BRIDGE):
            if not DarkForest.sight_flowing[idx] and not DarkForest.flow[idx] > 0:
                return False


        hp = ti.building_hp
        max_hp = Constants.MAX_HP_MAP[ti.entity_type]

        if 2 * hp <= max_hp:
            
            return True

        allies_ready, enemies_ready = cls.compute_readiness()
        if allies_ready > 2 * enemies_ready:
            
            return True

        ebot_dist_adj = BfsBureau.enemy_bot_dist_adj[idx]

        if ebot_dist_adj >= 2:
            
            return True

        if etype == EntityType.ROAD and ebot_dist_adj >= 1:
            
            return True

        return False