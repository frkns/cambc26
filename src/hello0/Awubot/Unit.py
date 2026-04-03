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
from Awubot.RobotPlayer import Entrypoint, Player
from Awubot.Util import Util
from Awubot.debug.Debug import Color, Debug
from Awubot.debug.Profiler import Profiler
from Awubot.explore.Explore import Explore
from Awubot.nav.DirectionPicker import DirectionPicker
from Awubot.nav.OmNom import OmNom


class Unit:
    def __init__(self):
        pass

    def start_turn(self):
        Profiler.start()
        Map.fill()
        Profiler.end("fill")

        Profiler.start()
        Map.fill_tile_info()
        Profiler.end("fill_tile_info")

        Cache.refresh()

    def run_turn(self):
        raise Exception("did you forgot to override? (yes)")

    def end_turn(self):
        if Globals.ct.get_current_round() == 1999:
            Profiler.report()
