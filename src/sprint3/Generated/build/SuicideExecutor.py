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


class SuicideExecutor:
    @staticmethod
    def execute_suicide_attempt():
        cond = MarketMaker.scale_ratio > 3
        strong_cond = MarketMaker.ti > 800 and MarketMaker.scale_ratio > 3 and Map.nearby_ally_bots > 5

        my_pos = Globals.my_pos
        ti = Map.tile_info[my_pos.x][my_pos.y]

        if not (ti.has_building and not ti.is_building_ally):
            return

        if ti.entity_type in Constants.TRANSPORTERS_SET and cond:
            Globals.ct.self_destruct()

        if ti.entity_type == EntityType.ROAD and strong_cond:
            Globals.ct.self_destruct()
            