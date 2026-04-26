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
        cls.ti, cls.ax = Globals.ct.get_global_resources()

        idx = Globals.round % 20
        cls.ti_hist[idx] = cls.ti
        cls.ti_diff_hist[idx] = cls.ti - cls.ti_hist[
            idx-1 if idx-1 >= 0 else idx-1+20
        ]
        cls.est_income = max(cls.ti_diff_hist)





    # cache
    hpos: Position | None = None
    hround: int = -1000
    hres: int = -1000

    @classmethod
    def harvester_cost(cls, apos: Position) -> int:

        if (
            cls.hpos is not None 
            and Globals.round - cls.hround < 5
            and apos.distance_squared(cls.hpos) < 50
        ):
            return cls.hres

        
        Profiler.start()
        bridges, _ = BfsBureau.find_bridge_route(apos, DarkForest.core_sink_set)
        Profiler.end(f"""BfsBureau.find_bridge_route""")
        h_cost, _ = Globals.ct.get_harvester_cost()
        b_cost, _ = Globals.ct.get_bridge_cost()
        cls.hres = h_cost + b_cost * bridges 
        cls.hpos = apos
        cls.hround = Globals.round
        return cls.hres

    @staticmethod
    def harvester_payback(apos: Position, cost: int = None) -> int:
        l1 = abs(apos.x - Unit.core_pos.x) + abs(apos.y - Unit.core_pos.y)
        if cost is None:
            cost = MarketMaker.harvester_cost(apos)
        return int(cost / 2.5) + (2 * l1)


    @staticmethod
    def should_build_ax_harvester(apos: Position) -> int:
        if Globals.round < 500 and \
                apos.distance_squared(Symmetry.enemy_core_pos) < apos.distance_squared(Unit.core_pos):
            return False

        n_ti = len(Map.ti_ally_harvester_set)
        n_ax = len(Map.ax_ally_harvester_set)

        if not (2 * n_ax <= n_ti):
            return False

        if MarketMaker.ax > 0:
            pbt = MarketMaker.harvester_payback(apos)
            if int(pbt * 1.5 + 100) < Util.get_rounds_left():
                return True

        return False


    @staticmethod
    def should_build_harvester(apos: Position) -> int:
        if Globals.round < 500 and \
                apos.distance_squared(Symmetry.enemy_core_pos) < apos.distance_squared(Unit.core_pos):
            return False

        pbt = MarketMaker.harvester_payback(apos)

        if int(pbt * 1.5 + 100) < Util.get_rounds_left():
            return True
        return False
