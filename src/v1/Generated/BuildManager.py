from cambc import Team, EntityType, Direction, Position, ResourceType, Environment, GameConstants, GameError, Controller
import random
import heapq
import array
import time
import math
import sys
from collections import deque, defaultdict
from typing import NamedTuple
from Awubot.Builder import BuilderState, Builder
from Awubot.Constants import Constants
from Awubot.Core import Core
from Awubot.Globals import Globals, Cache
from Awubot.Map import LocalMask, MapMask, TileInfo, Map
from Awubot.MoveManager import MoveManager
from Awubot.RobotPlayer import Entrypoint, Player
from Awubot.Unit import Unit
from Awubot.Util import Util
from Awubot.debug.Debug import Color, Debug
from Awubot.debug.Profiler import Profiler
from Awubot.explore.Explore import Explore
from Awubot.nav.DirectionPicker import DirectionPicker
from Awubot.nav.OmNom import OmNom


class BuildManager:
    reserve_ti: int = 100  # scale this
    reserve_ax: int = 0

    @staticmethod
    def scale(cost: int) -> int:
        return int(cost * Globals.ct.get_scale_percent() / 100.0)



    @classmethod
    def reserve_check_builder_bot(cls) -> bool:
        ti_cost, ax_cost = Globals.ct.get_builder_bot_cost()
        if (Cache.ti - ti_cost) < cls.reserve_ti * Cache.scale_ratio:
            return False
        if (Cache.ax - ax_cost) < cls.reserve_ax * Cache.scale_ratio:
            Debug.log('ax branch triggered')
            return False
        return True


    @classmethod
    def reserve_check_gunner(cls) -> bool:
        ti_cost, ax_cost = Globals.ct.get_gunner_cost()
        if (Cache.ti - ti_cost) < cls.reserve_ti * Cache.scale_ratio:
            return False
        if (Cache.ax - ax_cost) < cls.reserve_ax * Cache.scale_ratio:
            Debug.log('ax branch triggered')
            return False
        return True


    @classmethod
    def reserve_check_sentinel(cls) -> bool:
        ti_cost, ax_cost = Globals.ct.get_sentinel_cost()
        if (Cache.ti - ti_cost) < cls.reserve_ti * Cache.scale_ratio:
            return False
        if (Cache.ax - ax_cost) < cls.reserve_ax * Cache.scale_ratio:
            Debug.log('ax branch triggered')
            return False
        return True


    @classmethod
    def reserve_check_breach(cls) -> bool:
        ti_cost, ax_cost = Globals.ct.get_breach_cost()
        if (Cache.ti - ti_cost) < cls.reserve_ti * Cache.scale_ratio:
            return False
        if (Cache.ax - ax_cost) < cls.reserve_ax * Cache.scale_ratio:
            Debug.log('ax branch triggered')
            return False
        return True


    @classmethod
    def reserve_check_launcher(cls) -> bool:
        ti_cost, ax_cost = Globals.ct.get_launcher_cost()
        if (Cache.ti - ti_cost) < cls.reserve_ti * Cache.scale_ratio:
            return False
        if (Cache.ax - ax_cost) < cls.reserve_ax * Cache.scale_ratio:
            Debug.log('ax branch triggered')
            return False
        return True


    @classmethod
    def reserve_check_conveyor(cls) -> bool:
        ti_cost, ax_cost = Globals.ct.get_conveyor_cost()
        if (Cache.ti - ti_cost) < cls.reserve_ti * Cache.scale_ratio:
            return False
        if (Cache.ax - ax_cost) < cls.reserve_ax * Cache.scale_ratio:
            Debug.log('ax branch triggered')
            return False
        return True


    @classmethod
    def reserve_check_splitter(cls) -> bool:
        ti_cost, ax_cost = Globals.ct.get_splitter_cost()
        if (Cache.ti - ti_cost) < cls.reserve_ti * Cache.scale_ratio:
            return False
        if (Cache.ax - ax_cost) < cls.reserve_ax * Cache.scale_ratio:
            Debug.log('ax branch triggered')
            return False
        return True


    @classmethod
    def reserve_check_armoured_conveyor(cls) -> bool:
        ti_cost, ax_cost = Globals.ct.get_armoured_conveyor_cost()
        if (Cache.ti - ti_cost) < cls.reserve_ti * Cache.scale_ratio:
            return False
        if (Cache.ax - ax_cost) < cls.reserve_ax * Cache.scale_ratio:
            Debug.log('ax branch triggered')
            return False
        return True


    @classmethod
    def reserve_check_bridge(cls) -> bool:
        ti_cost, ax_cost = Globals.ct.get_bridge_cost()
        if (Cache.ti - ti_cost) < cls.reserve_ti * Cache.scale_ratio:
            return False
        if (Cache.ax - ax_cost) < cls.reserve_ax * Cache.scale_ratio:
            Debug.log('ax branch triggered')
            return False
        return True


    @classmethod
    def reserve_check_harvester(cls) -> bool:
        ti_cost, ax_cost = Globals.ct.get_harvester_cost()
        if (Cache.ti - ti_cost) < cls.reserve_ti * Cache.scale_ratio:
            return False
        if (Cache.ax - ax_cost) < cls.reserve_ax * Cache.scale_ratio:
            Debug.log('ax branch triggered')
            return False
        return True


    @classmethod
    def reserve_check_foundry(cls) -> bool:
        ti_cost, ax_cost = Globals.ct.get_foundry_cost()
        if (Cache.ti - ti_cost) < cls.reserve_ti * Cache.scale_ratio:
            return False
        if (Cache.ax - ax_cost) < cls.reserve_ax * Cache.scale_ratio:
            Debug.log('ax branch triggered')
            return False
        return True


    @classmethod
    def reserve_check_road(cls) -> bool:
        ti_cost, ax_cost = Globals.ct.get_road_cost()
        if (Cache.ti - ti_cost) < cls.reserve_ti * Cache.scale_ratio:
            return False
        if (Cache.ax - ax_cost) < cls.reserve_ax * Cache.scale_ratio:
            Debug.log('ax branch triggered')
            return False
        return True


    @classmethod
    def reserve_check_barrier(cls) -> bool:
        ti_cost, ax_cost = Globals.ct.get_barrier_cost()
        if (Cache.ti - ti_cost) < cls.reserve_ti * Cache.scale_ratio:
            return False
        if (Cache.ax - ax_cost) < cls.reserve_ax * Cache.scale_ratio:
            Debug.log('ax branch triggered')
            return False
        return True



