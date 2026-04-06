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
        return Util.rand_pos()

        # bestDx: int = None
        # bestDy: int = None
        # best_score: int = -1000000

        #         # 
        # score = Util.distance_to_edge(Globals.my_pos.x, Globals.my_pos.y, 0, -1)

        # 
        # if score > best_score:
        #     best_score = score
        #     bestDx = 0
        #     bestDy = -1

        #         # 
        # score = Util.distance_to_edge(Globals.my_pos.x, Globals.my_pos.y, 1, -1)

        #         # score += 1 # slightly prefer diagonals
        # 
        # if score > best_score:
        #     best_score = score
        #     bestDx = 1
        #     bestDy = -1

        #         # 
        # score = Util.distance_to_edge(Globals.my_pos.x, Globals.my_pos.y, 1, 0)

        # 
        # if score > best_score:
        #     best_score = score
        #     bestDx = 1
        #     bestDy = 0

        #         # 
        # score = Util.distance_to_edge(Globals.my_pos.x, Globals.my_pos.y, 1, 1)

        #         # score += 1 # slightly prefer diagonals
        # 
        # if score > best_score:
        #     best_score = score
        #     bestDx = 1
        #     bestDy = 1

        #         # 
        # score = Util.distance_to_edge(Globals.my_pos.x, Globals.my_pos.y, 0, 1)

        # 
        # if score > best_score:
        #     best_score = score
        #     bestDx = 0
        #     bestDy = 1

        #         # 
        # score = Util.distance_to_edge(Globals.my_pos.x, Globals.my_pos.y, -1, 1)

        #         # score += 1 # slightly prefer diagonals
        # 
        # if score > best_score:
        #     best_score = score
        #     bestDx = -1
        #     bestDy = 1

        #         # 
        # score = Util.distance_to_edge(Globals.my_pos.x, Globals.my_pos.y, -1, 0)

        # 
        # if score > best_score:
        #     best_score = score
        #     bestDx = -1
        #     bestDy = 0

        #         # 
        # score = Util.distance_to_edge(Globals.my_pos.x, Globals.my_pos.y, -1, -1)

        #         # score += 1 # slightly prefer diagonals
        # 
        # if score > best_score:
        #     best_score = score
        #     bestDx = -1
        #     bestDy = -1

        # 
        # if bestDx is None:
        #     return Util.rand_pos()

        # return Util.follow_to_edge(Globals.my_pos.x, Globals.my_pos.y, bestDx, bestDy)


    @classmethod
    def get_target(cls) -> Position:

        if (Globals.my_pos.distance_squared(cls.target) <= 2) or (Pathfinder.cur_target == cls.target and Pathfinder.given_up):
            cls.target = cls.new_target()

        return cls.target