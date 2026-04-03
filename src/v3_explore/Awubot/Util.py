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
from Awubot.build.Builder import BuilderState, Builder
from Awubot.core.Core import Core
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


class Util:
    @staticmethod
    def on_the_map(pos: Position) -> bool:
        return 0 <= pos.x < Map.W and 0 <= pos.y < Map.H

    @staticmethod
    def rand_pos() -> Position:
        return Position(random.randrange(Map.W), random.randrange(Map.H))


    @staticmethod
    def is_cardinal(dir: Direction) -> bool:
        # not great, to optimise, create polyfill for Direction
        dx, dy = dir.delta()
        return (dx == 0) ^ (dy == 0)

    @staticmethod
    def is_diagonal(dir: Direction) -> bool:
        dx, dy = dir.delta()
        return dx != 0 and dy != 0

    @staticmethod
    def get_rounds_left() -> int:
        return 2000 - Globals.round
