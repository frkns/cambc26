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
from Awubot.Constants import Constants
from Awubot.Globals import Globals
from Awubot.Map import TileInfo, Map
from Awubot.MoveManager import MoveManager
from Awubot.Util import Util
from Awubot.build.Builder import BuilderState, Builder
from Awubot.debug.Profiler import Profiler
from Awubot.explore.Explore import Explore
from Awubot.nav.Pathfinder import Pathfinder
from Generated.MarketMaker import MarketMaker
from Generated.RobotPlayer import Entrypoint, Player
from Generated.Unit import Unit
from Generated.build.BuildManager import BuildManager
from Generated.build.OreExecutive import OreExecutive
from Generated.build.OrePositionPicker import OrePositionPicker
from Generated.build.RouteToCore import RouteToCore
from Generated.build.SuicideExecutor import SuicideExecutor
from Generated.core.Core import Core
from Generated.debug.Debug import Color, Debug
from Generated.heal.HealExecutor import HealExecutor
from Generated.nav.BfsBureau import BfsBureau
from Generated.nav.DirectionPicker import DirectionPicker


class BuildManager:
    reserve_ti: int = 100  # scale this
    reserve_ax: int = 0

    @staticmethod
    def scale(cost: int) -> int:
        return int(cost * MarketMaker.scale_ratio)

    @staticmethod
    def is_buildable(pos: Position):
        dsq = Globals.ct.get_position().distance_squared(pos)
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
        dsq = Globals.ct.get_position().distance_squared(pos)
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



    @staticmethod
    def build_builder_bot(*a):
        Globals.ct.build_builder_bot(*a)

    @staticmethod
    def dbuild_builder_bot(pos, *a):
        if Globals.ct.can_destroy(pos):
            Globals.ct.destroy(pos)
        Globals.ct.build_builder_bot(pos, *a)

    @staticmethod
    def can_dbuild_builder_bot(pos) -> bool:
        return (
            Globals.ct.get_action_cooldown() == 0 and
            BuildManager.is_dbuildable(pos) and 
            BuildManager.can_afford_builder_bot()
        )

    @staticmethod
    def can_build_builder_bot(*a) -> bool:
        return Globals.ct.can_build_builder_bot(*a)

    @staticmethod
    def can_afford_builder_bot() -> bool:
        ti_cost, ax_cost = Globals.ct.get_builder_bot_cost()
        return MarketMaker.ti >= ti_cost and MarketMaker.ax >= ax_cost

    @classmethod
    def reserve_check_builder_bot(cls) -> bool:
        ti_cost, ax_cost = Globals.ct.get_builder_bot_cost()
        if (MarketMaker.ti - ti_cost) < cls.reserve_ti * MarketMaker.scale_ratio:
            return False
        if (MarketMaker.ax - ax_cost) < cls.reserve_ax * MarketMaker.scale_ratio:
            Debug.log('ax branch triggered')
            return False
        return True


    @staticmethod
    def build_gunner(*a):
        Globals.ct.build_gunner(*a)

    @staticmethod
    def dbuild_gunner(pos, *a):
        if Globals.ct.can_destroy(pos):
            Globals.ct.destroy(pos)
        Globals.ct.build_gunner(pos, *a)

    @staticmethod
    def can_dbuild_gunner(pos) -> bool:
        return (
            Globals.ct.get_action_cooldown() == 0 and
            BuildManager.is_dbuildable(pos) and 
            BuildManager.can_afford_gunner()
        )

    @staticmethod
    def can_build_gunner(*a) -> bool:
        return Globals.ct.can_build_gunner(*a)

    @staticmethod
    def can_afford_gunner() -> bool:
        ti_cost, ax_cost = Globals.ct.get_gunner_cost()
        return MarketMaker.ti >= ti_cost and MarketMaker.ax >= ax_cost

    @classmethod
    def reserve_check_gunner(cls) -> bool:
        ti_cost, ax_cost = Globals.ct.get_gunner_cost()
        if (MarketMaker.ti - ti_cost) < cls.reserve_ti * MarketMaker.scale_ratio:
            return False
        if (MarketMaker.ax - ax_cost) < cls.reserve_ax * MarketMaker.scale_ratio:
            Debug.log('ax branch triggered')
            return False
        return True


    @staticmethod
    def build_sentinel(*a):
        Globals.ct.build_sentinel(*a)

    @staticmethod
    def dbuild_sentinel(pos, *a):
        if Globals.ct.can_destroy(pos):
            Globals.ct.destroy(pos)
        Globals.ct.build_sentinel(pos, *a)

    @staticmethod
    def can_dbuild_sentinel(pos) -> bool:
        return (
            Globals.ct.get_action_cooldown() == 0 and
            BuildManager.is_dbuildable(pos) and 
            BuildManager.can_afford_sentinel()
        )

    @staticmethod
    def can_build_sentinel(*a) -> bool:
        return Globals.ct.can_build_sentinel(*a)

    @staticmethod
    def can_afford_sentinel() -> bool:
        ti_cost, ax_cost = Globals.ct.get_sentinel_cost()
        return MarketMaker.ti >= ti_cost and MarketMaker.ax >= ax_cost

    @classmethod
    def reserve_check_sentinel(cls) -> bool:
        ti_cost, ax_cost = Globals.ct.get_sentinel_cost()
        if (MarketMaker.ti - ti_cost) < cls.reserve_ti * MarketMaker.scale_ratio:
            return False
        if (MarketMaker.ax - ax_cost) < cls.reserve_ax * MarketMaker.scale_ratio:
            Debug.log('ax branch triggered')
            return False
        return True


    @staticmethod
    def build_breach(*a):
        Globals.ct.build_breach(*a)

    @staticmethod
    def dbuild_breach(pos, *a):
        if Globals.ct.can_destroy(pos):
            Globals.ct.destroy(pos)
        Globals.ct.build_breach(pos, *a)

    @staticmethod
    def can_dbuild_breach(pos) -> bool:
        return (
            Globals.ct.get_action_cooldown() == 0 and
            BuildManager.is_dbuildable(pos) and 
            BuildManager.can_afford_breach()
        )

    @staticmethod
    def can_build_breach(*a) -> bool:
        return Globals.ct.can_build_breach(*a)

    @staticmethod
    def can_afford_breach() -> bool:
        ti_cost, ax_cost = Globals.ct.get_breach_cost()
        return MarketMaker.ti >= ti_cost and MarketMaker.ax >= ax_cost

    @classmethod
    def reserve_check_breach(cls) -> bool:
        ti_cost, ax_cost = Globals.ct.get_breach_cost()
        if (MarketMaker.ti - ti_cost) < cls.reserve_ti * MarketMaker.scale_ratio:
            return False
        if (MarketMaker.ax - ax_cost) < cls.reserve_ax * MarketMaker.scale_ratio:
            Debug.log('ax branch triggered')
            return False
        return True


    @staticmethod
    def build_launcher(*a):
        Globals.ct.build_launcher(*a)

    @staticmethod
    def dbuild_launcher(pos, *a):
        if Globals.ct.can_destroy(pos):
            Globals.ct.destroy(pos)
        Globals.ct.build_launcher(pos, *a)

    @staticmethod
    def can_dbuild_launcher(pos) -> bool:
        return (
            Globals.ct.get_action_cooldown() == 0 and
            BuildManager.is_dbuildable(pos) and 
            BuildManager.can_afford_launcher()
        )

    @staticmethod
    def can_build_launcher(*a) -> bool:
        return Globals.ct.can_build_launcher(*a)

    @staticmethod
    def can_afford_launcher() -> bool:
        ti_cost, ax_cost = Globals.ct.get_launcher_cost()
        return MarketMaker.ti >= ti_cost and MarketMaker.ax >= ax_cost

    @classmethod
    def reserve_check_launcher(cls) -> bool:
        ti_cost, ax_cost = Globals.ct.get_launcher_cost()
        if (MarketMaker.ti - ti_cost) < cls.reserve_ti * MarketMaker.scale_ratio:
            return False
        if (MarketMaker.ax - ax_cost) < cls.reserve_ax * MarketMaker.scale_ratio:
            Debug.log('ax branch triggered')
            return False
        return True


    @staticmethod
    def build_conveyor(*a):
        Globals.ct.build_conveyor(*a)

    @staticmethod
    def dbuild_conveyor(pos, *a):
        if Globals.ct.can_destroy(pos):
            Globals.ct.destroy(pos)
        Globals.ct.build_conveyor(pos, *a)

    @staticmethod
    def can_dbuild_conveyor(pos) -> bool:
        return (
            Globals.ct.get_action_cooldown() == 0 and
            BuildManager.is_dbuildable(pos) and 
            BuildManager.can_afford_conveyor()
        )

    @staticmethod
    def can_build_conveyor(*a) -> bool:
        return Globals.ct.can_build_conveyor(*a)

    @staticmethod
    def can_afford_conveyor() -> bool:
        ti_cost, ax_cost = Globals.ct.get_conveyor_cost()
        return MarketMaker.ti >= ti_cost and MarketMaker.ax >= ax_cost

    @classmethod
    def reserve_check_conveyor(cls) -> bool:
        ti_cost, ax_cost = Globals.ct.get_conveyor_cost()
        if (MarketMaker.ti - ti_cost) < cls.reserve_ti * MarketMaker.scale_ratio:
            return False
        if (MarketMaker.ax - ax_cost) < cls.reserve_ax * MarketMaker.scale_ratio:
            Debug.log('ax branch triggered')
            return False
        return True


    @staticmethod
    def build_splitter(*a):
        Globals.ct.build_splitter(*a)

    @staticmethod
    def dbuild_splitter(pos, *a):
        if Globals.ct.can_destroy(pos):
            Globals.ct.destroy(pos)
        Globals.ct.build_splitter(pos, *a)

    @staticmethod
    def can_dbuild_splitter(pos) -> bool:
        return (
            Globals.ct.get_action_cooldown() == 0 and
            BuildManager.is_dbuildable(pos) and 
            BuildManager.can_afford_splitter()
        )

    @staticmethod
    def can_build_splitter(*a) -> bool:
        return Globals.ct.can_build_splitter(*a)

    @staticmethod
    def can_afford_splitter() -> bool:
        ti_cost, ax_cost = Globals.ct.get_splitter_cost()
        return MarketMaker.ti >= ti_cost and MarketMaker.ax >= ax_cost

    @classmethod
    def reserve_check_splitter(cls) -> bool:
        ti_cost, ax_cost = Globals.ct.get_splitter_cost()
        if (MarketMaker.ti - ti_cost) < cls.reserve_ti * MarketMaker.scale_ratio:
            return False
        if (MarketMaker.ax - ax_cost) < cls.reserve_ax * MarketMaker.scale_ratio:
            Debug.log('ax branch triggered')
            return False
        return True


    @staticmethod
    def build_armoured_conveyor(*a):
        Globals.ct.build_armoured_conveyor(*a)

    @staticmethod
    def dbuild_armoured_conveyor(pos, *a):
        if Globals.ct.can_destroy(pos):
            Globals.ct.destroy(pos)
        Globals.ct.build_armoured_conveyor(pos, *a)

    @staticmethod
    def can_dbuild_armoured_conveyor(pos) -> bool:
        return (
            Globals.ct.get_action_cooldown() == 0 and
            BuildManager.is_dbuildable(pos) and 
            BuildManager.can_afford_armoured_conveyor()
        )

    @staticmethod
    def can_build_armoured_conveyor(*a) -> bool:
        return Globals.ct.can_build_armoured_conveyor(*a)

    @staticmethod
    def can_afford_armoured_conveyor() -> bool:
        ti_cost, ax_cost = Globals.ct.get_armoured_conveyor_cost()
        return MarketMaker.ti >= ti_cost and MarketMaker.ax >= ax_cost

    @classmethod
    def reserve_check_armoured_conveyor(cls) -> bool:
        ti_cost, ax_cost = Globals.ct.get_armoured_conveyor_cost()
        if (MarketMaker.ti - ti_cost) < cls.reserve_ti * MarketMaker.scale_ratio:
            return False
        if (MarketMaker.ax - ax_cost) < cls.reserve_ax * MarketMaker.scale_ratio:
            Debug.log('ax branch triggered')
            return False
        return True


    @staticmethod
    def build_bridge(*a):
        Globals.ct.build_bridge(*a)

    @staticmethod
    def dbuild_bridge(pos, *a):
        if Globals.ct.can_destroy(pos):
            Globals.ct.destroy(pos)
        Globals.ct.build_bridge(pos, *a)

    @staticmethod
    def can_dbuild_bridge(pos) -> bool:
        return (
            Globals.ct.get_action_cooldown() == 0 and
            BuildManager.is_dbuildable(pos) and 
            BuildManager.can_afford_bridge()
        )

    @staticmethod
    def can_build_bridge(*a) -> bool:
        return Globals.ct.can_build_bridge(*a)

    @staticmethod
    def can_afford_bridge() -> bool:
        ti_cost, ax_cost = Globals.ct.get_bridge_cost()
        return MarketMaker.ti >= ti_cost and MarketMaker.ax >= ax_cost

    @classmethod
    def reserve_check_bridge(cls) -> bool:
        ti_cost, ax_cost = Globals.ct.get_bridge_cost()
        if (MarketMaker.ti - ti_cost) < cls.reserve_ti * MarketMaker.scale_ratio:
            return False
        if (MarketMaker.ax - ax_cost) < cls.reserve_ax * MarketMaker.scale_ratio:
            Debug.log('ax branch triggered')
            return False
        return True


    @staticmethod
    def build_harvester(*a):
        Globals.ct.build_harvester(*a)

    @staticmethod
    def dbuild_harvester(pos, *a):
        if Globals.ct.can_destroy(pos):
            Globals.ct.destroy(pos)
        Globals.ct.build_harvester(pos, *a)

    @staticmethod
    def can_dbuild_harvester(pos) -> bool:
        return (
            Globals.ct.get_action_cooldown() == 0 and
            BuildManager.is_dbuildable(pos) and 
            BuildManager.can_afford_harvester()
        )

    @staticmethod
    def can_build_harvester(*a) -> bool:
        return Globals.ct.can_build_harvester(*a)

    @staticmethod
    def can_afford_harvester() -> bool:
        ti_cost, ax_cost = Globals.ct.get_harvester_cost()
        return MarketMaker.ti >= ti_cost and MarketMaker.ax >= ax_cost

    @classmethod
    def reserve_check_harvester(cls) -> bool:
        ti_cost, ax_cost = Globals.ct.get_harvester_cost()
        if (MarketMaker.ti - ti_cost) < cls.reserve_ti * MarketMaker.scale_ratio:
            return False
        if (MarketMaker.ax - ax_cost) < cls.reserve_ax * MarketMaker.scale_ratio:
            Debug.log('ax branch triggered')
            return False
        return True


    @staticmethod
    def build_foundry(*a):
        Globals.ct.build_foundry(*a)

    @staticmethod
    def dbuild_foundry(pos, *a):
        if Globals.ct.can_destroy(pos):
            Globals.ct.destroy(pos)
        Globals.ct.build_foundry(pos, *a)

    @staticmethod
    def can_dbuild_foundry(pos) -> bool:
        return (
            Globals.ct.get_action_cooldown() == 0 and
            BuildManager.is_dbuildable(pos) and 
            BuildManager.can_afford_foundry()
        )

    @staticmethod
    def can_build_foundry(*a) -> bool:
        return Globals.ct.can_build_foundry(*a)

    @staticmethod
    def can_afford_foundry() -> bool:
        ti_cost, ax_cost = Globals.ct.get_foundry_cost()
        return MarketMaker.ti >= ti_cost and MarketMaker.ax >= ax_cost

    @classmethod
    def reserve_check_foundry(cls) -> bool:
        ti_cost, ax_cost = Globals.ct.get_foundry_cost()
        if (MarketMaker.ti - ti_cost) < cls.reserve_ti * MarketMaker.scale_ratio:
            return False
        if (MarketMaker.ax - ax_cost) < cls.reserve_ax * MarketMaker.scale_ratio:
            Debug.log('ax branch triggered')
            return False
        return True


    @staticmethod
    def build_road(*a):
        Globals.ct.build_road(*a)

    @staticmethod
    def dbuild_road(pos, *a):
        if Globals.ct.can_destroy(pos):
            Globals.ct.destroy(pos)
        Globals.ct.build_road(pos, *a)

    @staticmethod
    def can_dbuild_road(pos) -> bool:
        return (
            Globals.ct.get_action_cooldown() == 0 and
            BuildManager.is_dbuildable(pos) and 
            BuildManager.can_afford_road()
        )

    @staticmethod
    def can_build_road(*a) -> bool:
        return Globals.ct.can_build_road(*a)

    @staticmethod
    def can_afford_road() -> bool:
        ti_cost, ax_cost = Globals.ct.get_road_cost()
        return MarketMaker.ti >= ti_cost and MarketMaker.ax >= ax_cost

    @classmethod
    def reserve_check_road(cls) -> bool:
        ti_cost, ax_cost = Globals.ct.get_road_cost()
        if (MarketMaker.ti - ti_cost) < cls.reserve_ti * MarketMaker.scale_ratio:
            return False
        if (MarketMaker.ax - ax_cost) < cls.reserve_ax * MarketMaker.scale_ratio:
            Debug.log('ax branch triggered')
            return False
        return True


    @staticmethod
    def build_barrier(*a):
        Globals.ct.build_barrier(*a)

    @staticmethod
    def dbuild_barrier(pos, *a):
        if Globals.ct.can_destroy(pos):
            Globals.ct.destroy(pos)
        Globals.ct.build_barrier(pos, *a)

    @staticmethod
    def can_dbuild_barrier(pos) -> bool:
        return (
            Globals.ct.get_action_cooldown() == 0 and
            BuildManager.is_dbuildable(pos) and 
            BuildManager.can_afford_barrier()
        )

    @staticmethod
    def can_build_barrier(*a) -> bool:
        return Globals.ct.can_build_barrier(*a)

    @staticmethod
    def can_afford_barrier() -> bool:
        ti_cost, ax_cost = Globals.ct.get_barrier_cost()
        return MarketMaker.ti >= ti_cost and MarketMaker.ax >= ax_cost

    @classmethod
    def reserve_check_barrier(cls) -> bool:
        ti_cost, ax_cost = Globals.ct.get_barrier_cost()
        if (MarketMaker.ti - ti_cost) < cls.reserve_ti * MarketMaker.scale_ratio:
            return False
        if (MarketMaker.ax - ax_cost) < cls.reserve_ax * MarketMaker.scale_ratio:
            Debug.log('ax branch triggered')
            return False
        return True



