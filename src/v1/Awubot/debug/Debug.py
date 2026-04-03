from cambc import Team, EntityType, Direction, Position, ResourceType, Environment, GameConstants, GameError, Controller
import random
import heapq
import array
import time
import math
import sys
from collections import deque, defaultdict
from typing import NamedTuple
from Awubot.Builder import BuilderState, Builder
from Awubot.Constants import Constants
from Awubot.Core import Core
from Awubot.Globals import Globals, Cache
from Awubot.Map import LocalMask, MapMask, TileInfo, Map
from Awubot.MoveManager import MoveManager
from Awubot.RobotPlayer import Entrypoint, Player
from Awubot.Unit import Unit
from Awubot.Util import Util
from Awubot.debug.Profiler import Profiler
from Awubot.explore.Explore import Explore
from Awubot.nav.DirectionPicker import DirectionPicker
from Awubot.nav.OmNom import OmNom


class Color:
    WHITE = (255, 255, 255)
    RED = (255, 0, 0)
    GREEN = (0, 255, 0)
    BLUE = (0, 0, 255)
    BLACK = (0, 0, 0)
    YELLOW = (255, 255, 0)
    CYAN = (0, 255, 255)
    MAGENTA = (255, 0, 255)
    ORANGE = (255, 165, 0)
    PINK = (255, 105, 180)
    PURPLE = (128, 0, 128)
    GRAY = (128, 128, 128)
    LIME = (0, 255, 128)
    TEAL = (0, 128, 128)
    BROWN = (139, 69, 19)


class Debug:
    @staticmethod
    def line(pos_a: Position, pos_b: Position | tuple | None = None, color: tuple = Color.WHITE):
        if pos_b is None:
            pos_b = pos_a
            pos_a = Globals.ct.get_position()
        elif isinstance(pos_b, tuple):  # assume it's a color
            color = pos_b
            pos_b = pos_a
            pos_a = Globals.ct.get_position()
        Globals.ct.draw_indicator_line(pos_a, pos_b, *color)

    @staticmethod
    def dot(pos: Position, color: tuple = Color.WHITE):
        Globals.ct.draw_indicator_dot(pos, *color)

    @staticmethod
    def log(*a, **kw):
        print(*a, **kw, file=sys.stderr)

    @staticmethod
    def tee(*a, **kw):
        print(*a, **kw)
        print(*a, **kw, file=sys.stderr)

    @staticmethod
    def error(thing):
        raise Exception(thing)

    @staticmethod
    def transpose[T](mat: list[list[T]]) -> str:
        if not mat or not mat[0]:
            return "[empty matrix]"

        rows = len(mat)
        cols = len(mat[0])

        return "\n".join(
            " ".join(str(mat[r][c]) for r in range(rows))
            for c in range(cols)
        )
