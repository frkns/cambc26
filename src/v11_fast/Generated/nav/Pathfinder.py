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
from Awubot.Constants import Constants
from Awubot.Globals import Globals
from Awubot.MoveManager import MoveManager
from Awubot.Util import Util
from Awubot.debug.Profiler import Profiler
from Generated.Comms import Comms
from Generated.MarketMaker import MarketMaker
from Generated.RobotPlayer import Entrypoint, Player
from Generated.Unit import Unit
from Generated.builder.BuildManager import BuildManager
from Generated.builder.Builder import BuilderState, Builder
from Generated.builder.OreExecutive import OreExecutive
from Generated.builder.OrePositionPicker import OrePositionPicker
from Generated.builder.RouteToCore import RouteToCore
from Generated.builder.SuicideExecutor import SuicideExecutor
from Generated.core.Core import Core
from Generated.debug.Debug import Color, Debug
from Generated.explore.Explore import Explore
from Generated.heal.HealExecutor import HealExecutor
from Generated.map.DarkForest import TreeNode, DarkForest
from Generated.map.Map import TileInfo, Map
from Generated.map.Symmetry import Sym, Symmetry
from Generated.nav.BfsBureau import BfsBureau
from Generated.nav.DirectionPicker import DirectionPicker
from Generated.nav.Pathfinder import Pathfinder
# ===--- IMPORT



class Pathfinder:
    cur_target = None
    given_up: bool

    @classmethod
    def reset(cls):
        cls.given_up = False

    @classmethod
    def move_to(cls, target: Position, ban_target_pos: bool = False):
        if Globals.ct.get_move_cooldown() != 0:
            return

        if target != cls.cur_target:
            cls.reset()
            cls.cur_target = target

        Debug.line(target)
        my_pos = Globals.ct.get_position()

        Profiler.start()
        dist, dir = BfsBureau.find_route(Globals.ct.get_position(), target, ban_target_pos)
        Profiler.end("""BfsBureau.find_route""")

        if dir is None:
            cls.given_up = True
        else:
            if MoveManager.can_move(dir):
                MoveManager.move(dir)
            elif MoveManager.can_fill_move(dir):
                Globals.ct.build_road(my_pos.add(dir))
                MoveManager.move(dir)

