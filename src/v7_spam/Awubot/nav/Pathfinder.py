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
from Awubot.Constants import Constants
from Awubot.Globals import Globals
from Awubot.Map import TileInfo, Map
from Awubot.MoveManager import MoveManager
from Awubot.Util import Util
from Awubot.build.Builder import BuilderState, Builder
from Awubot.debug.Profiler import Profiler
from Awubot.explore.Explore import Explore
from Generated.MarketMaker import MarketMaker
from Generated.RobotPlayer import Entrypoint, Player
from Generated.Unit import Unit
from Generated.build.BuildManager import BuildManager
from Generated.build.OreExecutive import OreExecutive
from Generated.build.OrePositionPicker import OrePositionPicker
from Generated.build.RouteToCore import RouteToCore
from Generated.build.SuicideExecutor import SuicideExecutor
from Generated.core.Core import Core
from Generated.debug.Debug import Color, Debug
from Generated.heal.HealExecutor import HealExecutor
from Generated.nav.BfsBureau import BfsBureau
from Generated.nav.DirectionPicker import DirectionPicker


class Pathfinder:
    @classmethod
    def move_to(cls, target: Position, ban_target_pos: bool = False):
        if Globals.ct.get_move_cooldown() != 0:
            return

        Profiler.start()
        dist = BfsBureau.dists_from_pos(target)
        Profiler.end("BfsBureau")

        # Profiler.start()
        cand: DirectionPicker.Candidate = \
            DirectionPicker.pick_best_candidate(dist, ban_target_pos)
        # Profiler.end("DirectionPicker")

        print()
        print('with ban_target_pos as', ban_target_pos)
        print(cand)

        if cand.moveable:
            assert MoveManager.can_move(cand.direction)
            MoveManager.move(cand.direction)
        elif cand.fill_moveable:
            assert MoveManager.can_fill_move(cand.direction)
            Globals.ct.build_road(cand.position)
            MoveManager.move(cand.direction)

