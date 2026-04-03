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
from Awubot.explore.Explore import Explore
from Generated.MarketMaker import MarketMaker
from Generated.RobotPlayer import Entrypoint, Player
from Generated.Unit import Unit
from Generated.build.BuildManager import BuildManager
from Generated.build.Builder import BuilderState, Builder
from Generated.build.OreExecutive import OreExecutive
from Generated.build.OrePositionPicker import OrePositionPicker
from Generated.build.RouteToCore import RouteToCore
from Generated.build.SuicideExecutor import SuicideExecutor
from Generated.core.Core import Core
from Generated.debug.Debug import Color, Debug
from Generated.heal.HealExecutor import HealExecutor
from Generated.map.DarkForest import TreeNode, DarkForest
from Generated.map.Map import TileInfo, Map
from Generated.map.Symmetry import Sym, Symmetry
from Generated.nav.BfsBureau import BfsBureau
from Generated.nav.DirectionPicker import DirectionPicker
from Generated.nav.Pathfinder import Pathfinder



class SuicideExecutor:
    @staticmethod
    def execute_suicide_attempt():
        cond = MarketMaker.scale_ratio > 3
        strong_cond = MarketMaker.ti > 800 and MarketMaker.scale_ratio > 3 and Map.nearby_ally_bots > 5

        my_pos = Globals.ct.get_position()
        ti = Map.tile_info[my_pos.x][my_pos.y]

        if not (ti.has_building and not ti.is_building_ally):
            return

        if ti.entity_type in Constants.TRANSPORTERS_SET and cond:
            Globals.ct.self_destruct()

        if ti.entity_type == EntityType.ROAD and strong_cond:
            Globals.ct.self_destruct()
            