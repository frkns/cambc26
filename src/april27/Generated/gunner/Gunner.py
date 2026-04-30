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

class Gunner(Unit):
    @classmethod
    def init(cls):
        Unit.init()
        DarkForest.init()
        TurretSuicide.init()

    @classmethod
    def start_turn(cls):
        Unit.start_turn()
        TurretSuicide.update_and_check()

        DarkForest.fcompute()

        GunnerSupervisor.fill()

    @classmethod
    def run_turn(cls):
        GunnerSupervisor.try_fire()

    @classmethod
    def end_turn(cls):
        Unit.end_turn()