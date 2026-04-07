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


class FoundryBuild:
    @classmethod
    def build_foundry(cls, pos):
        print("Trying to build foundry at", pos)
        print("Foundry cost:", Globals.ct.get_foundry_cost()[0])

        Pathfinder.move_to(pos, ban_target_pos=True)
        if Globals.ct.get_global_resources()[0]> Globals.ct.get_foundry_cost()[0] and Globals.ct.can_destroy(pos) and Globals.ct.get_action_cooldown()==0:
            Globals.ct.destroy(pos)
        if Globals.ct.can_build_foundry(pos):
            Globals.ct.build_foundry(pos)
            RouteToFoundry._foundry_target = None
            DarkForest.register_sink((((pos.x) + 3) * 56 + ((pos.y) + 3)), 3)
            return True
        return False
        
    
    @classmethod
    def _pick_target(cls):
        if RouteToFoundry._foundry_target is None:
            return None
        t = ((RouteToFoundry._foundry_target) // 56 - 3), ((RouteToFoundry._foundry_target) % 56 - 3)
        return Position(t[0], t[1])
        