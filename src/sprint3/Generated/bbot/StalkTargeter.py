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


class StalkTargeter:
    @classmethod
    def get_best_target(cls) -> Position | None:
        if not Map.harvester_set:
            return None

        for pos, x, y, idx, ti in Map.proc_nearby_tiles:
            if ti.has_bot and not ti.is_bot_ally:
                return Position(x, y)