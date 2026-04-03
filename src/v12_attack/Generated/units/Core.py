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
from Awubot.Constants import Constants
from Awubot.Globals import Globals
from Awubot.MoveManager import MoveManager
from Awubot.Util import Util
from Awubot.debug.Profiler import Profiler
from Generated.MarketMaker import MarketMaker
from Generated.RobotPlayer import Entrypoint, Player
from Generated.bbot.Attacker import Attacker
from Generated.bbot.Builder import Builder
from Generated.bbot.States import StateBuildHarvester, StateAttackTransporter, StateRoute, StateExplore
from Generated.bbot.VisionTracker import TransporterInfo, VisionTracker
from Generated.build.BuildManager import BuildManager
from Generated.build.OreExecutive import OreExecutive
from Generated.build.OrePositionPicker import OrePositionPicker
from Generated.build.RouteToCore import RouteToCore
from Generated.build.SuicideExecutor import SuicideExecutor
from Generated.comms.Comms import Comms
from Generated.comms.Marker import Marker
from Generated.comms.MarkerPositionPicker import MarkerPositionPicker
from Generated.debug.Debug import Color, Debug
from Generated.explore.Explore import Explore
from Generated.heal.HealExecutor import HealExecutor
from Generated.map.DarkForest import TreeNode, DarkForest
from Generated.map.Map import TileInfo, Map
from Generated.map.Symmetry import Sym, Symmetry
from Generated.nav.BfsBureau import BfsBureau
from Generated.nav.Pathfinder import Pathfinder
from Generated.units.Core import Core
from Generated.units.Unit import Unit
# ===--- IMPORT





class Core(Unit):
    num_spawned: int = 0

    @classmethod
    def init(cls):
        Unit.init()

    @classmethod
    def start_turn(cls):
        Unit.start_turn()
        print(f'est income: {MarketMaker.est_income}')


    @classmethod
    def spawn(cls):
        # rework this
        pos = Globals.my_pos.add(random.choice(Constants.DIRECTIONS))
        if Globals.ct.can_spawn(pos):
            Globals.ct.spawn_builder(pos)
            cls.num_spawned += 1

    @classmethod
    def run_turn(cls):
        if cls.num_spawned < 3 or MarketMaker.ti > 1000:
            if cls.num_spawned < 6:
                cls.spawn()

    @classmethod
    def end_turn(cls):
        Unit.end_turn()

        if Globals.round > 666:
            Globals.ct.resign()

