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
from Awubot.MoveManager import MoveManager
from Awubot.Util import Util
from Generated.Constants import Constants
from Generated.MarketMaker import MarketMaker
from Generated.RobotPlayer import Entrypoint, Player
# ===--- IMPORT


class Globals:
    # const
    ct: Controller
    my_id: int
    my_team: Team
    my_type: EntityType
    
    # updating
    round: int
    my_pos: Position

    @classmethod
    def init(cls, ct: Controller):
        cls.ct = ct
        cls.my_id = ct.get_id()
        cls.my_team = ct.get_team()
        cls.my_pos = ct.get_position()
        cls.my_type = ct.get_entity_type()

    @classmethod
    def start_tick(cls):
        cls.round = cls.ct.get_current_round()
        cls.my_pos = cls.ct.get_position()

