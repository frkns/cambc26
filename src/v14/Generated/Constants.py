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



class Constants:
    ALL_DIRECTIONS: list[Direction] = [
        Direction.NORTH,
        Direction.NORTHEAST,
        Direction.EAST,
        Direction.SOUTHEAST,
        Direction.SOUTH,
        Direction.SOUTHWEST,
        Direction.WEST,
        Direction.NORTHWEST,
        Direction.CENTRE
    ]
    DIRECTIONS: list[Direction] = [
        Direction.NORTH,
        Direction.NORTHEAST,
        Direction.EAST,
        Direction.SOUTHEAST,
        Direction.SOUTH,
        Direction.SOUTHWEST,
        Direction.WEST,
        Direction.NORTHWEST,
    ]
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