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
from Generated.nav.DialDijkstra import DialDijkstra
from Generated.nav.DirectionPicker import DirectionPicker
from Generated.nav.EgoBridgeBfs import EgoBridgeBfs
from Generated.nav.MyGlobalBfs import MyGlobalBfs


class Unit:
    core_pos: Position
    core_pos_list: list[tuple[int, int]]
    core_pos_set: set[tuple[int, int]]

    @staticmethod
    def init():
        MyGlobalBfs.init()

        core_id = Globals.ct.get_tile_building_id(Globals.ct.get_position())
        Unit.core_pos = Globals.ct.get_position(core_id)
        x = Unit.core_pos.x
        y = Unit.core_pos.y
        Unit.core_pos_list = [
            (x , y -1),
            (x +1, y -1),
            (x +1, y ),
            (x +1, y +1),
            (x , y +1),
            (x -1, y +1),
            (x -1, y ),
            (x -1, y -1),
            (x , y ),
        ]
        Unit.core_pos_set = set(Unit.core_pos_list)


    @classmethod
    def start_turn(cls):
        Globals.start_tick()
        MarketMaker.refresh()

        Profiler.start()
        Map.fill_tile_info()
        Profiler.end("fill_tile_info")

        MyGlobalBfs.update()


    @classmethod
    def run_turn(cls):
        pass

    @classmethod
    def end_turn(cls):
        if Globals.round == 1999:
            Profiler.report()
        print(f'scale ratio {MarketMaker.scale_ratio:.2f}')

