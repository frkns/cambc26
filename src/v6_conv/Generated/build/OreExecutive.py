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
from Awubot.core.Core import Core
from Awubot.debug.Profiler import Profiler
from Awubot.explore.Explore import Explore
from Awubot.nav.Pathfinder import Pathfinder
from Generated.MarketMaker import MarketMaker
from Generated.RobotPlayer import Entrypoint, Player
from Generated.Unit import Unit
from Generated.build.BuildManager import BuildManager
from Generated.build.OreExecutive import OreExecutive
from Generated.build.OrePositionPicker import OrePositionPicker
from Generated.build.RouteToCore import RouteToCore
from Generated.build.SuicideExecutor import SuicideExecutor
from Generated.debug.Debug import Color, Debug
from Generated.heal.HealExecutor import HealExecutor
from Generated.nav.BfsBureau import BfsBureau
from Generated.nav.ClaudeGlobalBfs import ClaudeGlobalBfs
from Generated.nav.DirectionPicker import DirectionPicker
from Generated.nav.EgoBridgeBfs import EgoBridgeBfs
from Generated.nav.MyGlobalBfs import MyGlobalBfs
from Generated.nav.MyGlobalBfs2 import MyGlobalBfs2


class OreExecutive:
    banned: set[tuple[int, int]] = set()

    @classmethod
    def find_ore_to_mine(cls) -> Position | None:
        # TODO: passable check
        ct = Globals.ct
        tile_info = Map.tile_info

        for pos in Map.nearby_tiles:
            ti = tile_info[pos.x][pos.y]
            env = ti.env
            if env != Environment.ORE_TITANIUM and env != Environment.ORE_AXIONITE:
                continue
            if ti.entity_type == EntityType.HARVESTER:
                continue

            return pos

        return None

    @classmethod
    def go_build_harvester(cls, pos):
        Pathfinder.move_to(pos, ban_target_pos=True)
        if BuildManager.can_dbuild_harvester(pos):
            Debug.line(pos, Color.YELLOW)
            BuildManager.dbuild_harvester(pos)

            cand: OrePositionPicker.Candidate = OrePositionPicker.pick_best_candidate(pos)
            RouteToCore.set_pos(cand.position)