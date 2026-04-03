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


class Globals:
    ct: Controller
    my_team: Team

    @classmethod
    def init(cls, ct: Controller):
        cls.ct = ct
        cls.my_team = ct.get_team()


class Cache:
    ti: int = 0
    ax: int = 0
    scale_ratio: float = 0

    @staticmethod
    def refresh():
        Cache.ti, Cache.ax = Globals.ct.get_global_resources()
        Cache.scale_ratio = Globals.ct.get_scale_percent() / 100.0
