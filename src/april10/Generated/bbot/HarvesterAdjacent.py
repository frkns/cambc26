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

class AdjacentInfo:
    position: Position
    enemy_hadj: int  # enemy harvesters adjacent
    ally_hadj: int   # ally  "          "
    dist_enemy_core: int
    bfs_dist: int

    @staticmethod
    def is_better_than(a: AdjacentInfo, b: AdjacentInfo):
        if a.bfs_dist >= 1000000: return False
        if b.bfs_dist >= 1000000: return True

        if a.enemy_hadj != b.enemy_hadj:
            return a.enemy_hadj > b.enemy_hadj
        if a.ally_hadj != b.ally_hadj:
            return a.ally_hadj > b.ally_hadj
        if a.bfs_dist != b.bfs_dist:
            return a.bfs_dist < b.bfs_dist
        return a.dist_enemy_core < b.dist_enemy_core


class HarvesterAdjacent:
    cand: list[AdjacentInfo]  # adjacent candidate build positions


    @classmethod
    def get_best_hijack_position(cls) -> Position | None:
        if not cls.cand:
            return None

        best = cls.cand[0]
        for c in cls.cand[1:]:
            if AdjacentInfo.is_better_than(c, best):
                best = c

        if best.enemy_hadj == 0:
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
                    continue

            info = AdjacentInfo()
            cls.cand.append(info)
            info.position = pos
            info.dist_enemy_core = Util.dist_sq(pos, Symmetry.enemy_core_pos)
            info.enemy_hadj = 0
            info.ally_hadj = 0
            info.bfs_dist = BfsBureau.bfs20_dist[idx]


            nti = tile_info[x ][y -1]
            if nti is not None and nti.has_building and nti.entity_type == EntityType.HARVESTER:
                if nti.is_building_ally:
                    info.ally_hadj += 1
                else:
                    info.enemy_hadj += 1

            nti = tile_info[x +1][y ]
            if nti is not None and nti.has_building and nti.entity_type == EntityType.HARVESTER:
                if nti.is_building_ally:
                    info.ally_hadj += 1
                else:
                    info.enemy_hadj += 1

            nti = tile_info[x ][y +1]
            if nti is not None and nti.has_building and nti.entity_type == EntityType.HARVESTER:
                if nti.is_building_ally:
                    info.ally_hadj += 1
                else:
                    info.enemy_hadj += 1

            nti = tile_info[x -1][y ]
            if nti is not None and nti.has_building and nti.entity_type == EntityType.HARVESTER:
                if nti.is_building_ally:
                    info.ally_hadj += 1
                else:
                    info.enemy_hadj += 1
            
