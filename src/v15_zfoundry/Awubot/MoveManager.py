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
from Awubot.Util import Util
# ===--- IMPORT


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

        if not Globals.ct.can_build_road(pos):
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
