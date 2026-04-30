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

class OrePositionPicker:
    class Candidate(NamedTuple):
        position: Position
        ti: TileInfo | None  # if None, it is outside map
        build_metric: int  # manhattan, but if directly on top, need to ~take a step back~
        is_accessible: bool
        empty: bool

    cand: list[Candidate | None] = [None] * 4

    @classmethod
    def precompute(cls, ore_pos: Position):
        my_pos = Globals.my_pos
        me_x, me_y = my_pos.x, my_pos.y

        x, y = ore_pos.x, ore_pos.y


        nx, ny = x , y -1

        build_metric = max(abs(nx - me_x), abs(ny - me_y)) 
        if build_metric == 0:
            build_metric += 2

        ti = Map.tile_info[nx][ny]

        cls.cand[0] = cls.Candidate(
            Position(nx, ny),
            ti,
            build_metric,
            ti is not None and ti.env != Environment.WALL,
            ti is not None and ti.env == Environment.EMPTY,
        )

        nx, ny = x +1, y 

        build_metric = max(abs(nx - me_x), abs(ny - me_y)) 
        if build_metric == 0:
            build_metric += 2

        ti = Map.tile_info[nx][ny]

        cls.cand[1] = cls.Candidate(
            Position(nx, ny),
            ti,
            build_metric,
            ti is not None and ti.env != Environment.WALL,
            ti is not None and ti.env == Environment.EMPTY,
        )

        nx, ny = x , y +1

        build_metric = max(abs(nx - me_x), abs(ny - me_y)) 
        if build_metric == 0:
            build_metric += 2

        ti = Map.tile_info[nx][ny]

        cls.cand[2] = cls.Candidate(
            Position(nx, ny),
            ti,
            build_metric,
            ti is not None and ti.env != Environment.WALL,
            ti is not None and ti.env == Environment.EMPTY,
        )

        nx, ny = x -1, y 

        build_metric = max(abs(nx - me_x), abs(ny - me_y)) 
        if build_metric == 0:
            build_metric += 2

        ti = Map.tile_info[nx][ny]

        cls.cand[3] = cls.Candidate(
            Position(nx, ny),
            ti,
            build_metric,
            ti is not None and ti.env != Environment.WALL,
            ti is not None and ti.env == Environment.EMPTY,
        )

    @classmethod
    def is_better_than(cls, a: Candidate, b: Candidate) -> bool:
        # prio:
        # 0. not null |
        # 1. on map   | collasped
        # 2. empty
        # 3. no building
        # 4. has ally building AND is road
        # 5. no builder bot
        # 6. build metric
        # 7. arbitrary

        if not a.is_accessible: return False
        if not b.is_accessible: return True

        EMPTY = Environment.EMPTY

        if a.empty and (not b.empty): return True
        if (not a.empty) and b.empty: return False

        if a.ti.has_building and (not b.ti.has_building):
            return False
        if (not a.ti.has_building) and b.ti.has_building:
            return True

        if a.ti.has_building and b.ti.has_building:
            ROAD = EntityType.ROAD
            a_cond = a.ti.is_building_ally and a.ti.entity_type == ROAD
            b_cond = b.ti.is_building_ally and b.ti.entity_type == ROAD

            if a_cond and (not b_cond):
                return True
            if (not a_cond) and b_cond:
                return False

        if a.ti.has_bot and (not b.ti.has_bot):
            return False
        if (not a.ti.has_bot) and b.ti.has_bot:
            return True

        if a.build_metric != b.build_metric:
            return a.build_metric < b.build_metric

        return True  # arbitrary

    @classmethod
    def pick_best_candidate(cls, ore_pos: Position) -> Candidate:
        cls.precompute(ore_pos)

        best = cls.cand[3]
        if cls.is_better_than(cls.cand[2], best):
            best = cls.cand[2]
        if cls.is_better_than(cls.cand[1], best):
            best = cls.cand[1]
        if cls.is_better_than(cls.cand[0], best):
            best = cls.cand[0]

        if not best.is_accessible:
            return None

        return best








