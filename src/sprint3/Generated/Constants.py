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


class Constants:
    ALL_DIRECTIONS: list[Direction] = (
        Direction.NORTH,
        Direction.NORTHEAST,
        Direction.EAST,
        Direction.SOUTHEAST,
        Direction.SOUTH,
        Direction.SOUTHWEST,
        Direction.WEST,
        Direction.NORTHWEST,
        Direction.CENTRE
    )
    DIRECTIONS: list[Direction] = (
        Direction.NORTH,
        Direction.NORTHEAST,
        Direction.EAST,
        Direction.SOUTHEAST,
        Direction.SOUTH,
        Direction.SOUTHWEST,
        Direction.WEST,
        Direction.NORTHWEST,
    )
    TRANSPORTERS_SET: set[EntityType] = {
        EntityType.CONVEYOR,
        EntityType.ARMOURED_CONVEYOR,
        EntityType.BRIDGE,
        EntityType.SPLITTER,
    }
    PASSABLE_SET: set[EntityType] = {
        EntityType.ROAD,
        EntityType.CONVEYOR,
        EntityType.ARMOURED_CONVEYOR,
        EntityType.BRIDGE,
        EntityType.SPLITTER,
    }

    MAX_HP_MAP: dict[EntityType, int] = {
        EntityType.BUILDER_BOT: 30,
        EntityType.CORE: 500,
        EntityType.GUNNER: 40,
        EntityType.SENTINEL: 30,
        EntityType.BREACH: 60,
        EntityType.LAUNCHER: 30,
        EntityType.CONVEYOR: 20,
        EntityType.SPLITTER: 20,
        EntityType.ARMOURED_CONVEYOR: 50,
        EntityType.BRIDGE: 20,
        EntityType.HARVESTER: 30,
        EntityType.FOUNDRY: 50,
        EntityType.ROAD: 5,
        EntityType.BARRIER: 30,
        EntityType.MARKER: 1,
    }

    SENTINEL_PATTERN: list[list[tuple[int, int]]] = (
        ((-1, -5), (-1, -4), (-1, -3), (-1, -2), (-1, -1), (-1, 0), (0, -5), (0, -4), (0, -3), (0, -2), (0, -1), (1, -5), (1, -4), (1, -3), (1, -2), (1, -1), (1, 0)),
        ((0, -2), (0, -1), (1, -3), (1, -2), (1, -1), (1, 0), (2, -4), (2, -3), (2, -2), (2, -1), (2, 0), (3, -4), (3, -3), (3, -2), (3, -1), (4, -4), (4, -3), (4, -2)),
        ((0, -1), (0, 1), (1, -1), (1, 0), (1, 1), (2, -1), (2, 0), (2, 1), (3, -1), (3, 0), (3, 1), (4, -1), (4, 0), (4, 1), (5, -1), (5, 0), (5, 1)),
        ((0, 1), (0, 2), (1, 0), (1, 1), (1, 2), (1, 3), (2, 0), (2, 1), (2, 2), (2, 3), (2, 4), (3, 1), (3, 2), (3, 3), (3, 4), (4, 2), (4, 3), (4, 4)),
        ((-1, 0), (-1, 1), (-1, 2), (-1, 3), (-1, 4), (-1, 5), (0, 1), (0, 2), (0, 3), (0, 4), (0, 5), (1, 0), (1, 1), (1, 2), (1, 3), (1, 4), (1, 5)),
        ((-4, 2), (-4, 3), (-4, 4), (-3, 1), (-3, 2), (-3, 3), (-3, 4), (-2, 0), (-2, 1), (-2, 2), (-2, 3), (-2, 4), (-1, 0), (-1, 1), (-1, 2), (-1, 3), (0, 1), (0, 2)),
        ((-5, -1), (-5, 0), (-5, 1), (-4, -1), (-4, 0), (-4, 1), (-3, -1), (-3, 0), (-3, 1), (-2, -1), (-2, 0), (-2, 1), (-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1)),
        ((-4, -4), (-4, -3), (-4, -2), (-3, -4), (-3, -3), (-3, -2), (-3, -1), (-2, -4), (-2, -3), (-2, -2), (-2, -1), (-2, 0), (-1, -3), (-1, -2), (-1, -1), (-1, 0), (0, -2), (0, -1)),
    )

    SENTINEL_REVERSE: dict[tuple, tuple[int, ...]] = {
        (-1, -5): (0,),
        (-1, -4): (0,),
        (-1, -3): (0, 7),
        (-1, -2): (0, 7),
        (-1, -1): (0, 6, 7),
        (-1, 0): (0, 4, 5, 6, 7),
        (0, -5): (0,),
        (0, -4): (0,),
        (0, -3): (0,),
        (0, -2): (0, 1, 7),
        (0, -1): (0, 1, 2, 6, 7),
        (1, -5): (0,),
        (1, -4): (0,),
        (1, -3): (0, 1),
        (1, -2): (0, 1),
        (1, -1): (0, 1, 2),
        (1, 0): (0, 1, 2, 3, 4),
        (2, -4): (1,),
        (2, -3): (1,),
        (2, -2): (1,),
        (2, -1): (1, 2),
        (2, 0): (1, 2, 3),
        (3, -4): (1,),
        (3, -3): (1,),
        (3, -2): (1,),
        (3, -1): (1, 2),
        (4, -4): (1,),
        (4, -3): (1,),
        (4, -2): (1,),
        (0, 1): (2, 3, 4, 5, 6),
        (1, 1): (2, 3, 4),
        (2, 1): (2, 3),
        (3, 0): (2,),
        (3, 1): (2, 3),
        (4, -1): (2,),
        (4, 0): (2,),
        (4, 1): (2,),
        (5, -1): (2,),
        (5, 0): (2,),
        (5, 1): (2,),
        (0, 2): (3, 4, 5),
        (1, 2): (3, 4),
        (1, 3): (3, 4),
        (2, 2): (3,),
        (2, 3): (3,),
        (2, 4): (3,),
        (3, 2): (3,),
        (3, 3): (3,),
        (3, 4): (3,),
        (4, 2): (3,),
        (4, 3): (3,),
        (4, 4): (3,),
        (-1, 1): (4, 5, 6),
        (-1, 2): (4, 5),
        (-1, 3): (4, 5),
        (-1, 4): (4,),
        (-1, 5): (4,),
        (0, 3): (4,),
        (0, 4): (4,),
        (0, 5): (4,),
        (1, 4): (4,),
        (1, 5): (4,),
        (-4, 2): (5,),
        (-4, 3): (5,),
        (-4, 4): (5,),
        (-3, 1): (5, 6),
        (-3, 2): (5,),
        (-3, 3): (5,),
        (-3, 4): (5,),
        (-2, 0): (5, 6, 7),
        (-2, 1): (5, 6),
        (-2, 2): (5,),
        (-2, 3): (5,),
        (-2, 4): (5,),
        (-5, -1): (6,),
        (-5, 0): (6,),
        (-5, 1): (6,),
        (-4, -1): (6,),
        (-4, 0): (6,),
        (-4, 1): (6,),
        (-3, -1): (6, 7),
        (-3, 0): (6,),
        (-2, -1): (6, 7),
        (-4, -4): (7,),
        (-4, -3): (7,),
        (-4, -2): (7,),
        (-3, -4): (7,),
        (-3, -3): (7,),
        (-3, -2): (7,),
        (-2, -4): (7,),
        (-2, -3): (7,),
        (-2, -2): (7,),
    }