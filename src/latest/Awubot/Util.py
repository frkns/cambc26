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

class Util:
    @staticmethod
    def on_the_map(pos: Position) -> bool:
        return 0 <= pos.x < Map.W and 0 <= pos.y < Map.H

    @staticmethod
    def rand_pos() -> Position:
        return Position(random.randrange(Map.W), random.randrange(Map.H))

    @staticmethod
    def distance_to_edge(x, y, dx, dy):
        """Calculate how many steps in the direction represented by (dx, dy) before going off map."""
        dist = 1_000_000
        if dx > 0:
            dist = min(dist, Map.W - x - 1)
        elif dx < 0:
            dist = min(dist, x)
        if dy > 0:
            dist = min(dist, Map.H - y - 1)
        elif dy < 0:
            dist = min(dist, y)
        return dist

    @staticmethod
    def follow_to_edge(x, y, dx, dy):
        """Follows the direction represented by (dx, dy) to the edge of the map, and returns the closest position."""
        dist = Util.distance_to_edge(x, y, dx, dy)
        return Position(x + dx * dist, y + dy * dist)

    @staticmethod
    def is_cardinal(dir: Direction) -> bool:
        # not great, to optimise, create polyfill for Direction
        dx, dy = dir.delta()
        return (dx == 0) ^ (dy == 0)

    @staticmethod
    def is_diagonal(dir: Direction) -> bool:
        dx, dy = dir.delta()
        return dx != 0 and dy != 0

    @staticmethod
    def dist_sq(A: Position, B: Position) -> int:
        dx = A.x - B.x
        dy = A.y - B.y
        return dx*dx + dy*dy

    @staticmethod
    def l1(A: Position, B: Position) -> int:
        return abs(A.x - B.x) + abs(A.y - B.y)

    @staticmethod
    def linf(A: Position, B: Position) -> int:
        return max(abs(A.x - B.x), abs(A.y - B.y))

    @staticmethod
    def get_rounds_left() -> int:
        return 2000 - Globals.round
