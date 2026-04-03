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
from Generated.Constants import Constants
from Generated.MarketMaker import MarketMaker
from Generated.RobotPlayer import Entrypoint, Player
# ===--- IMPORT


class Util:
    @staticmethod
    def on_the_map(pos: Position) -> bool:
        return 0 <= pos.x < Map.W and 0 <= pos.y < Map.H

    @staticmethod
    def rand_pos() -> Position:
        return Position(random.randrange(Map.W), random.randrange(Map.H))


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
