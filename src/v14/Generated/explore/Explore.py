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
from Awubot.Util import Util
from Generated.Constants import Constants
from Generated.MarketMaker import MarketMaker
from Generated.RobotPlayer import Entrypoint, Player
# ===--- IMPORT



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

    @classmethod
    def get_target(cls) -> Position:

        if (Globals.my_pos.distance_squared(cls.target) <= 2) or (Pathfinder.cur_target == cls.target and Pathfinder.given_up):
            cls.target = cls.new_target()

        return cls.target