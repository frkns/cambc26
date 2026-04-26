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

class CoreHistory:

    wround: int
    hp_hist = [500] * 100

    @classmethod
    def fill(cls):
        cls.wround = Globals.round % 100
        cls.hp_hist[cls.wround] = Globals.ct.get_hp()

    @classmethod
    def hp_delta(cls, rounds: int):  
        # negative when HP lost
        assert rounds < 100
        return cls.hp_hist[cls.wround] - cls.hp_hist[(cls.wround - rounds) % 100]