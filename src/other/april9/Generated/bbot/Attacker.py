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

class Attacker:
    @classmethod
    def get_trans_target(cls) -> Position | None:
        trans: TransporterInfo = VisionTracker.get_best_trans_atk_target()
        if trans is None:
            return None
        if not trans.reachable: 
            return None
        if trans.flowing_into_ally:
            return None
        if trans.flow == 0:
            return None
        if not VisionTracker.me_is_canonical_ally(trans.position):
            return None
        return trans.position


    @classmethod
    def compute_readiness(cls):
        allies_ready = 0
        lst: tuple[int, int] = []

        for pos, x, y, idx, ti in Map.proc_nearby_tiles:
            if (ti.has_bot and ti.is_bot_ally) \
                    and (ti.has_building and not ti.is_building_ally) \
                    and (ti.entity_type in Constants.ATTACKABLE_TRANSPORTERS_SET):
                allies_ready += 1
                lst.append((x, y))

        enemies_ready_set: set[int] = set()  # hashed pos
        tile_info = Map.tile_info

        for x, y in lst:

            nti = tile_info[(x )][(y -1)]
            if nti is not None and nti.has_bot and not nti.is_bot_ally:
                enemies_ready_set.add(((x ) << 6) | (y -1))

            nti = tile_info[(x +1)][(y -1)]
            if nti is not None and nti.has_bot and not nti.is_bot_ally:
                enemies_ready_set.add(((x +1) << 6) | (y -1))

            nti = tile_info[(x +1)][(y )]
            if nti is not None and nti.has_bot and not nti.is_bot_ally:
                enemies_ready_set.add(((x +1) << 6) | (y ))

            nti = tile_info[(x +1)][(y +1)]
            if nti is not None and nti.has_bot and not nti.is_bot_ally:
                enemies_ready_set.add(((x +1) << 6) | (y +1))

            nti = tile_info[(x )][(y +1)]
            if nti is not None and nti.has_bot and not nti.is_bot_ally:
                enemies_ready_set.add(((x ) << 6) | (y +1))

            nti = tile_info[(x -1)][(y +1)]
            if nti is not None and nti.has_bot and not nti.is_bot_ally:
                enemies_ready_set.add(((x -1) << 6) | (y +1))

            nti = tile_info[(x -1)][(y )]
            if nti is not None and nti.has_bot and not nti.is_bot_ally:
                enemies_ready_set.add(((x -1) << 6) | (y ))

            nti = tile_info[(x -1)][(y -1)]
            if nti is not None and nti.has_bot and not nti.is_bot_ally:
                enemies_ready_set.add(((x -1) << 6) | (y -1))

        return allies_ready, len(enemies_ready_set)


    @classmethod
    def should_fire(cls, pos):
        ti = Map.tile_info[pos.x][pos.y]

        # assume caller passes in enemy transporter position
        assert not ti.is_building_ally

        hp = ti.building_hp
        max_hp = Constants.MAX_HP_MAP[ti.entity_type]

        if 2 * hp <= max_hp:
            return True

        allies_ready, enemies_ready = cls.compute_readiness()

        if allies_ready > 2 * enemies_ready:
            return True

        return False


