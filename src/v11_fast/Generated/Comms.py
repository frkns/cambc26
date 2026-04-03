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



class Comms:
    @staticmethod
    def handle_simple1(symV, symH, symR, tix, tiy):
        Symmetry.and_sym(symV, symH, symR)
        if tix != 63:
            OreExecutive.register_ti(Position(tix, tiy))


    SIMPLE1 = 0

    @staticmethod
    def pack_simple1(symV, symH, symR, tix, tiy):
        return (0 << 31) | ((symV & 1) << 30) | ((symH & 1) << 29) | ((symR & 1) << 28) | ((tix & 63) << 22) | ((tiy & 63) << 16)

    @staticmethod
    def unpack_simple1(val):
        return (((val >> 30) & 1), ((val >> 29) & 1), ((val >> 28) & 1), ((val >> 22) & 63), ((val >> 16) & 63))

    @staticmethod
    def read_message(val):
        t = val >> 31
        if t == 0:
            Comms.handle_simple1(((val >> 30) & 1), ((val >> 29) & 1), ((val >> 28) & 1), ((val >> 22) & 63), ((val >> 16) & 63))
            return
