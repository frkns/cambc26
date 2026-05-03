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
from Awubot import *
from Generated import *

class Sentinel(Unit):
    @classmethod
    def init(cls):
        Unit.init()
        DarkForest.init()
        TurretSuicide.init()
        SentinelChain.init()

    @classmethod
    def start_turn(cls):
        Unit.start_turn()
        TurretSuicide.update_and_check()
        DarkForest.fcompute()
        # DarkForest.debug_kind()
        SentinelChain.fill()
        SentinelSupervisor.fill()

    @classmethod
    def run_turn(cls):
        # shooting mod 3 doesn't work too well
        # consider that harvester outputs every 4 rounds 
        # interval is further slowed by harvester splitting to accepting nodes
        # i think just try firing when we can
        SentinelSupervisor.try_fire()

    @classmethod
    def end_turn(cls):
        Unit.end_turn()