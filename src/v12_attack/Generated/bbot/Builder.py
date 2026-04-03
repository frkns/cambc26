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

        Symmetry.run_sym_check()
        DarkForest.fcompute()

        Profiler.start()
        BfsBureau.bfs20()
        Profiler.end("""bfs20""")

        OreExecutive.fill()

        Profiler.start()
        VisionTracker.fill()
        Profiler.end("""VisionTracker.fill""")

        Symmetry.debug()
                


    @classmethod
    def run_turn(cls):
        cls.state, pos = cls.determine_state()

        if pos is None:
            print(f'running: {cls.state}')
        else:
            print(f'running: {cls.state}  @ ({pos.x}, {pos.y})')

        globals()[f'State{cls.state}'].run(pos)


    @classmethod
    def end_turn(cls):
        Unit.end_turn()

        Profiler.start()
        HealExecutor.execute_heal_attempt()
        Profiler.end("""HealExecutor.execute_heal_attempt""")

        Profiler.start()
        Marker.attempt_mark()
        Profiler.end("""Marker.attempt_mark""")


    @classmethod
    def determine_state(cls):
        if RouteToCore.is_active:
            return 'Route', None

        apos = Attacker.get_trans_target()
        if apos is not None:
            return 'AttackTransporter', apos

        hpos = OreExecutive.get_target()
        if hpos is not None:
            return 'BuildHarvester', hpos

        return 'Explore', Explore.get_target()
