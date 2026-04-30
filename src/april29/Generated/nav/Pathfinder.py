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
    near_base: bool = False  # hysteresis state: prefer empties over roads when True

    @classmethod
    def reset(cls):
        cls.given_up = False
        cls.near_base = False

    @classmethod
    def move_off(cls):
        best_dir = None
        best_w = 1000000
        d = BfsBureau.bfs20_dist
        idx = Globals.my_idx

        nidx = idx -1
        if MoveManager.can_move(Direction.NORTH) and d[nidx] < best_w:
            best_dir = Direction.NORTH
            best_w = d[nidx]
        nidx = idx +55
        if MoveManager.can_move(Direction.NORTHEAST) and d[nidx] < best_w:
            best_dir = Direction.NORTHEAST
            best_w = d[nidx]
        nidx = idx +56
        if MoveManager.can_move(Direction.EAST) and d[nidx] < best_w:
            best_dir = Direction.EAST
            best_w = d[nidx]
        nidx = idx +57
        if MoveManager.can_move(Direction.SOUTHEAST) and d[nidx] < best_w:
            best_dir = Direction.SOUTHEAST
            best_w = d[nidx]
        nidx = idx +1
        if MoveManager.can_move(Direction.SOUTH) and d[nidx] < best_w:
            best_dir = Direction.SOUTH
            best_w = d[nidx]
        nidx = idx -55
        if MoveManager.can_move(Direction.SOUTHWEST) and d[nidx] < best_w:
            best_dir = Direction.SOUTHWEST
            best_w = d[nidx]
        nidx = idx -56
        if MoveManager.can_move(Direction.WEST) and d[nidx] < best_w:
            best_dir = Direction.WEST
            best_w = d[nidx]
        nidx = idx -57
        if MoveManager.can_move(Direction.NORTHWEST) and d[nidx] < best_w:
            best_dir = Direction.NORTHWEST
            best_w = d[nidx]

        if best_dir is None:
            return False

        MoveManager.move(best_dir)
        return True


    @classmethod
    def move_to(cls, target: Position, ban_target_pos: bool = False, orbit: bool = False):



        if Globals.ct.get_move_cooldown() != 0:
            return

        if target != cls.cur_target:
            cls.reset()
            cls.cur_target = target

        Debug.line(target)
        my_pos = Globals.my_pos
        midx = (((my_pos.x) + 3) * 56 + ((my_pos.y) + 3))


        # ── Hysteresis: switch to road-building mode near base/enemy-base ──
        # Enter near_base when rsq <= 18, exit only when rsq > 25.
        # The dead-band [19..25] prevents flickering at the boundary.
        dsq_to_own_core   = my_pos.distance_squared(Unit.core_pos)
        dsq_to_enemy_core = my_pos.distance_squared(Symmetry.enemy_core_pos) if Symmetry.is_sym_known else 1000000
        dsq_to_nearest_base = min(dsq_to_own_core, dsq_to_enemy_core)

        if dsq_to_nearest_base <= 18:
            cls.near_base = True
        elif dsq_to_nearest_base > 25:
            cls.near_base = False
        # else: in dead-band [19..25], keep previous near_base value

        Profiler.start(f"""BfsBureau.find_route""")
        if cls.near_base:
            dist, dir = BfsBureau.find_route_inv(my_pos, target, ban_target_pos)  # prefer empties → lays roads
        else:
            dist, dir = BfsBureau.find_route(my_pos, target, ban_target_pos)      # prefer roads → uses existing roads
        Profiler.end(f"""BfsBureau.find_route""")

        if orbit and 0 < target.distance_squared(my_pos) <= 2:
            dir = my_pos.direction_to(target).rotate_left()


        if dir is not None:
            dsq = my_pos.distance_squared(target)
            ndsq = my_pos.add(dir).distance_squared(target)
            if (dsq == 1 or dsq == 2) and dsq < ndsq: 
                if BfsBureau.now_weight[midx] <= 3:
                    if not MoveManager.can_fill_move(my_pos.direction_to(target)):
                        
                        return

        if dir is None:
            cls.given_up = True
            
            return

        if MoveManager.can_move(dir):
            MoveManager.move(dir)
        elif MoveManager.can_fill_move(dir):
            Globals.ct.build_road(my_pos.add(dir))
            MoveManager.move(dir)

        
