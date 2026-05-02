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

class Globals:
    # const
    ct: Controller
    my_id: int
    my_team: Team
    my_type: EntityType
    spawn_round: int

    # updating
    round: int
    my_pos: Position
    my_idx: int

    @classmethod
    def init(cls, ct: Controller):
        cls.ct = ct
        cls.my_id = ct.get_id()
        cls.my_team = ct.get_team()
        cls.round = cls.ct.get_current_round()
        cls.spawn_round = cls.round
        cls.my_pos = ct.get_position()
        cls.my_idx = (((cls.my_pos.x) + 3) * 56 + ((cls.my_pos.y) + 3))
        cls.my_type = ct.get_entity_type()

    @classmethod
    def start_tick(cls):
        cls.round = cls.ct.get_current_round()
        cls.my_pos = cls.ct.get_position()
        cls.my_idx = (((cls.my_pos.x) + 3) * 56 + ((cls.my_pos.y) + 3))
