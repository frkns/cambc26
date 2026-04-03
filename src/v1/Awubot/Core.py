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
from Awubot.Globals import Globals, Cache
from Awubot.Map import LocalMask, MapMask, TileInfo, Map
from Awubot.MoveManager import MoveManager
from Awubot.RobotPlayer import Entrypoint, Player
from Awubot.Unit import Unit
from Awubot.Util import Util
from Awubot.debug.Debug import Color, Debug
from Awubot.debug.Profiler import Profiler
from Awubot.explore.Explore import Explore
from Awubot.nav.DirectionPicker import DirectionPicker
from Awubot.nav.OmNom import OmNom


class Core(Unit):
    def __init__(self):
        super().__init__()
        self.num_spawned = 0

    def start_turn(self):
        super().start_turn()

    def run_turn(self):
        if self.num_spawned < 3:
            pos = Globals.ct.get_position().add(random.choice(Constants.DIRECTIONS))
            if Globals.ct.can_spawn(pos):
                Globals.ct.spawn_builder(pos)
                self.num_spawned += 1

    def end_turn(self):
        super().end_turn()


