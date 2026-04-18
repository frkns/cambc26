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

class StalkTargeter:
    @classmethod
    def get_best_target(cls) -> Position | None:
        

        my_pos = Globals.my_pos

        if my_pos.distance_squared(Unit.core_pos) > my_pos.distance_squared(Symmetry.enemy_core_pos):
            return None

        if not Map.harvester_set:
            return None

        bfs20_dist_adj = BfsBureau.bfs20_dist_adj
        
        best: Position = None
        best_dist: int = 1000000

        for pos, x, y, idx, ti in Map.proc_nearby_tiles:

            if ti.has_bot and not ti.is_bot_ally \
                    and VisionTracker.me_is_canonical_ally(pos):
                dist = bfs20_dist_adj[idx]
                if dist < best_dist:
                    best_dist = dist
                    best = pos
                
        
                
        return best



