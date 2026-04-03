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
from Awubot.Constants import Constants
from Awubot.Core import Core
from Awubot.Globals import Globals, Cache
from Awubot.Map import LocalMask, MapMask, TileInfo, Map
from Awubot.MoveManager import MoveManager
from Awubot.RobotPlayer import Entrypoint, Player
from Awubot.Util import Util
from Awubot.build.Builder import BuilderState, Builder
from Awubot.debug.Profiler import Profiler
from Awubot.explore.Explore import Explore
from Awubot.nav.Pathfinder import Pathfinder
from Generated.Unit import Unit
from Generated.build.BuildManager import BuildManager
from Generated.build.OreExecutive import OreExecutive
from Generated.build.OrePositionPicker import OrePositionPicker
from Generated.build.RouteToCore import RouteToCore
from Generated.debug.Debug import Color, Debug
from Generated.nav.ClaudeGlobalBfs import ClaudeGlobalBfs
from Generated.nav.DirectionPicker import DirectionPicker
from Generated.nav.EgoBridgeBfs import EgoBridgeBfs


class OrePositionPicker:
    class Candidate(NamedTuple):
        position: Position
        ti: TileInfo | None  # if None, it is outside map
        build_metric: int  # manhattan, but if directly on top, need to ~take a step back~

    cand: list[Candidate | None] = [None] * 4

    @classmethod
    def precompute(cls, ore_pos: Position):
        my_pos = Globals.ct.get_position()
        me_x, me_y = my_pos.x, my_pos.y

        x, y = ore_pos.x, ore_pos.y


        nx, ny = x , y -1

        build_metric = max(abs(nx - me_x), abs(ny - me_y)) 
        if build_metric == 0:
            build_metric += 2

        cls.cand[0] = cls.Candidate(
            Position(nx, ny),
            Map.tile_info[nx][ny],
            build_metric,
        )

        nx, ny = x +1, y 

        build_metric = max(abs(nx - me_x), abs(ny - me_y)) 
        if build_metric == 0:
            build_metric += 2

        cls.cand[1] = cls.Candidate(
            Position(nx, ny),
            Map.tile_info[nx][ny],
            build_metric,
        )

        nx, ny = x , y +1

        build_metric = max(abs(nx - me_x), abs(ny - me_y)) 
        if build_metric == 0:
            build_metric += 2

        cls.cand[2] = cls.Candidate(
            Position(nx, ny),
            Map.tile_info[nx][ny],
            build_metric,
        )

        nx, ny = x -1, y 

        build_metric = max(abs(nx - me_x), abs(ny - me_y)) 
        if build_metric == 0:
            build_metric += 2

        cls.cand[3] = cls.Candidate(
            Position(nx, ny),
            Map.tile_info[nx][ny],
            build_metric,
        )

    @classmethod
    def is_better_than(cls, a: Candidate, b: Candidate) -> bool:
        # prio:
        # 1. on map
        # 2. empty
        # 3. no building
        # 4. has ally building AND is road
        # 5. no builder bot
        # 6. build metric
        # 7. arbitrary

        if a.ti is None and (b.ti is not None):
            return False
        if (a.ti is not None) and b.ti is None:
            return True

        EMPTY = Environment.EMPTY

        if a.ti.env == EMPTY and b.ti.env != EMPTY:
            return True
        if a.ti.env != EMPTY and b.ti.env == EMPTY:
            return False

        if a.ti.has_building and (not b.ti.has_building):
            return False
        if (not a.ti.has_building) and b.ti.has_building:
            return True

        if a.ti.has_building and b.ti.has_building:
            ROAD = EntityType.ROAD
            a_cond = a.ti.is_building_ally and a.ti.entity_type == ROAD
            b_cond = b.ti.is_building_ally and b.ti.entity_type == ROAD

            if a_cond and (not b_cond):
                return True
            if (not a_cond) and b_cond:
                return False

        if a.ti.has_builder_bot and (not b.ti.has_builder_bot):
            return False
        if (not a.ti.has_builder_bot) and b.ti.has_builder_bot:
            return True

        if a.build_metric != b.build_metric:
            return a.build_metric < b.build_metric

        return True  # arbitrary

    @classmethod
    def pick_best_candidate(cls, ore_pos: Position) -> Candidate:
        cls.precompute(ore_pos)

        best = cls.cand[3]
        if cls.is_better_than(cls.cand[2], best):
            best = cls.cand[2]
        if cls.is_better_than(cls.cand[1], best):
            best = cls.cand[1]
        if cls.is_better_than(cls.cand[0], best):
            best = cls.cand[0]

        return best










