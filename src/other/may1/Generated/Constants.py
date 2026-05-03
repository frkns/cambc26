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
    CARDINAL_DIRECTIONS: list[Direction] = (
        Direction.NORTH,
        Direction.EAST,
        Direction.SOUTH,
        Direction.WEST,
    )
    TRANSPORTERS_SET: set[EntityType] = {
        EntityType.CONVEYOR,
        EntityType.ARMOURED_CONVEYOR,
        EntityType.BRIDGE,
        EntityType.SPLITTER,
    }
    ATTACKABLE_TRANSPORTERS_SET: set[EntityType] = {
        EntityType.CONVEYOR,  # sans the ARMOURED_CONVEYOR
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

    PASSABLE_ATTACKABLE_SET: set[EntityType] = {
        EntityType.ROAD,
        EntityType.CONVEYOR,
        EntityType.BRIDGE,
        EntityType.SPLITTER,
    }

    TURRET_SET: set[EntityType] = {
        EntityType.SENTINEL,
        EntityType.GUNNER,
        EntityType.LAUNCHER,
        EntityType.BREACH,
    }

    AXIONITE_START: int = 100 # Start producing axionite at this round

    HEAL_OVER: int = 9999 # stop heal attempt now, never

    MAX_HP_MAP: dict[EntityType, int] = {
        EntityType.BUILDER_BOT: 40,
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
        EntityType.ROAD: 4,
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

    GUNNER_HITS_CORE_OFFSETS: list[int] = [-225, -224, -223, -171, -170, -169, -168, -167, -166, -165, -115, -114, -113, -112, -111, -110, -109, -60, -59, -58, -54, -53, -52, -4, -3, -2, 2, 3, 4, 52, 53, 54, 58, 59, 60, 109, 110, 111, 112, 113, 114, 115, 165, 166, 167, 168, 169, 170, 171, 223, 224, 225]
    SENTINEL_HITS_CORE_OFFSETS: list[int] = [-285, -284, -283, -282, -281, -280, -279, -278, -277, -276, -275, -229, -228, -227, -226, -225, -224, -223, -222, -221, -220, -219, -173, -172, -171, -170, -169, -168, -167, -166, -165, -164, -163, -117, -116, -115, -114, -113, -112, -111, -110, -109, -108, -107, -61, -60, -59, -58, -54, -53, -52, -51, -5, -4, -3, -2, 2, 3, 4, 5, 51, 52, 53, 54, 58, 59, 60, 61, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 163, 164, 165, 166, 167, 168, 169, 170, 171, 172, 173, 219, 220, 221, 222, 223, 224, 225, 226, 227, 228, 229, 275, 276, 277, 278, 279, 280, 281, 282, 283, 284, 285]
