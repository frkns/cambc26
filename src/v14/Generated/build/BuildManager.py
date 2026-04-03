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
from Generated.Constants import Constants
from Generated.MarketMaker import MarketMaker
from Generated.RobotPlayer import Entrypoint, Player
# ===--- IMPORT



class BuildManager:
    reserve_ti: int = 100  # scale this
    reserve_ax: int = 0

    @staticmethod
    def scale(cost: int) -> int:
        return int(cost * MarketMaker.scale_ratio)

    @staticmethod
    def is_buildable(pos: Position):
        dsq = Globals.my_pos.distance_squared(pos)
        if dsq > 2 or dsq == 0:
            return False

        ti = Map.tile_info[pos.x][pos.y]
        return (
            ti.env != Environment.WALL 
            and not ti.has_building
            and not ti.has_bot
        )

    @staticmethod
    def is_dbuildable(pos: Position):
        dsq = Globals.my_pos.distance_squared(pos)
        if dsq > 2 or dsq == 0:
            return False

        ti = Map.tile_info[pos.x][pos.y]

        if Globals.ct.can_destroy(pos) and not ti.has_bot:
            return True

        return (
            ti.env != Environment.WALL
            and not ti.has_bot
            and (not ti.has_building or (ti.is_building_ally and ti.entity_type != EntityType.CORE))
        )




