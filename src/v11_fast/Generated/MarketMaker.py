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



class MarketMaker:
    ti: int
    ax: int
    scale_ratio: float

    ti_hist: list[int] = [GameConstants.STARTING_TITANIUM] * 20
    ti_diff_hist: list[int] = [0] * 20
    est_income: int

    @classmethod
    def refresh(cls):
        cls.scale_ratio = Globals.ct.get_scale_percent() / 100.0
        cls.ti, MarketMaker.ax = Globals.ct.get_global_resources()

        idx = Globals.round % 20
        cls.ti_hist[idx] = cls.ti
        cls.ti_diff_hist[idx] = cls.ti - cls.ti_hist[
            idx-1 if idx-1 >= 0 else idx-1+20
        ]
        cls.est_income = max(cls.ti_diff_hist)





    @staticmethod
    def harvester_payback(apos: Position) -> int:
        l1 = abs(apos.x - Unit.core_pos.x) + abs(apos.y - Unit.core_pos.y)
        Profiler.start()
        bridges, _ = BfsBureau.find_bridge_route(Globals.ct.get_position(), DarkForest.sink_set)
        Profiler.end("""BfsBureau.find_bridge_route""")
        h_cost, _ = Globals.ct.get_harvester_cost()
        b_cost, _ = Globals.ct.get_bridge_cost()
        cost = h_cost + b_cost * bridges
        return int(cost / 2.5) + (2 * l1)


    @staticmethod
    def should_build_harvester(apos: Position) -> int:
        pbt = MarketMaker.harvester_payback(apos)
        print(f"""{pbt=}""")

        if int(pbt * 1.5 + 100) < Util.get_rounds_left():
            return True
        return False
