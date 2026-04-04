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





class Builder(Unit):
    state: str

    @classmethod
    def init(cls):
        Unit.init()
        Explore.init()
        DarkForest.init()
        cls.state = 'Explore'


    @classmethod
    def start_turn(cls):
        Unit.start_turn()

        
        BfsBureau.update()
        

        Symmetry.run_sym_check()

        
        DarkForest.fcompute()
        


        
        BfsBureau.bfs20()
        

        
        OreExecutive.fill()
        

        
        VisionTracker.fill()
        

        
        HarvesterAdjacent.fill()
        

        
        HealTargeter.fill()
        

        
        ShieldTargeter.fill()
        

                


    @classmethod
    def run_turn(cls):
        cls.state, *args = cls.determine_state()


        globals()[f'State{cls.state}'].run(*args)


    @classmethod
    def end_turn(cls):
        Unit.end_turn()

        
        HealExecutor.execute_heal_attempt()
        

        
        Marker.attempt_mark()
        


    @classmethod
    def determine_state(cls):
        if RouteToCore.is_active:
            return ('Route',)

        hpos = HarvesterAdjacent.get_best_hijack_position()
        if hpos is not None:
            Debug.dot(hpos, Color.PURPLE)
            return 'BuildTurret', hpos, None

        healpos = HealTargeter.get_best_target()
        if healpos is not None:
            return 'MoveTo', healpos, 'Heal'

        # shieldpos = ShieldTargeter.get_best_target()
        # if shieldpos is not None:
        #     return 'BuildBarrier', shieldpos, None

        trans: TransporterInfo = ConnectManager.get_connect_target_info()
        if trans is not None:
            tpos = trans.target

            if Util.dist_sq(tpos, Symmetry.enemy_core_pos) \
                    < Util.dist_sq(tpos, Unit.core_pos):
                return 'BuildTurret', tpos, None if trans.is_bridge else trans.target.direction_to(tpos)

            if tpos not in RouteToCore.killed:
                RouteToCore.set_pos(tpos)
                return 'MoveTo', tpos, 'InitRoute'

        apos = Attacker.get_trans_target()
        if apos is not None:
            return 'AttackTransporter', apos

        """
        axTarg = OreExecutive.get_axionite_target()
        if axTarg is not None:
            return 'BuildHarvesterAx', axTarg
        """
        bhpos = OreExecutive.get_titanium_target()
        if bhpos is not None:
            return 'BuildHarvester', bhpos

        rushTarget = RushTargeter.get_best_target()
        if rushTarget is not None:
            return 'MoveTo', rushTarget, 'Rush'

        return 'MoveTo', Explore.get_target(), 'Explore'
