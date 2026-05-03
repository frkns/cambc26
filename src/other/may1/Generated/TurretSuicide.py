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

# disintegrate if we have no feeder and no ammo for X rounds and far away from enemy core

class TurretSuicide:
    has_ammo_history: list[bool]
    enemy_core_visible: bool
    post_init_completed: bool
    has_feeder: bool
    

    @classmethod
    def init(cls):
        cls.has_ammo_history = [True] * 20
        cls.enemy_core_visible = False
        cls.post_init_completed = False


    @classmethod
    def post_init(cls):
        # hack
        for pos, x, y, idx, ti in Map.proc_nearby_tiles:
            ti: TileInfo
            if ti.entity_type == EntityType.CORE and not ti.is_building_ally:
                cls.enemy_core_visible = True
                break
        cls.post_init_completed = True


    @classmethod
    def update_and_check(cls):
        if not cls.post_init_completed:
            cls.post_init()

        my_pos = Globals.my_pos
        sx, sy = my_pos.x, my_pos.y

        r = Globals.round % 20
        cls.has_ammo_history[r] = Globals.ct.get_ammo_amount() > 0

        cls.has_feeder = Map.tile_info[sx][sy].harvester_adjacent
        for pos, x, y, idx, ti in Map.proc_nearby_tiles:
            ti: TileInfo
            if ti.target == my_pos:
                cls.has_feeder = True
                break

        if not cls.has_feeder and not cls.enemy_core_visible and not any(cls.has_ammo_history):
            Debug.diamond(Color.ORANGE)
            Debug.log(f'This {Globals.my_type} is self-destructing :(')
            Globals.ct.self_destruct()
            raise NotImplementedError
