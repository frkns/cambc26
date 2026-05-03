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

class Unit:

    core_pos: Position
    core_pos_list: list[tuple[int, int]]
    core_pos_set: set[int]

    on_pong: bool = False

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
        BfsBureau.init()

        if Globals.my_type in (EntityType.BUILDER_BOT, EntityType.CORE):
            Unit.core_pos_init()
            Symmetry.predict_enemy_core()
        else:
            cls.core_pos_set = set()

        if Globals.my_type in (EntityType.BUILDER_BOT, EntityType.CORE) and (Map.maxX, Map.maxY) == (49, 34):
            cx, cy = cls.core_pos.x, cls.core_pos.y
            isA = Globals.ct.get_team() == Team.A

            if (isA and (cx, cy) == (8, 8)) or (not isA and (cx, cy) == (41, 8)):
                PongManager.init()
                Debug.log('PONG detected!!')
                cls.on_pong = True


    @classmethod
    def start_turn(cls):
        if cls.on_pong:
            Globals.start_tick()
            PongManager.run()
            raise NotImplementedError

        Globals.start_tick()
        MarketMaker.refresh()

        if Globals.ct.get_entity_type() != EntityType.LAUNCHER:
            Profiler.start(f"""Map.fill_tile_info""")
            Map.fill_tile_info()
            Profiler.end(f"""Map.fill_tile_info""")

        Profiler.start_turn_check()

    @classmethod
    def run_turn(cls):
        pass

    @classmethod
    def end_turn(cls):

        if Globals.round == 667:
            Profiler.report()
        print(f'scale ratio {MarketMaker.scale_ratio:.2f}')

