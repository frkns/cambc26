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

class MoveManager:
    @staticmethod
    def can_move(direction: Direction) -> bool:
        if direction == Direction.CENTRE:
            return True
        return Globals.ct.can_move(direction)

    @staticmethod
    def can_fill_move(direction: Direction) -> bool:
        if MoveManager.can_move(direction):
            return True
        if Globals.ct.get_action_cooldown() != 0:
            return False

        pos: Position = Globals.my_pos.add(direction)
        if not Util.on_the_map(pos):
            return False

        if not BuildManager.can_build_road(pos):
            return False

        ti: TileInfo = Map.tile_info[pos.x][pos.y]  # type: ignore
        if ti.has_building or ti.has_bot:
            return False

        return True


    @staticmethod
    def move(direction: Direction):
        if direction == Direction.CENTRE:
            return
        Globals.ct.move(direction)
        Globals.my_pos = Globals.ct.get_position()


    @classmethod
    def debug_moves(cls):
        print('can_move')
        print(f'N:{cls.can_move(Direction.NORTH)}', end=' ')
        print(f'NE:{cls.can_move(Direction.NORTHEAST)}', end=' ')
        print(f'E:{cls.can_move(Direction.EAST)}', end=' ')
        print(f'SE:{cls.can_move(Direction.SOUTHEAST)}', end=' ')
        print(f'S:{cls.can_move(Direction.SOUTH)}', end=' ')
        print(f'SW:{cls.can_move(Direction.SOUTHWEST)}', end=' ')
        print(f'W:{cls.can_move(Direction.WEST)}', end=' ')
        print(f'NW:{cls.can_move(Direction.NORTHWEST)}', end=' ')
        print(f'C:{cls.can_move(Direction.CENTRE)}', end=' ')
        print()
        print('can_fill_move')
        print(f'N:{cls.can_fill_move(Direction.NORTH)}', end=' ')
        print(f'NE:{cls.can_fill_move(Direction.NORTHEAST)}', end=' ')
        print(f'E:{cls.can_fill_move(Direction.EAST)}', end=' ')
        print(f'SE:{cls.can_fill_move(Direction.SOUTHEAST)}', end=' ')
        print(f'S:{cls.can_fill_move(Direction.SOUTH)}', end=' ')
        print(f'SW:{cls.can_fill_move(Direction.SOUTHWEST)}', end=' ')
        print(f'W:{cls.can_fill_move(Direction.WEST)}', end=' ')
        print(f'NW:{cls.can_fill_move(Direction.NORTHWEST)}', end=' ')
        print(f'C:{cls.can_fill_move(Direction.CENTRE)}', end=' ')
        print()