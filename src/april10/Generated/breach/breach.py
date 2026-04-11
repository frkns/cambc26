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

class Breach(Unit):
    @classmethod
    def init(cls):
        Unit.init()
        DarkForest.init()

    @classmethod
    def start_turn(cls):
        Unit.start_turn()
        DarkForest.fcompute()
        DarkForest.debug_kind()

    @classmethod
    def run_turn(cls):
        myDir = Globals.ct.get_direction()
        myPos = Globals.my_pos
        newPos =myPos.add(myDir).add(myDir).add(myDir)
        if Globals.ct.can_fire(newPos):
            Globals.ct.fire(newPos)
        newPos = myPos.add(myDir).add(myDir)
        if Globals.ct.can_fire(newPos):
            Globals.ct.fire(newPos)
            print("Yo we fire!", file=sys.stderr)

    @classmethod
    def end_turn(cls):
        Unit.end_turn()