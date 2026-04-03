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
from Awubot.Constants import Constants
from Awubot.Globals import Globals
from Awubot.MoveManager import MoveManager
from Awubot.Util import Util
from Awubot.debug.Profiler import Profiler
from Awubot.explore.Explore import Explore
from Generated.MarketMaker import MarketMaker
from Generated.RobotPlayer import Entrypoint, Player
from Generated.Unit import Unit
from Generated.build.BuildManager import BuildManager
from Generated.build.Builder import BuilderState, Builder
from Generated.build.OreExecutive import OreExecutive
from Generated.build.OrePositionPicker import OrePositionPicker
from Generated.build.RouteToCore import RouteToCore
from Generated.build.SuicideExecutor import SuicideExecutor
from Generated.core.Core import Core
from Generated.debug.Debug import Color, Debug
from Generated.heal.HealExecutor import HealExecutor
from Generated.map.DarkForest import TreeNode, DarkForest
from Generated.map.Map import TileInfo, Map
from Generated.map.Symmetry import Sym, Symmetry
from Generated.nav.BfsBureau import BfsBureau
from Generated.nav.DirectionPicker import DirectionPicker
from Generated.nav.Pathfinder import Pathfinder



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
        elif isinstance(pos_b, tuple) and not isinstance(pos_b, Position):  # color tuple, not Position
            color = pos_b
            pos_b = pos_a
            pos_a = Globals.ct.get_position()
        Globals.ct.draw_indicator_line(pos_a, pos_b, *color)

    @staticmethod
    def diline(a: Position, b: Position, color: tuple = Color.WHITE):
        Globals.ct.draw_indicator_line(a, b, *color)
        Globals.ct.draw_indicator_dot(b, *color)

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

    @staticmethod
    def debug_dist(dist: list[list[int]]):
        my_pos = Globals.ct.get_position()
        print("N:", 
              dist[my_pos.x +0][my_pos.y -1], end=', ')
        print("NE:", 
              dist[my_pos.x +1][my_pos.y -1], end=', ')
        print("E:", 
              dist[my_pos.x +1][my_pos.y +0], end=', ')
        print("SE:", 
              dist[my_pos.x +1][my_pos.y +1], end=', ')
        print("S:", 
              dist[my_pos.x +0][my_pos.y +1], end=', ')
        print("SW:", 
              dist[my_pos.x -1][my_pos.y +1], end=', ')
        print("W:", 
              dist[my_pos.x -1][my_pos.y +0], end=', ')
        print("NW:", 
              dist[my_pos.x -1][my_pos.y -1], end=', ')
        print("C:", 
              dist[my_pos.x +0][my_pos.y +0], end=', ')
        print()

    @staticmethod
    def diamond(color: tuple = Color.WHITE):
        c = Globals.ct.get_position()
        x, y = c.x, c.y

        top    = Position(x, y - 1)
        right  = Position(x + 1, y)
        bottom = Position(x, y + 1)
        left   = Position(x - 1, y)

        Globals.ct.draw_indicator_line(top, right, *color)
        Globals.ct.draw_indicator_line(right, bottom, *color)
        Globals.ct.draw_indicator_line(bottom, left, *color)
        Globals.ct.draw_indicator_line(left, top, *color)
