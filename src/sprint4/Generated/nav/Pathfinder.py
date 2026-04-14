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

class Pathfinder:
    cur_target = None
    given_up: bool = False

    @classmethod
    def reset(cls):
        cls.given_up = False

    @classmethod
    def move_to(cls, target: Position, ban_target_pos: bool = False):
        if Globals.ct.get_move_cooldown() != 0:
            return

        if target != cls.cur_target:
            cls.reset()
            cls.cur_target = target

        Debug.line(target)
        my_pos = Globals.my_pos

        Profiler.start()
        dist, dir = BfsBureau.find_route(Globals.my_pos, target, ban_target_pos)
        Profiler.end("""BfsBureau.find_route""")

        if dir is None or dist >= 1000000:
            cls.given_up = True
        else:
            if MoveManager.can_move(dir):
                MoveManager.move(dir)
            elif MoveManager.can_fill_move(dir):
                Globals.ct.build_road(my_pos.add(dir))
                MoveManager.move(dir)

