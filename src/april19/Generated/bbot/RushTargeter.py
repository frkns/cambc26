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

    @classmethod
    def enemy_core_turret_target(cls, attack_r_sq) -> Position | None:
        if not Symmetry.is_sym_known:
            return None
        enemy_core = Symmetry.enemy_core_pos
        print("Yo so the enemy core is at", enemy_core)

        vision_r = int(attack_r_sq ** 0.5) + 1

        # ── Step 1: pick best attack landing position ────────────────
        attack_pos = None
        best_attack_dist = float('inf')
        currLoc = Globals.my_pos
        for dx in range(-vision_r, vision_r + 1):
            for dy in range(-vision_r, vision_r + 1):
                if dx * dx + dy * dy >attack_r_sq:
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
            print("No valid attack position within",attack_r_sq,"radius square of enemy core")
            return None
        print("CLEARLY the best attack position is", attack_pos)
        return (((attack_pos.x) + 3) * 56 + ((attack_pos.y) + 3))

    @classmethod
    def nearest_titanium_to_enemy(cls) -> Position | None:
        if not Symmetry.is_sym_known:
            return None
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
                    if OreExecutive.state[thepos] == 2: #killed
                        continue
                    if ti.entity_type in [EntityType.HARVESTER,EntityType.FOUNDRY]:
                        continue
                    if ti.has_building and not ti.is_building_ally and ti.entity_type != EntityType.MARKER:
                        continue
                    if env == Environment.ORE_TITANIUM:
                        return thepos

        return None  # Nothing found

    @classmethod
    def get_best_target(cls):
        if Symmetry.is_sym_known:
            if Globals.my_pos.distance_squared(Symmetry.enemy_core_pos) < 25: #sufficiently near
                cls.beenNearbyEnemyCore = True
            if Builder.mode == 2:
                if cls.beenNearbyEnemyCore:
                    funPos = cls.nearest_titanium_to_enemy()
                    if funPos == None:
                        return Explore.get_target(),'M' #move
                    return funPos,'B' #build harvester
                else:
                    return Explore.get_target(),'M' #move
            if (Globals.my_id % 3 == 0 and BuildManager.can_afford_sentinel() and MarketMaker.est_income >= 50 and Globals.round > 100):
                return Symmetry.enemy_core_pos,'M' #move
        elif Builder.mode == 2:
            return Symmetry.sym_pos(Unit.core_pos),'M' #move
        return None