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



class Explore:
    target: Position
    target = None

    @classmethod
    def init(cls) -> None:
        cls.target = cls.new_target()

    @classmethod
    def new_target(cls) -> Position:
        # return random.choice((Position(0, 0), Position(Map.W - 1, Map.H - 1)))
        # return random.choice((
        #     Position(0, 0),
        #     Position(0, Map.maxY),
        #     Position(Map.maxX, 0),
        #     Position(Map.maxX, Map.maxY),
        # ))
        return Util.rand_pos()

        # bestDx: int = None
        # bestDy: int = None
        # best_score: int = -1000000

        #         # 
        # score = Util.distance_to_edge(Globals.my_pos.x, Globals.my_pos.y, 0, -1)
        
        #         
        # if score > best_score:
        #     best_score = score
        #     bestDx = 0
        #     bestDy = -1
            
        #         # 
        # score = Util.distance_to_edge(Globals.my_pos.x, Globals.my_pos.y, 1, -1)
        
        #         # score += 1 # slightly prefer diagonals
        #         
        # if score > best_score:
        #     best_score = score
        #     bestDx = 1
        #     bestDy = -1
            
        #         # 
        # score = Util.distance_to_edge(Globals.my_pos.x, Globals.my_pos.y, 1, 0)
        
        #         
        # if score > best_score:
        #     best_score = score
        #     bestDx = 1
        #     bestDy = 0
            
        #         # 
        # score = Util.distance_to_edge(Globals.my_pos.x, Globals.my_pos.y, 1, 1)
        
        #         # score += 1 # slightly prefer diagonals
        #         
        # if score > best_score:
        #     best_score = score
        #     bestDx = 1
        #     bestDy = 1
            
        #         # 
        # score = Util.distance_to_edge(Globals.my_pos.x, Globals.my_pos.y, 0, 1)
        
        #         
        # if score > best_score:
        #     best_score = score
        #     bestDx = 0
        #     bestDy = 1
            
        #         # 
        # score = Util.distance_to_edge(Globals.my_pos.x, Globals.my_pos.y, -1, 1)
        
        #         # score += 1 # slightly prefer diagonals
        #         
        # if score > best_score:
        #     best_score = score
        #     bestDx = -1
        #     bestDy = 1
            
        #         # 
        # score = Util.distance_to_edge(Globals.my_pos.x, Globals.my_pos.y, -1, 0)
        
        #         
        # if score > best_score:
        #     best_score = score
        #     bestDx = -1
        #     bestDy = 0
            
        #         # 
        # score = Util.distance_to_edge(Globals.my_pos.x, Globals.my_pos.y, -1, -1)
        
        #         # score += 1 # slightly prefer diagonals
        #         
        # if score > best_score:
        #     best_score = score
        #     bestDx = -1
        #     bestDy = -1
            
        # 
        # if bestDx is None:
        #     return Util.rand_pos()
            
        # return Util.follow_to_edge(Globals.my_pos.x, Globals.my_pos.y, bestDx, bestDy)


    @classmethod
    def get_target(cls) -> Position:

        if (Globals.my_pos.distance_squared(cls.target) <= 2) or (Pathfinder.cur_target == cls.target and Pathfinder.given_up):
            cls.target = cls.new_target()

        return cls.target