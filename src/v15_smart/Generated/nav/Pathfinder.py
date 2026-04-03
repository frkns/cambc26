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
# ===--- IMPORT



class Pathfinder:
    cur_target = None
    given_up: bool

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

        
        dist, dir = BfsBureau.find_route(Globals.my_pos, target, ban_target_pos)
        

        if dir is None:
            cls.given_up = True
        else:
            if MoveManager.can_move(dir):
                MoveManager.move(dir)
            elif MoveManager.can_fill_move(dir):
                Globals.ct.build_road(my_pos.add(dir))
                MoveManager.move(dir)

