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


class Explore:
    target: Position
    target = None

    @classmethod
    def init(cls) -> None:
        cls.target = cls.new_target()

    @classmethod
    def new_target(cls) -> Position:
        # return random.choice((Position(0, 0), Position(Map.W - 1, Map.H - 1)))
        # return Util.rand_pos()
        return random.choice((
            Position(0, 0),
            Position(0, Map.maxY),
            Position(Map.maxX, 0),
            Position(Map.maxX, Map.maxY),
        ))

    @classmethod
    def get_target(cls) -> Position:
        if Globals.ct.get_position().distance_squared(cls.target) <= 2:
            cls.target = cls.new_target()

        return cls.target
