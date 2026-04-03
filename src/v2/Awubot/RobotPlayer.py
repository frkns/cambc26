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
from Awubot.MoveManager import MoveManager
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


class Entrypoint:
    me: type[Core | Builder]
    needs_init = True

    @classmethod
    def init(cls, ct: Controller):
        Globals.init(ct)
        Map.init()

        match ct.get_entity_type():
            case EntityType.CORE:
                Core.init()
                cls.me = Core
            case EntityType.BUILDER_BOT:
                Builder.init()
                cls.me = Builder

    @classmethod
    def run(cls, ct: Controller):
        Globals.ct = ct  # in case not fixed...
        if cls.needs_init:
            cls.init(ct)
            cls.needs_init = False

        cls.me.start_turn()
        cls.me.run_turn()
        cls.me.end_turn()


class Player:
    def run(self, ct):
        try:
            Entrypoint.run(ct)
        except Exception as e:
            Debug.line(Position(0, 0), Color.RED)
            Debug.tee(e)
            raise e
