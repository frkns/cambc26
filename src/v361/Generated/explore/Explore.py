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

class Explore:
    target: Position
    target = None

    @classmethod
    def init(cls) -> None:
        cls.target = cls.new_target()

    @classmethod
    def new_target(cls) -> Position:
        # # Later in the game, we should just go to random places to hit every last corner
        # else:
        if Builder.mode == 2:
            pos = Symmetry.sym_pos(Unit.core_pos)
            dx, dy = random.choice(cls.one)
            return Position(max(0, min(pos.x + dx, Map.maxX)), max(0, min(pos.y + dy, Map.maxY)))
        elif Builder.mode == 3:
            pos = Unit.core_pos
            dx, dy = random.choice(cls.two)
            return Position(max(0, min(pos.x + dx, Map.maxX)), max(0, min(pos.y + dy, Map.maxY)))
        else:
            return Util.rand_pos()
            # mx, my = Globals.my_pos.x, Globals.my_pos.y
            # r = max(Map.W, Map.H) / 2
            # theta = random.uniform(0, 2 * math.pi)
            # dist = math.sqrt(random.random()) * r
            # nx = max(0, min(Map.maxX, int(round(mx + dist * math.cos(theta)))))
            # ny = max(0, min(Map.maxY, int(round(my + dist * math.sin(theta)))))
            # return Position(nx, ny)

    one = [(dx, dy) for dx in range(-6, 6) for dy in range(-6, 6) if abs(dx) > 1 or abs(dy) > 1]
    two = [(dx, dy) for dx in range(-5, 5) for dy in range(-5, 5) if abs(dx) > 1 or abs(dy) > 1]

    @classmethod
    def get_target(cls) -> Position:

        if (Globals.my_pos.distance_squared(cls.target) <= 2) or (Pathfinder.cur_target == cls.target and Pathfinder.given_up):
            cls.target = cls.new_target()

        return cls.target