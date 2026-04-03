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
from Awubot.MoveManager import MoveManager
from Awubot.Util import Util
from Awubot.debug.Profiler import Profiler
from Generated.Comms import Comms
from Generated.MarketMaker import MarketMaker
from Generated.RobotPlayer import Entrypoint, Player
from Generated.Unit import Unit
from Generated.builder.BuildManager import BuildManager
from Generated.builder.Builder import BuilderState, Builder
from Generated.builder.OreExecutive import OreExecutive
from Generated.builder.OrePositionPicker import OrePositionPicker
from Generated.builder.RouteToCore import RouteToCore
from Generated.builder.SuicideExecutor import SuicideExecutor
from Generated.core.Core import Core
from Generated.debug.Debug import Color, Debug
from Generated.explore.Explore import Explore
from Generated.heal.HealExecutor import HealExecutor
from Generated.map.DarkForest import TreeNode, DarkForest
from Generated.map.Map import TileInfo, Map
from Generated.map.Symmetry import Sym, Symmetry
from Generated.nav.BfsBureau import BfsBureau
from Generated.nav.DirectionPicker import DirectionPicker
from Generated.nav.Pathfinder import Pathfinder
# ===--- IMPORT


class Globals:
    # const
    ct: Controller
    my_id: int
    my_team: Team
    
    # updating
    round: int

    @classmethod
    def init(cls, ct: Controller):
        cls.ct = ct
        cls.my_id = ct.get_id()
        cls.my_team = ct.get_team()

    @classmethod
    def start_tick(cls):
        cls.round = Globals.ct.get_current_round()



