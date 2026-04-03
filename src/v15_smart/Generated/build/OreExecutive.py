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
# ===--- IMPORT



class OreExecutive:
    ore_pos: Position | None = None  # current

    state: dict[Position, int] = defaultdict(int)  
    ti_queue: list[tuple[int, Position]] = []


    @classmethod
    def register_ti(cls, pos: Position):
        if cls.state[pos] == 0:
            dist = pos.distance_squared(Unit.core_pos)
            heapq.heappush(cls.ti_queue, (dist, pos))
            cls.state[pos] = 1


    @classmethod
    def fill(cls):
        for pos in Map.nearby_tiles:
            # not using Map.harvester_set..?

            if cls.state[pos] == 2:
                continue
            ti = Map.tile_info[pos.x][pos.y]
            env = ti.env
            if ti.entity_type == EntityType.HARVESTER:
                continue

            if env == Environment.ORE_TITANIUM:
                if cls.state[pos] != 1:  # intended: can potentially requeue
                    dist = pos.distance_squared(Unit.core_pos)
                    heapq.heappush(cls.ti_queue, (dist, pos))
                    cls.state[pos] = 1


    @classmethod
    def get_target(cls) -> Position | None:
        ret = None
        while cls.ti_queue:
            dist, pos = cls.ti_queue[0]

            if cls.state[pos] == 2:
                heapq.heappop(cls.ti_queue)
                continue

            ti = Map.tile_info[pos.x][pos.y]

            if ti.entity_type == EntityType.HARVESTER:
                heapq.heappop(cls.ti_queue)
                cls.state[pos] = 3
                continue

            if not ti.has_bot and MarketMaker.should_build_harvester(pos):
                ret = pos
                break
            else:
                break

        if ret is None:
            return None

        if not VisionTracker.me_is_canonical_ally(ret):
            # just kill?
            cls.state[ret] = 2
            return None

        return ret


    @classmethod
    def go_build_harvester(cls, pos):
        Pathfinder.move_to(pos, ban_target_pos=True)

        if Pathfinder.given_up:
            Debug.line(pos, Color.RED)
            Debug.diamond(Color.RED)
            cls.state[pos] = 2
            return

        if BuildManager.can_dbuild_harvester(pos):
            Debug.line(pos, Color.YELLOW)
            BuildManager.dbuild_harvester(pos)

            cand: OrePositionPicker.Candidate = OrePositionPicker.pick_best_candidate(pos)
            RouteToCore.set_pos(cand.position)