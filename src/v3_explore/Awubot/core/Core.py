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
from Generated.debug.Debug import Color, Debug
from Generated.heal.HealExecutor import HealExecutor
from Generated.nav.ClaudeGlobalBfs import ClaudeGlobalBfs
from Generated.nav.DirectionPicker import DirectionPicker
from Generated.nav.EgoBridgeBfs import EgoBridgeBfs


class Core(Unit):
    num_spawned: int = 0

    @classmethod
    def init(cls):
        super().init()

    @classmethod
    def start_turn(cls):
        super().start_turn()
        print(f'est income: {MarketMaker.est_income}')


    @classmethod
    def spawn(cls):
        # rework this
        pos = Globals.ct.get_position().add(random.choice(Constants.DIRECTIONS))
        if Globals.ct.can_spawn(pos):
            Globals.ct.spawn_builder(pos)
            cls.num_spawned += 1

    @classmethod
    def run_turn(cls):
        if cls.num_spawned < 3 or MarketMaker.ti > 1000:
            cls.spawn()

    @classmethod
    def end_turn(cls):
        super().end_turn()


