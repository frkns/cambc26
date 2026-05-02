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

        if MarketMaker.est_income < 3:
            
            return None

        bfs20_dist_adj = BfsBureau.bfs20_dist_adj
        
        best: Position = None
        best_is_on_ally_transporter: bool = False
        best_dist: int = 1000000
        best_transporter_hp: int = 1000000
        best_id: int = 1000000

        for pos, x, y, idx, ti in Map.proc_nearby_tiles:

            if ti.has_bot and not ti.is_bot_ally \
                    and VisionTracker.me_is_canonical_ally(pos):
                dist = bfs20_dist_adj[idx]
                if dist >= 1000000:
                    continue
                is_on_ally_transporter = ti.has_building and ti.is_building_ally and ti.entity_type in Constants.TRANSPORTERS_SET
                transporter_hp = ti.building_hp if is_on_ally_transporter else 1000000
                bot_id = ti.bot_id if ti.has_bot else 1000000
                
                better = False
                if dist < 2 <= best_dist:
                    better = True
                elif is_on_ally_transporter != best_is_on_ally_transporter:
                    better = is_on_ally_transporter
                elif transporter_hp != best_transporter_hp:
                    better = transporter_hp < best_transporter_hp
                elif dist != best_dist:
                    better = dist < best_dist
                else:
                    better = bot_id < best_id
                        
                if better:
                    best = pos
                    best_is_on_ally_transporter = is_on_ally_transporter
                    best_dist = dist
                    best_transporter_hp = transporter_hp
                    best_id = bot_id

        
                
        return best



