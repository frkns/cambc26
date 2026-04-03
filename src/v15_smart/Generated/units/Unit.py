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



class Unit:
    core_pos: Position
    core_pos_list: list[tuple[int, int]]
    core_pos_set: set[int]

    @staticmethod
    def core_pos_init():
        core_id = Globals.ct.get_tile_building_id(Globals.my_pos)
        Unit.core_pos = Globals.ct.get_position(core_id)
        x = Unit.core_pos.x
        y = Unit.core_pos.y
        Unit.core_pos_list = [
            (x , y -1),
            (x +1, y -1),
            (x +1, y ),
            (x +1, y +1),
            (x , y +1),
            (x -1, y +1),
            (x -1, y ),
            (x -1, y -1),
            (x , y ),
        ]
        idx = (((x) + 3) * 56 + ((y) + 3))
        Unit.core_pos_set = {
            idx -1,
            idx +55,
            idx +56,
            idx +57,
            idx +1,
            idx -55,
            idx -56,
            idx -57,
            idx ,
        }


    @classmethod
    def init(cls):
        random.seed(Globals.my_id)
        if Globals.my_type == EntityType.BUILDER_BOT:
            Unit.core_pos_init()
            BfsBureau.init()
            Symmetry.predict_enemy_core()
        else:
            cls.core_pos_set = set()


    @classmethod
    def start_turn(cls):
        Globals.start_tick()
        MarketMaker.refresh()

        
        Map.fill_tile_info()
        

    @classmethod
    def run_turn(cls):
        pass

    @classmethod
    def end_turn(cls):

        if Globals.round == 1999:
            Profiler.report()
        print(f'scale ratio {MarketMaker.scale_ratio:.2f}')

