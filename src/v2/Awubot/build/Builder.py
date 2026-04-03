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
from Awubot.Constants import Constants
from Awubot.Core import Core
from Awubot.Globals import Globals, Cache
from Awubot.Map import LocalMask, MapMask, TileInfo, Map
from Awubot.MoveManager import MoveManager
from Awubot.RobotPlayer import Entrypoint, Player
from Awubot.Util import Util
from Awubot.debug.Profiler import Profiler
from Awubot.explore.Explore import Explore
from Awubot.nav.Pathfinder import Pathfinder
from Generated.Unit import Unit
from Generated.build.BuildManager import BuildManager
from Generated.build.OreExecutive import OreExecutive
from Generated.build.OrePositionPicker import OrePositionPicker
from Generated.build.RouteToCore import RouteToCore
from Generated.debug.Debug import Color, Debug
from Generated.nav.ClaudeGlobalBfs import ClaudeGlobalBfs
from Generated.nav.DirectionPicker import DirectionPicker
from Generated.nav.EgoBridgeBfs import EgoBridgeBfs


class BuilderState(Enum):
    UNKNOWN = 0
    EXPLORE = 1
    ROUTE = 2
    BUILD_HARVESTER = 3


class Builder(Unit):
    state: BuilderState | int
    state_map: dict

    @classmethod
    def init(cls):
        super().init()
        Explore.init()

        cls.state_map = {
            BuilderState.EXPLORE: cls.state_explore,
            BuilderState.BUILD_HARVESTER: cls.state_build_harvester,
            BuilderState.ROUTE: cls.state_route,
        }
        cls.state = BuilderState.EXPLORE


    @classmethod
    def start_turn(cls):
        super().start_turn()

    @classmethod
    def run_turn(cls):
        cls.state, pos = cls.determine_state()
        cls.state_map[cls.state](pos)

    @classmethod
    def end_turn(cls):
        super().end_turn()

    @classmethod
    def state_explore(cls, pos):
        Pathfinder.move_to(pos, ban_target_pos=True)  # change to false

    @classmethod
    def state_route(cls, _):
        RouteToCore.do_routing()

    @classmethod
    def state_build_harvester(cls, pos):
        OreExecutive.go_build_harvester(pos)

    @classmethod
    def determine_state(cls):
        if RouteToCore.is_active:
            return BuilderState.ROUTE, None

        hpos = OreExecutive.find_ore_to_mine()
        if hpos is not None:
            return BuilderState.BUILD_HARVESTER, hpos


        return BuilderState.EXPLORE, Explore.get_target()

