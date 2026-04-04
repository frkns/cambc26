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
from Generated.bbot.States import StateBuildHarvester, StateBuildHarvesterAx, StateAttackTransporter, StateRoute, StateFoundryBuild, StateRouteFoundry, StateMoveTo, StateBuildTurret
from Generated.bbot.VisionTracker import TransporterInfo, ConnectManager, BotInfo, VisionTracker
from Generated.build.BuildManager import BuildManager
from Generated.build.FoundryBuild import FoundryBuild
from Generated.build.OreExecutive import OreExecutive
from Generated.build.OrePositionPicker import OrePositionPicker
from Generated.build.RouteToCore import RouteToCore
from Generated.build.RouteToFoundry import RouteToFoundry
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



class FoundryBuild:
    @classmethod
    def build_foundry(cls, pos):
        print("Trying to build foundry at", pos)
        print("Foundry cost:", Globals.ct.get_foundry_cost()[0])

        if Globals.my_pos.distance_squared(pos) > 2:
            Pathfinder.move_to(pos, ban_target_pos=True)
        if Globals.ct.get_global_resources()[0]> Globals.ct.get_foundry_cost()[0] and Globals.ct.can_destroy(pos) and Globals.ct.get_action_cooldown()==0:
            Globals.ct.destroy(pos)
        if Globals.ct.can_build_foundry(pos):
            Globals.ct.build_foundry(pos)
            RouteToFoundry._foundry_target = None
            DarkForest.register_sink((((pos.x) + 3) * 56 + ((pos.y) + 3)), 3)
            return True
        return False
        
    
    @classmethod
    def _pick_target(cls):
        if RouteToFoundry._foundry_target is None:
            return None
        t = ((RouteToFoundry._foundry_target) // 56 - 3), ((RouteToFoundry._foundry_target) % 56 - 3)
        return Position(t[0], t[1])
        