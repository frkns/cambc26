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



class Marker:
    @classmethod
    def attempt_mark(cls):
        pos = MarkerPositionPicker.get_marker_pos()
        if pos is None:
            return
        
        val = Comms.pack_simple1(Symmetry.V, Symmetry.H, Symmetry.R, 63, 63)
        Globals.ct.place_marker(pos, val)