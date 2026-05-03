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

# for choosing build position

class TakedownTargetInfo:
    position: Position
    dist_enemy_core: int # distance to the enemy core
    has_transporter: bool # whether the tile has an allied transporter already
    ally_turrets_nearby: int # allied turrets on nearby tiles
    enemy_turrets_nearby: int # enemy turrets on nearby tiles

    @staticmethod
    def is_better_than(a: TakedownTargetInfo, b: TakedownTargetInfo):
        if a.enemy_turrets_nearby != b.enemy_turrets_nearby:
            return a.enemy_turrets_nearby > b.enemy_turrets_nearby
        if a.has_transporter != b.has_transporter:
            return a.has_transporter < b.has_transporter
        return a.dist_enemy_core < b.dist_enemy_core


class TurretTakedown:
    cand: list[TakedownTargetInfo] # adjacent candidate build positions


    @classmethod
    def get_best_hijack_position(cls) -> Position | None:
        if not cls.cand:
            return None

        best = cls.cand[0]
        for c in cls.cand[1:]:
            if TakedownTargetInfo.is_better_than(c, best):
                best = c

        if best.enemy_turrets_nearby == 0:
            return None
        
        # If we already have turrets, don't break transporters
        if best.ally_turrets_nearby > 0 and best.has_transporter:
            return None

        if not VisionTracker.me_is_canonical_ally(best.position):
            return None

        return best.position


    @classmethod
    def fill(cls):
        cls.cand = []
        tile_info = Map.tile_info

        for pos, x, y, idx, ti in Map.proc_nearby_tiles:
            if not ti.harvester_adjacent: 
                continue
            
            if ti.env == Environment.WALL:
                continue

            if ti.has_building:
                if not ti.is_building_ally:
                    continue
                if ti.entity_type != EntityType.ROAD:
                    # We can build on top of allied transporters if we really need to
                    if not ti.entity_type in Constants.TRANSPORTERS_SET:
                        continue
                    
            # Some teams will leave their bots on turret spots to stop builders
            if ti.has_bot and not ti.is_bot_ally:
                continue

            info = TakedownTargetInfo()
            cls.cand.append(info)
            info.position = pos
            info.dist_enemy_core = Util.dist_sq(pos, Symmetry.enemy_core_pos)
            info.has_transporter = (ti.has_building and ti.is_building_ally and ti.entity_type in Constants.TRANSPORTERS_SET)
            info.enemy_turrets_nearby = 0
            info.ally_turrets_nearby = 0


            nti = tile_info[x ][y -1]
            if nti is not None and nti.has_turret:
                if nti.is_building_ally:
                    info.ally_turrets_nearby += 1
                else:
                    info.enemy_turrets_nearby += 1

            nti = tile_info[x +1][y -1]
            if nti is not None and nti.has_turret:
                if nti.is_building_ally:
                    info.ally_turrets_nearby += 1
                else:
                    info.enemy_turrets_nearby += 1

            nti = tile_info[x +1][y ]
            if nti is not None and nti.has_turret:
                if nti.is_building_ally:
                    info.ally_turrets_nearby += 1
                else:
                    info.enemy_turrets_nearby += 1

            nti = tile_info[x +1][y +1]
            if nti is not None and nti.has_turret:
                if nti.is_building_ally:
                    info.ally_turrets_nearby += 1
                else:
                    info.enemy_turrets_nearby += 1

            nti = tile_info[x ][y +1]
            if nti is not None and nti.has_turret:
                if nti.is_building_ally:
                    info.ally_turrets_nearby += 1
                else:
                    info.enemy_turrets_nearby += 1

            nti = tile_info[x -1][y +1]
            if nti is not None and nti.has_turret:
                if nti.is_building_ally:
                    info.ally_turrets_nearby += 1
                else:
                    info.enemy_turrets_nearby += 1

            nti = tile_info[x -1][y ]
            if nti is not None and nti.has_turret:
                if nti.is_building_ally:
                    info.ally_turrets_nearby += 1
                else:
                    info.enemy_turrets_nearby += 1

            nti = tile_info[x -1][y -1]
            if nti is not None and nti.has_turret:
                if nti.is_building_ally:
                    info.ally_turrets_nearby += 1
                else:
                    info.enemy_turrets_nearby += 1
            
