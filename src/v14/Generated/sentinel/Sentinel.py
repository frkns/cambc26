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
from Generated.Constants import Constants
from Generated.MarketMaker import MarketMaker
from Generated.RobotPlayer import Entrypoint, Player
# ===--- IMPORT





class Sentinel(Unit):
    @classmethod
    def init(cls):
        Unit.init()
        DarkForest.init()

    @classmethod
    def start_turn(cls):
        Unit.start_turn()
        DarkForest.fcompute()
        DarkForest.debug_kind()

        SentinelSupervisor.fill()

    @classmethod
    def run_turn(cls):
        SentinelSupervisor.try_fire()

    @classmethod
    def end_turn(cls):
        Unit.end_turn()