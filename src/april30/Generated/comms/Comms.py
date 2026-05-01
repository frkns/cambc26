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

class Comms:
    @staticmethod
    def handle_simple1(symV, symH, symR, tix, tiy):
        Symmetry.and_sym(symV, symH, symR)
        if tix != 63:
            pass


    SIMPLE1 = 0

    @staticmethod
    def pack_simple1(symV, symH, symR, tix, tiy):
        return (0 << 31) | ((symV & 1) << 30) | ((symH & 1) << 29) | ((symR & 1) << 28) | ((tix & 63) << 22) | ((tiy & 63) << 16)

    @staticmethod
    def unpack_simple1(val):
        return (((val >> 30) & 1), ((val >> 29) & 1), ((val >> 28) & 1), ((val >> 22) & 63), ((val >> 16) & 63))

    @staticmethod
    def handle_message(val):
        t = val >> 31

        if t == 0:
            Comms.handle_simple1(((val >> 30) & 1), ((val >> 29) & 1), ((val >> 28) & 1), ((val >> 22) & 63), ((val >> 16) & 63))
            return

        # Unknown message type — ignore rather than crash.
        print(f"Comms: unknown message type {t}", file=sys.stderr)