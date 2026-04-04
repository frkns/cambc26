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
from Awubot.Util import Util
from Generated.bbot.Attacker import Attacker
from Generated.bbot.Builder import Builder
from Generated.bbot.HarvesterAdjacent import AdjacentInfo, HarvesterAdjacent
from Generated.bbot.HealExecutor import HealExecutor
from Generated.bbot.HealTargeter import HealTargetInfo, HealTargeter
from Generated.bbot.RushTargeter import RushTargeter
from Generated.bbot.ShieldTargeter import ShieldTargetInfo, ShieldTargeter
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


class MoveManager:
    @staticmethod
    def can_move(direction: Direction) -> bool:
        if direction == Direction.CENTRE:
            return True
        return Globals.ct.can_move(direction)

    @staticmethod
    def can_fill_move(direction: Direction) -> bool:
        if MoveManager.can_move(direction):
            return True
        if Globals.ct.get_action_cooldown() != 0:
            return False

        pos: Position = Globals.my_pos.add(direction)
        if not Util.on_the_map(pos):
            return False

        if not Globals.ct.can_build_road(pos):
            return False

        ti: TileInfo = Map.tile_info[pos.x][pos.y]  # type: ignore
        if ti.has_building or ti.has_bot:
            return False

        return True


    @staticmethod
    def move(direction: Direction):
        if direction == Direction.CENTRE:
            return
        Globals.ct.move(direction)
        Globals.my_pos = Globals.ct.get_position()
