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
from Awubot.Globals import Globals, Cache
from Awubot.Map import LocalMask, MapMask, TileInfo, Map
from Awubot.MoveManager import MoveManager
from Awubot.RobotPlayer import Entrypoint, Player
from Awubot.Util import Util
from Awubot.build.Builder import BuilderState, Builder
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


class Core(Unit):
    @classmethod
    def init(cls):
        super().init()
        cls.num_spawned = 0

    @classmethod
    def start_turn(cls):
        super().start_turn()

    @classmethod
    def run_turn(cls):
        if cls.num_spawned < 3:
            pos = Globals.ct.get_position().add(random.choice(Constants.DIRECTIONS))
            if Globals.ct.can_spawn(pos):
                Globals.ct.spawn_builder(pos)
                cls.num_spawned += 1

    @classmethod
    def end_turn(cls):
        super().end_turn()


