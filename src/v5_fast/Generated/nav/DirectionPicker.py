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
from Awubot.Constants import Constants
from Awubot.Globals import Globals
from Awubot.Map import TileInfo, Map
from Awubot.MoveManager import MoveManager
from Awubot.Util import Util
from Awubot.build.Builder import BuilderState, Builder
from Awubot.core.Core import Core
from Awubot.debug.Profiler import Profiler
from Awubot.explore.Explore import Explore
from Awubot.nav.Pathfinder import Pathfinder
from Generated.MarketMaker import MarketMaker
from Generated.RobotPlayer import Entrypoint, Player
from Generated.Unit import Unit
from Generated.build.BuildManager import BuildManager
from Generated.build.OreExecutive import OreExecutive
from Generated.build.OrePositionPicker import OrePositionPicker
from Generated.build.RouteToCore import RouteToCore
from Generated.build.SuicideExecutor import SuicideExecutor
from Generated.debug.Debug import Color, Debug
from Generated.heal.HealExecutor import HealExecutor
from Generated.nav.BfsBureau import BfsBureau
from Generated.nav.ClaudeGlobalBfs import ClaudeGlobalBfs
from Generated.nav.DialDijkstra import DialDijkstra
from Generated.nav.DirectionPicker import DirectionPicker
from Generated.nav.EgoBridgeBfs import EgoBridgeBfs
from Generated.nav.MyGlobalBfs import MyGlobalBfs
from Generated.nav.MyGlobalBfs2 import MyGlobalBfs2


class DirectionPicker:
    class Candidate(NamedTuple):
        direction: Direction
        position: Position
        banned: bool
        moveable: bool
        fill_moveable: bool
        dist: int
        closer_than_center: bool
        rand_key: float

    cand: list[Candidate | None] = [None] * 9

    @classmethod
    def precompute(cls, dist: list[list[int]], ban_target_pos: bool = False):
        my_pos = Globals.ct.get_position()
        center_dist = dist[my_pos.x][my_pos.y]

        d = dist[my_pos.x +0][my_pos.y +0]
        cls.cand[8] = cls.Candidate(
            Direction.CENTRE,
            my_pos.add(Direction.CENTRE),
            ban_target_pos and d == 0,
            MoveManager.can_move(Direction.CENTRE),
            MoveManager.can_fill_move(Direction.CENTRE),
            d,
            d < center_dist,
            random.random(),
        )
        d = dist[my_pos.x -1][my_pos.y -1]
        cls.cand[7] = cls.Candidate(
            Direction.NORTHWEST,
            my_pos.add(Direction.NORTHWEST),
            ban_target_pos and d == 0,
            MoveManager.can_move(Direction.NORTHWEST),
            MoveManager.can_fill_move(Direction.NORTHWEST),
            d,
            d < center_dist,
            random.random(),
        )
        d = dist[my_pos.x -1][my_pos.y +0]
        cls.cand[6] = cls.Candidate(
            Direction.WEST,
            my_pos.add(Direction.WEST),
            ban_target_pos and d == 0,
            MoveManager.can_move(Direction.WEST),
            MoveManager.can_fill_move(Direction.WEST),
            d,
            d < center_dist,
            random.random(),
        )
        d = dist[my_pos.x -1][my_pos.y +1]
        cls.cand[5] = cls.Candidate(
            Direction.SOUTHWEST,
            my_pos.add(Direction.SOUTHWEST),
            ban_target_pos and d == 0,
            MoveManager.can_move(Direction.SOUTHWEST),
            MoveManager.can_fill_move(Direction.SOUTHWEST),
            d,
            d < center_dist,
            random.random(),
        )
        d = dist[my_pos.x +0][my_pos.y +1]
        cls.cand[4] = cls.Candidate(
            Direction.SOUTH,
            my_pos.add(Direction.SOUTH),
            ban_target_pos and d == 0,
            MoveManager.can_move(Direction.SOUTH),
            MoveManager.can_fill_move(Direction.SOUTH),
            d,
            d < center_dist,
            random.random(),
        )
        d = dist[my_pos.x +1][my_pos.y +1]
        cls.cand[3] = cls.Candidate(
            Direction.SOUTHEAST,
            my_pos.add(Direction.SOUTHEAST),
            ban_target_pos and d == 0,
            MoveManager.can_move(Direction.SOUTHEAST),
            MoveManager.can_fill_move(Direction.SOUTHEAST),
            d,
            d < center_dist,
            random.random(),
        )
        d = dist[my_pos.x +1][my_pos.y +0]
        cls.cand[2] = cls.Candidate(
            Direction.EAST,
            my_pos.add(Direction.EAST),
            ban_target_pos and d == 0,
            MoveManager.can_move(Direction.EAST),
            MoveManager.can_fill_move(Direction.EAST),
            d,
            d < center_dist,
            random.random(),
        )
        d = dist[my_pos.x +1][my_pos.y -1]
        cls.cand[1] = cls.Candidate(
            Direction.NORTHEAST,
            my_pos.add(Direction.NORTHEAST),
            ban_target_pos and d == 0,
            MoveManager.can_move(Direction.NORTHEAST),
            MoveManager.can_fill_move(Direction.NORTHEAST),
            d,
            d < center_dist,
            random.random(),
        )
        d = dist[my_pos.x +0][my_pos.y -1]
        cls.cand[0] = cls.Candidate(
            Direction.NORTH,
            my_pos.add(Direction.NORTH),
            ban_target_pos and d == 0,
            MoveManager.can_move(Direction.NORTH),
            MoveManager.can_fill_move(Direction.NORTH),
            d,
            d < center_dist,
            random.random(),
        )

    @classmethod
    def is_better_than(cls, a: Candidate, b: Candidate) -> bool:
        if a.banned and (not b.banned):
            return False
        if (not a.banned) and b.banned:
            return True

        if a.fill_moveable and (not b.fill_moveable):
            return True
        if (not a.fill_moveable) and b.fill_moveable:
            return False

        if a.closer_than_center and (not b.closer_than_center):
             return True
        if (not a.closer_than_center) and b.closer_than_center:
             return False

        if a.moveable and (not b.moveable):
             return True
        if (not a.moveable) and b.moveable:
             return False

        if a.dist != b.dist:
            return a.dist < b.dist

        return a.rand_key < b.rand_key

    @classmethod
    def pick_best_candidate(cls, dist: list[list[int]], ban_target_pos: bool = False) -> Candidate:
        cls.precompute(dist, ban_target_pos)

        best = cls.cand[8]
        if cls.is_better_than(cls.cand[7], best):
            best = cls.cand[7]
        if cls.is_better_than(cls.cand[6], best):
            best = cls.cand[6]
        if cls.is_better_than(cls.cand[5], best):
            best = cls.cand[5]
        if cls.is_better_than(cls.cand[4], best):
            best = cls.cand[4]
        if cls.is_better_than(cls.cand[3], best):
            best = cls.cand[3]
        if cls.is_better_than(cls.cand[2], best):
            best = cls.cand[2]
        if cls.is_better_than(cls.cand[1], best):
            best = cls.cand[1]
        if cls.is_better_than(cls.cand[0], best):
            best = cls.cand[0]

        return best








