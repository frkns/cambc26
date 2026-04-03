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



class SpawnManager:
    num_spawned: int = 0

    @classmethod
    def spawn(cls):
        # rework this
        pos = Globals.my_pos.add(random.choice(Constants.DIRECTIONS))
        if Globals.ct.can_spawn(pos):
            Globals.ct.spawn_builder(pos)
            cls.num_spawned += 1

    @classmethod
    def should_spawn(cls):
        ct = Globals.ct
        num_units = ct.get_unit_count()

        ti, ax = ct.get_global_resources()
        bot_ti, bot_ax = ct.get_builder_bot_cost()

        if Globals.round <= 10 and cls.num_spawned < 5:
            return True

        if ti - bot_ti >= num_units * 100:
            return True

        return False


    @classmethod
    def should_spawn_emergency(cls):
        lost_short = CoreHistory.hp_delta(1) < 0 
        lost_long = CoreHistory.hp_delta(10) < 0 
        low_hp = Globals.ct.get_hp() < 450

        if (lost_short or lost_long) and low_hp:
            return True

        return False


