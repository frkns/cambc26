# ---=== IMPORT
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
from Awubot.Globals import Globals
from Awubot.MoveManager import MoveManager
from Awubot.Util import Util
from Generated.Constants import Constants
from Generated.MarketMaker import MarketMaker
from Generated.RobotPlayer import Entrypoint, Player
from Generated.bbot.Attacker import Attacker
from Generated.bbot.Builder import Builder
from Generated.bbot.HarvesterAdjacent import AdjacentInfo, HarvesterAdjacent
from Generated.bbot.HealExecutor import HealExecutor
from Generated.bbot.HealTargeter import HealTargetInfo, HealTargeter
from Generated.bbot.States import StateBuildHarvester, StateAttackTransporter, StateRoute, StateMoveTo, StateBuildTurret
from Generated.bbot.VisionTracker import TransporterInfo, ConnectManager, BotInfo, VisionTracker
from Generated.build.BuildManager import BuildManager
from Generated.build.OreExecutive import OreExecutive
from Generated.build.OrePositionPicker import OrePositionPicker
from Generated.build.RouteToCore import RouteToCore
from Generated.build.SuicideExecutor import SuicideExecutor
from Generated.comms.Comms import Comms
from Generated.comms.Marker import Marker
from Generated.comms.MarkerPositionPicker import MarkerPositionPicker
from Generated.core.Core import Core
from Generated.core.CoreHistory import CoreHistory
from Generated.core.SpawnManager import SpawnManager
from Generated.debug.Debug import Color, Debug
from Generated.debug.Profiler import Profiler
from Generated.explore.Explore import Explore
from Generated.map.DarkForest import TreeNode, DarkForest
from Generated.map.Map import TileInfo, Map
from Generated.map.Symmetry import Sym, Symmetry
from Generated.nav.BfsBureau import BfsBureau
from Generated.nav.Pathfinder import Pathfinder
from Generated.sentinel.Sentinel import Sentinel
from Generated.sentinel.SentinelSupervisor import SentinelTargetInfo, SentinelSupervisor
from Generated.units.Unit import Unit
# ===--- IMPORT



class Unit:
    core_pos: Position
    core_pos_list: list[tuple[int, int]]
    core_pos_set: set[int]

    @staticmethod
    def core_pos_init():
        core_id = Globals.ct.get_tile_building_id(Globals.my_pos)
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
        idx = (((x) + 3) * 56 + ((y) + 3))
        Unit.core_pos_set = {
            idx -1,
            idx +55,
            idx +56,
            idx +57,
            idx +1,
            idx -55,
            idx -56,
            idx -57,
            idx ,
        }


    @classmethod
    def init(cls):
        random.seed(Globals.my_id)
        if Globals.my_type == EntityType.BUILDER_BOT:
            Unit.core_pos_init()
            BfsBureau.init()
            Symmetry.predict_enemy_core()
        else:
            cls.core_pos_set = set()


    @classmethod
    def start_turn(cls):
        Globals.start_tick()
        MarketMaker.refresh()

        Profiler.start()
        Map.fill_tile_info()
        Profiler.end("""Map.fill_tile_info""")

    @classmethod
    def run_turn(cls):
        pass

    @classmethod
    def end_turn(cls):

        if Globals.round == 667:
            Profiler.report()
        print(f'scale ratio {MarketMaker.scale_ratio:.2f}')

