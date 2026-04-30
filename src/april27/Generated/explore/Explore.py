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
        # return random.choice((Position(0, 0), Position(Map.W - 1, Map.H - 1)))
        # return random.choice((
        #     Position(0, 0),
        #     Position(0, Map.maxY),
        #     Position(Map.maxX, 0),
        #     Position(Map.maxX, Map.maxY),
        # ))
        
        # # Special early game heuristics
        # if Globals.round < 50:
        #     # Move away from the core when starting out (except for the first couple bots)
        #     if Globals.spawn_round >= 3 and cls.target is None:
        #         direction_to_core = Globals.my_pos.direction_to(Unit.core_pos)
        #         if direction_to_core != Direction.CENTRE:
        #             return Util.follow_to_edge(Globals.my_pos.x, Globals.my_pos.y, *direction_to_core.delta())

        #     # Find the direction that will let us move the furthest before hitting the edge
        #     bestDx: int = None
        #     bestDy: int = None
        #     best_score: int = -1000000

        #             #     
        #     score = Util.distance_to_edge(Globals.my_pos.x, Globals.my_pos.y, 0, -1)

        #     
        #     if score > best_score:
        #         best_score = score
        #         bestDx = 0
        #         bestDy = -1

        #             #     
        #     score = Util.distance_to_edge(Globals.my_pos.x, Globals.my_pos.y, 1, -1)

        #             #     score += 1 # slightly prefer diagonals
        #     
        #     if score > best_score:
        #         best_score = score
        #         bestDx = 1
        #         bestDy = -1

        #             #     
        #     score = Util.distance_to_edge(Globals.my_pos.x, Globals.my_pos.y, 1, 0)

        #     
        #     if score > best_score:
        #         best_score = score
        #         bestDx = 1
        #         bestDy = 0

        #             #     
        #     score = Util.distance_to_edge(Globals.my_pos.x, Globals.my_pos.y, 1, 1)

        #             #     score += 1 # slightly prefer diagonals
        #     
        #     if score > best_score:
        #         best_score = score
        #         bestDx = 1
        #         bestDy = 1

        #             #     
        #     score = Util.distance_to_edge(Globals.my_pos.x, Globals.my_pos.y, 0, 1)

        #     
        #     if score > best_score:
        #         best_score = score
        #         bestDx = 0
        #         bestDy = 1

        #             #     
        #     score = Util.distance_to_edge(Globals.my_pos.x, Globals.my_pos.y, -1, 1)

        #             #     score += 1 # slightly prefer diagonals
        #     
        #     if score > best_score:
        #         best_score = score
        #         bestDx = -1
        #         bestDy = 1

        #             #     
        #     score = Util.distance_to_edge(Globals.my_pos.x, Globals.my_pos.y, -1, 0)

        #     
        #     if score > best_score:
        #         best_score = score
        #         bestDx = -1
        #         bestDy = 0

        #             #     
        #     score = Util.distance_to_edge(Globals.my_pos.x, Globals.my_pos.y, -1, -1)

        #             #     score += 1 # slightly prefer diagonals
        #     
        #     if score > best_score:
        #         best_score = score
        #         bestDx = -1
        #         bestDy = -1

        #     
        #     if bestDx is None:
        #         return Util.rand_pos()

        #     return Util.follow_to_edge(Globals.my_pos.x, Globals.my_pos.y, bestDx, bestDy)
        # # Later in the game, we should just go to random places to hit every last corner
        # else:
        if Builder.mode == 2:
            pos = Symmetry.sym_pos(Unit.core_pos)
            dx, dy = random.choice([(dx, dy) for dx in range(-6, 6) for dy in range(-6, 6) if abs(dx) > 1 or abs(dy) > 1])
            return Position(max(0,min(pos.x + dx,Map.W)), max(0,min(pos.y + dy,Map.H)))
        elif Builder.mode == 3:
            pos = Unit.core_pos
            dx, dy = random.choice([(dx, dy) for dx in range(-5, 5) for dy in range(-5, 5) if abs(dx) > 1 or abs(dy) > 1])
            return Position(max(0,min(pos.x + dx,Map.W)), max(0,min(pos.y + dy,Map.H)))
        else:
            return Util.rand_pos()


    @classmethod
    def get_target(cls) -> Position:

        if (Globals.my_pos.distance_squared(cls.target) <= 2) or (Pathfinder.cur_target == cls.target and Pathfinder.given_up):
            cls.target = cls.new_target()

        return cls.target