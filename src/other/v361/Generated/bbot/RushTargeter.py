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

class RushTargeter:
    persistentOre = None
    beenNearbyEnemyCore = False
    killed: set[Position] = set()

    @classmethod
    def enemy_core_turret_target(cls, vision_r, attack_rsq) -> Position | None:
        if not Symmetry.is_sym_known:
            return None
        enemy_core = Symmetry.enemy_core_pos
        print("Yo so the enemy core is at", enemy_core)


        # ── Step 1: pick best attack landing position ────────────────
        attack_pos = None
        best_attack_dist = float('inf')
        currLoc = Globals.my_pos
        for dx in range(-vision_r, vision_r + 1):
            for dy in range(-vision_r, vision_r + 1):
                if dx * dx + dy * dy > attack_rsq:
                    continue
                candidate = Position(enemy_core.x + dx, enemy_core.y + dy)
                tile = Map.tile_info[candidate.x][candidate.y]
                if tile is None:
                    continue
                if tile.env in [Environment.WALL]:
                    continue
                if tile.has_building and (not tile.is_building_ally):
                    continue
                if tile.has_building and tile.entity_type in Constants.TURRET_SET:
                    continue
                if tile.has_building and tile.entity_type in Constants.TRANSPORTERS_SET:
                    continue
                d = currLoc.distance_squared(candidate)
                if d < best_attack_dist:
                    best_attack_dist = d
                    attack_pos = candidate

        if attack_pos is None:
            print("No valid attack position within", attack_rsq,"radius square of enemy core")
            return None
        print("CLEARLY the best attack position is", attack_pos)
        return (((attack_pos.x) + 3) * 56 + ((attack_pos.y) + 3))

    @classmethod
    def nearest_source_to_enemy(cls):
        if not Symmetry.is_sym_known:
            return None, "C" # for cry
        maxr = 10
        cx = Symmetry.enemy_core_pos.x
        cy = Symmetry.enemy_core_pos.y
        for r in range(1, maxr + 1):
            # Walk the perimeter of the square at radius r
            for dx in range(-r, r + 1):
                for dy in range(-r, r + 1):
                    # Only visit cells on the edge of this ring
                    if abs(dx) != r and abs(dy) != r:
                        continue

                    x, y = cx + dx, cy + dy

                    # Skip out-of-bounds cells
                    if not (0 <= x < Map.W and 0 <= y < Map.H ):
                        continue

                    ti = Map.tile_info[x][y]
                    if ti is None:
                        continue
                    env = ti.env
                    thepos = Position(x, y)
                    if OreExecutive.state.get(thepos, 0) == 2: #killed
                        continue
                    if ti.entity_type == EntityType.FOUNDRY:
                        if thepos in cls.killed:
                            continue
                        return thepos, "R" # for just Route
                    if ti.entity_type in (EntityType.HARVESTER, EntityType.FOUNDRY):
                        continue
                    if ti.has_building and not ti.is_building_ally:
                        continue
                    if env == Environment.ORE_TITANIUM and not ti.has_turret:
                        return thepos, "B" # for build harvester

        return None, "C"  # Nothing found

    @classmethod
    def get_best_target(cls):
        if MarketMaker.est_income <= 10:
            return None

        if Symmetry.is_sym_known:
            if Globals.my_pos.distance_squared(Symmetry.enemy_core_pos) < 25: #sufficiently near
                cls.beenNearbyEnemyCore = True
            if Builder.mode == 2:
                if cls.beenNearbyEnemyCore and BuildManager.can_afford_harvester():
                    stuff = cls.nearest_source_to_enemy()
                    funPos = stuff[0]
                    if funPos == None or not VisionTracker.me_is_canonical_ally(funPos):
                        return None
                    return funPos, stuff[1] # <------- non move
                else:
                    return Explore.get_target(),'M' #move
        elif Builder.mode == 2:
            return Explore.get_target(),'M' #move
        return None