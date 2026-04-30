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
    class Candidate:
        __slots__ = ('position', 'ti', 'build_metric', 'is_accessible', 'empty')

    cand: list[Candidate | None] = [None] * 4

    @classmethod
    def precompute(cls, ore_pos: Position):
        my_pos = Globals.my_pos
        me_x, me_y = my_pos.x, my_pos.y

        x, y = ore_pos.x, ore_pos.y


        nx, ny = x , y -1

        ti = Map.tile_info[nx][ny]

        cand = cls.Candidate()
        cand.ti = ti
        cand.position = Position(nx, ny)
        cand.build_metric = abs(Unit.core_pos.x - nx) + abs(Unit.core_pos.y - ny)
        cand.is_accessible = ti is not None and ti.env != Environment.WALL 
        cand.empty = ti is not None and ti.env == Environment.EMPTY

        cls.cand[0] = cand

        nx, ny = x +1, y 

        ti = Map.tile_info[nx][ny]

        cand = cls.Candidate()
        cand.ti = ti
        cand.position = Position(nx, ny)
        cand.build_metric = abs(Unit.core_pos.x - nx) + abs(Unit.core_pos.y - ny)
        cand.is_accessible = ti is not None and ti.env != Environment.WALL 
        cand.empty = ti is not None and ti.env == Environment.EMPTY

        cls.cand[1] = cand

        nx, ny = x , y +1

        ti = Map.tile_info[nx][ny]

        cand = cls.Candidate()
        cand.ti = ti
        cand.position = Position(nx, ny)
        cand.build_metric = abs(Unit.core_pos.x - nx) + abs(Unit.core_pos.y - ny)
        cand.is_accessible = ti is not None and ti.env != Environment.WALL 
        cand.empty = ti is not None and ti.env == Environment.EMPTY

        cls.cand[2] = cand

        nx, ny = x -1, y 

        ti = Map.tile_info[nx][ny]

        cand = cls.Candidate()
        cand.ti = ti
        cand.position = Position(nx, ny)
        cand.build_metric = abs(Unit.core_pos.x - nx) + abs(Unit.core_pos.y - ny)
        cand.is_accessible = ti is not None and ti.env != Environment.WALL 
        cand.empty = ti is not None and ti.env == Environment.EMPTY

        cls.cand[3] = cand

    @classmethod
    def is_better_than(cls, a: Candidate, b: Candidate) -> bool:
        if not a.is_accessible: return False
        if not b.is_accessible: return True

        if a.empty and (not b.empty): return True
        if (not a.empty) and b.empty: return False

        if a.ti.has_building and (not b.ti.has_building):
            return False
        if (not a.ti.has_building) and b.ti.has_building:
            return True

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








