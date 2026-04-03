from cambc import Team, EntityType, Direction, Position, ResourceType, Environment, GameConstants, GameError, Controller
import random
import heapq
import array
import time
import math
import sys
from collections import deque, defaultdict
from typing import NamedTuple
from Awubot.Builder import BuilderState, Builder
from Awubot.Constants import Constants
from Awubot.Core import Core
from Awubot.Globals import Globals, Cache
from Awubot.Map import LocalMask, MapMask, TileInfo, Map
from Awubot.MoveManager import MoveManager
from Awubot.Unit import Unit
from Awubot.Util import Util
from Awubot.debug.Debug import Color, Debug
from Awubot.debug.Profiler import Profiler
from Awubot.explore.Explore import Explore
from Awubot.nav.DirectionPicker import DirectionPicker
from Awubot.nav.OmNom import OmNom


class Entrypoint:
    me: Unit
    needs_init = True

    @classmethod
    def init(cls, ct: Controller):
        Globals.init(ct)
        Map.init()

        match ct.get_entity_type():
            case EntityType.CORE:
                cls.me = Core()
            case EntityType.BUILDER_BOT:
                cls.me = Builder()

    @classmethod
    def run(cls, ct: Controller):
        Globals.ct = ct  # TODO: remove when fixed
        if cls.needs_init:
            cls.init(ct)
            cls.needs_init = False

        cls.me.start_turn()
        cls.me.run_turn()
        cls.me.end_turn()


class Player:
    def run(self, ct):
        Entrypoint.run(ct)
