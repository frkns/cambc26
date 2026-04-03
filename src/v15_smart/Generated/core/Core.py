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
# ===--- IMPORT





class Core(Unit):

    @classmethod
    def init(cls):
        Unit.init()

    @classmethod
    def start_turn(cls):
        Unit.start_turn()
        CoreHistory.fill()
        print(f'est income: {MarketMaker.est_income}')

    @classmethod
    def run_turn(cls):
        if SpawnManager.should_spawn() or SpawnManager.should_spawn_emergency():
            SpawnManager.spawn()

    @classmethod
    def end_turn(cls):
        Unit.end_turn()

