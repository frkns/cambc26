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



class StateBuildHarvester:
    @classmethod
    def run(cls, pos):
        OreExecutive.go_build_harvester(pos)


class StateAttackTransporter:
    @classmethod
    def run(cls, pos):
        Pathfinder.move_to(pos)

        if Globals.my_pos == pos:
            if Globals.ct.can_fire(pos):
                Globals.ct.fire(pos)


class StateRoute:
    @classmethod
    def run(cls):
        RouteToCore.do_routing()


class StateMoveTo:
    @classmethod
    def run(cls, pos, tag='_'):
        Pathfinder.move_to(pos)


class StateBuildTurret:
    @classmethod
    def run(cls, pos, banned_dir: Direction | None):
        Pathfinder.move_to(pos, ban_target_pos=True)

        if BuildManager.can_dbuild_sentinel(pos):

            # download better dir logic soon
            dir: Direction = pos.direction_to(Symmetry.enemy_core_pos) 
            if dir == banned_dir:
                dir = dir.rotate_left() if random.random() < 0.5 else dir.rotate_right()

            BuildManager.dbuild_sentinel(pos, dir)
