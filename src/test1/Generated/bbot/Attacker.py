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



class Attacker:
    @classmethod
    def get_trans_target(cls) -> Position | None:
        trans: TransporterInfo = VisionTracker.get_best_trans_atk_target()
        if trans is None:
            return None
        if not trans.reachable: 
            return None
        if trans.flowing_into_ally:
            return None
        if trans.flow == 0:
            return None
        if not VisionTracker.me_is_canonical_ally(trans.position):
            return None
        return trans.position