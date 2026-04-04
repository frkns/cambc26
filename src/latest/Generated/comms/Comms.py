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
from Generated.bbot.Attacker import Attacker
from Generated.bbot.Builder import Builder
from Generated.bbot.HarvesterAdjacent import AdjacentInfo, HarvesterAdjacent
from Generated.bbot.HealExecutor import HealExecutor
from Generated.bbot.HealTargeter import HealTargetInfo, HealTargeter
from Generated.bbot.PatrolTargeter import PatrolTargeter
from Generated.bbot.RushTargeter import RushTargeter
from Generated.bbot.ShieldTargeter import ShieldTargetInfo, ShieldTargeter
from Generated.bbot.StalkTargeter import StalkTargeter
from Generated.bbot.States import StateBuildHarvester, StateBuildHarvesterAx, StateAttackTransporter, StateRoute, StateMoveTo, StateBuildTurret, StateBuildBarrier
from Generated.bbot.VisionTracker import TransporterInfo, ConnectManager, BotInfo, VisionTracker
from Generated.build.BuildManager import BuildManager
from Generated.build.OreExecutive import OreExecutive
from Generated.build.OrePositionPicker import OrePositionPicker
from Generated.build.RouteToCore import RouteToCore
from Generated.build.SuicideExecutor import SuicideExecutor
from Generated.comms.Comms import Comms
from Generated.comms.Marker import Marker
from Generated.comms.MarkerPositionPicker import MarkerPositionPicker
from Generated.Constants import Constants
from Generated.core.Core import Core
from Generated.core.CoreHistory import CoreHistory
from Generated.core.SpawnManager import SpawnManager
from Generated.debug.Debug import Color, Debug
from Generated.debug.Profiler import Profiler
from Generated.explore.Explore import Explore
from Generated.map.DarkForest import TreeNode, DarkForest
from Generated.map.Map import TileInfo, Map
from Generated.map.Symmetry import Sym, Symmetry
from Generated.MarketMaker import MarketMaker
from Generated.nav.BfsBureau import BfsBureau
from Generated.nav.Pathfinder import Pathfinder
from Generated.RobotPlayer import Entrypoint, Player
from Generated.sentinel.Sentinel import Sentinel
from Generated.sentinel.SentinelSupervisor import SentinelTargetInfo, SentinelSupervisor
from Generated.units.Unit import Unit
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
    def handle_message(val):
        t = val >> 31

        if t == 0:
            Comms.handle_simple1(((val >> 30) & 1), ((val >> 29) & 1), ((val >> 28) & 1), ((val >> 22) & 63), ((val >> 16) & 63))
            return

        assert False