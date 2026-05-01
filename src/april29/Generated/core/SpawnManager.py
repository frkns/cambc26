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

class SpawnManager:
    nearest_dangerous_enemy: Position | None
    dangerous_enemy_counter: int = 0
    last_spawned: int = 0

    # persistent
    num_spawned: int = 0


    @classmethod
    def fill(cls):
        my_pos = Globals.my_pos
        dist = 1000000
        enemy = None

        for pos, x, y, idx, ti in Map.proc_nearby_tiles:
            ti: TileInfo

            if not ti.entity_type in Constants.ATTACKABLE_TRANSPORTERS_SET:
                continue
            if not (ti.has_bot and not ti.is_bot_ally):
                continue
            if ti.allied_bots_adjacent > 0:
                continue

            # Calculate the distance first
            d = my_pos.distance_squared(pos)

            if enemy is None or d < dist:
                dist = d
                enemy = pos

        cls.nearest_dangerous_enemy = enemy
        
        if cls.nearest_dangerous_enemy != None:
            cls.dangerous_enemy_counter += 1
        else:
            cls.dangerous_enemy_counter = 0




    @classmethod
    def spawn(cls):
        # rework this
        my_pos = Globals.my_pos

        pos = my_pos.add(Direction.CENTRE)

        if Globals.ct.can_spawn(pos):
            Globals.ct.spawn_builder(pos)
            cls.num_spawned += 1
            cls.dangerous_enemy_counter = 0
            cls.last_spawned = Globals.round
        pos = my_pos.add(Direction.NORTHWEST)

        if Globals.ct.can_spawn(pos):
            Globals.ct.spawn_builder(pos)
            cls.num_spawned += 1
            cls.dangerous_enemy_counter = 0
            cls.last_spawned = Globals.round
        pos = my_pos.add(Direction.WEST)

        if Globals.ct.can_spawn(pos):
            Globals.ct.spawn_builder(pos)
            cls.num_spawned += 1
            cls.dangerous_enemy_counter = 0
            cls.last_spawned = Globals.round
        pos = my_pos.add(Direction.SOUTHWEST)

        if Globals.ct.can_spawn(pos):
            Globals.ct.spawn_builder(pos)
            cls.num_spawned += 1
            cls.dangerous_enemy_counter = 0
            cls.last_spawned = Globals.round
        pos = my_pos.add(Direction.SOUTH)

        if Globals.ct.can_spawn(pos):
            Globals.ct.spawn_builder(pos)
            cls.num_spawned += 1
            cls.dangerous_enemy_counter = 0
            cls.last_spawned = Globals.round
        pos = my_pos.add(Direction.SOUTHEAST)

        if Globals.ct.can_spawn(pos):
            Globals.ct.spawn_builder(pos)
            cls.num_spawned += 1
            cls.dangerous_enemy_counter = 0
            cls.last_spawned = Globals.round
        pos = my_pos.add(Direction.EAST)

        if Globals.ct.can_spawn(pos):
            Globals.ct.spawn_builder(pos)
            cls.num_spawned += 1
            cls.dangerous_enemy_counter = 0
            cls.last_spawned = Globals.round
        pos = my_pos.add(Direction.NORTHEAST)

        if Globals.ct.can_spawn(pos):
            Globals.ct.spawn_builder(pos)
            cls.num_spawned += 1
            cls.dangerous_enemy_counter = 0
            cls.last_spawned = Globals.round
        pos = my_pos.add(Direction.NORTH)

        if Globals.ct.can_spawn(pos):
            Globals.ct.spawn_builder(pos)
            cls.num_spawned += 1
            cls.dangerous_enemy_counter = 0
            cls.last_spawned = Globals.round


    @classmethod
    def should_spawn(cls):
        ct = Globals.ct
        num_units = ct.get_unit_count()

        ti, ax = ct.get_global_resources()
        bot_ti, bot_ax = ct.get_builder_bot_cost()

        if Globals.round <= 20 or MarketMaker.ti <= 10:
            return cls.num_spawned < 4

        rem_ti = ti - bot_ti

        if rem_ti >= int(cls.require_leftover() * MarketMaker.scale_ratio):
            return True

        return False


    @classmethod
    def require_leftover(cls):
        if cls.num_spawned < 8:
            return 100
        if cls.num_spawned < 16:
            return 120
        return 120 + (10 * ct.get_unit_count())


    @classmethod
    def should_spawn_emergency(cls):
        if cls.dangerous_enemy_counter >= 5 or (cls.dangerous_enemy_counter >= 1 and cls.last_spawned - Globals.round >= 5):
            return True
        
        lost_short = CoreHistory.hp_delta(1) < 0 
        lost_long = CoreHistory.hp_delta(10) < 0 
        low_hp = Globals.ct.get_hp() < 450

        if (lost_short or lost_long) and low_hp:
            return True

        return False






