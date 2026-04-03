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
from Awubot.Constants import Constants
from Awubot.Core import Core
from Awubot.Globals import Globals, Cache
from Awubot.Map import LocalMask, MapMask, TileInfo, Map
from Awubot.RobotPlayer import Entrypoint, Player
from Awubot.Util import Util
from Awubot.build.Builder import BuilderState, Builder
from Awubot.debug.Profiler import Profiler
from Awubot.explore.Explore import Explore
from Awubot.nav.Pathfinder import Pathfinder
from Generated.Unit import Unit
from Generated.build.BuildManager import BuildManager
from Generated.build.OreExecutive import OreExecutive
from Generated.build.OrePositionPicker import OrePositionPicker
from Generated.build.RouteToCore import RouteToCore
from Generated.debug.Debug import Color, Debug
from Generated.nav.ClaudeGlobalBfs import ClaudeGlobalBfs
from Generated.nav.DirectionPicker import DirectionPicker
from Generated.nav.EgoBridgeBfs import EgoBridgeBfs


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

        pos: Position = Globals.ct.get_position().add(direction)
        if not Util.on_the_map(pos):
            return False

        if not Globals.ct.can_build_road(pos):
            return False

        ti: TileInfo = Map.tile_info[pos.x][pos.y]  # type: ignore
        if ti.has_building or ti.has_builder_bot:
            return False

        return True


    @staticmethod
    def move(direction: Direction):
        if direction == Direction.CENTRE:
            return
        Globals.ct.move(direction)
