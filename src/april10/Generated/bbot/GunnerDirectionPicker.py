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

class GunnerDirectionInfo:
    direction: Direction
    banned: bool
    enemy_building_hp: int  # sum of all in attack range
    enemy_bot_hp: int
    cosine_sim: float  # normalised dot product of vector to enemy core

    @staticmethod
    def is_better_than(a: GunnerDirectionInfo, b: GunnerDirectionInfo) -> bool:
        if a.banned: return False
        if b.banned: return True

        if a.enemy_building_hp != b.enemy_building_hp:
            return a.enemy_building_hp > b.enemy_building_hp

        if a.enemy_bot_hp != b.enemy_bot_hp:
            return a.enemy_bot_hp > b.enemy_bot_hp

        return a.cosine_sim > b.cosine_sim


class GunnerDirectionPicker:
    infos: list[GunnerDirectionInfo] = []


    @classmethod
    def get_best_direction(cls, spos) -> Direction:
        cls.precompute(spos)
        best = cls.infos[0]
        for info in cls.infos[1:]:
            if GunnerDirectionInfo.is_better_than(info, best):
                best = info
        return best.direction

    @classmethod
    def precompute(cls, spos):
        infos = cls.infos
        infos.clear()

        tile_info = Map.tile_info

        sx, sy = spos.x, spos.y
        sidx = (((sx) + 3) * 56 + ((sy) + 3))

        has_feeder = [False] * 8
        nadj_feeders = 0

        ti = tile_info[sx + 0][sy + -1]
        if ti is not None:
            if (ti.entity_type == EntityType.HARVESTER and ti.env == Environment.ORE_TITANIUM) or ti.target == spos:
                has_feeder[0] = True
                nadj_feeders += 1
        ti = tile_info[sx + 1][sy + 0]
        if ti is not None:
            if (ti.entity_type == EntityType.HARVESTER and ti.env == Environment.ORE_TITANIUM) or ti.target == spos:
                has_feeder[2] = True
                nadj_feeders += 1
        ti = tile_info[sx + 0][sy + 1]
        if ti is not None:
            if (ti.entity_type == EntityType.HARVESTER and ti.env == Environment.ORE_TITANIUM) or ti.target == spos:
                has_feeder[4] = True
                nadj_feeders += 1
        ti = tile_info[sx + -1][sy + 0]
        if ti is not None:
            if (ti.entity_type == EntityType.HARVESTER and ti.env == Environment.ORE_TITANIUM) or ti.target == spos:
                has_feeder[6] = True
                nadj_feeders += 1

        ecore = Symmetry.enemy_core_pos


        if nadj_feeders == 1:

            info0 = GunnerDirectionInfo()
            info0.direction = Direction.NORTH
            info0.banned = has_feeder[0]
            info0.enemy_building_hp = 0
            info0.enemy_bot_hp = 0

            u1, u2 = ecore.x - sx, ecore.y - sy
            mu = math.hypot(u1, u2)
            u1 /= mu
            u2 /= mu
            info0.cosine_sim = u1 * 0.0 + u2 * -1.0

            infos.append(info0)

            info1 = GunnerDirectionInfo()
            info1.direction = Direction.NORTHEAST
            info1.banned = has_feeder[1]
            info1.enemy_building_hp = 0
            info1.enemy_bot_hp = 0

            u1, u2 = ecore.x - sx, ecore.y - sy
            mu = math.hypot(u1, u2)
            u1 /= mu
            u2 /= mu
            info1.cosine_sim = u1 * 0.7071067811865475 + u2 * -0.7071067811865475

            infos.append(info1)

            info2 = GunnerDirectionInfo()
            info2.direction = Direction.EAST
            info2.banned = has_feeder[2]
            info2.enemy_building_hp = 0
            info2.enemy_bot_hp = 0

            u1, u2 = ecore.x - sx, ecore.y - sy
            mu = math.hypot(u1, u2)
            u1 /= mu
            u2 /= mu
            info2.cosine_sim = u1 * 1.0 + u2 * 0.0

            infos.append(info2)

            info3 = GunnerDirectionInfo()
            info3.direction = Direction.SOUTHEAST
            info3.banned = has_feeder[3]
            info3.enemy_building_hp = 0
            info3.enemy_bot_hp = 0

            u1, u2 = ecore.x - sx, ecore.y - sy
            mu = math.hypot(u1, u2)
            u1 /= mu
            u2 /= mu
            info3.cosine_sim = u1 * 0.7071067811865475 + u2 * 0.7071067811865475

            infos.append(info3)

            info4 = GunnerDirectionInfo()
            info4.direction = Direction.SOUTH
            info4.banned = has_feeder[4]
            info4.enemy_building_hp = 0
            info4.enemy_bot_hp = 0

            u1, u2 = ecore.x - sx, ecore.y - sy
            mu = math.hypot(u1, u2)
            u1 /= mu
            u2 /= mu
            info4.cosine_sim = u1 * 0.0 + u2 * 1.0

            infos.append(info4)

            info5 = GunnerDirectionInfo()
            info5.direction = Direction.SOUTHWEST
            info5.banned = has_feeder[5]
            info5.enemy_building_hp = 0
            info5.enemy_bot_hp = 0

            u1, u2 = ecore.x - sx, ecore.y - sy
            mu = math.hypot(u1, u2)
            u1 /= mu
            u2 /= mu
            info5.cosine_sim = u1 * -0.7071067811865475 + u2 * 0.7071067811865475

            infos.append(info5)

            info6 = GunnerDirectionInfo()
            info6.direction = Direction.WEST
            info6.banned = has_feeder[6]
            info6.enemy_building_hp = 0
            info6.enemy_bot_hp = 0

            u1, u2 = ecore.x - sx, ecore.y - sy
            mu = math.hypot(u1, u2)
            u1 /= mu
            u2 /= mu
            info6.cosine_sim = u1 * -1.0 + u2 * 0.0

            infos.append(info6)

            info7 = GunnerDirectionInfo()
            info7.direction = Direction.NORTHWEST
            info7.banned = has_feeder[7]
            info7.enemy_building_hp = 0
            info7.enemy_bot_hp = 0

            u1, u2 = ecore.x - sx, ecore.y - sy
            mu = math.hypot(u1, u2)
            u1 /= mu
            u2 /= mu
            info7.cosine_sim = u1 * -0.7071067811865475 + u2 * -0.7071067811865475

            infos.append(info7)

        else:

            info0 = GunnerDirectionInfo()
            info0.direction = Direction.NORTH
            info0.banned = False
            info0.enemy_building_hp = 0
            info0.enemy_bot_hp = 0

            u1, u2 = ecore.x - sx, ecore.y - sy
            mu = math.hypot(u1, u2)
            u1 /= mu
            u2 /= mu
            info0.cosine_sim = u1 * 0.0 + u2 * -1.0

            infos.append(info0)

            info1 = GunnerDirectionInfo()
            info1.direction = Direction.NORTHEAST
            info1.banned = False
            info1.enemy_building_hp = 0
            info1.enemy_bot_hp = 0

            u1, u2 = ecore.x - sx, ecore.y - sy
            mu = math.hypot(u1, u2)
            u1 /= mu
            u2 /= mu
            info1.cosine_sim = u1 * 0.7071067811865475 + u2 * -0.7071067811865475

            infos.append(info1)

            info2 = GunnerDirectionInfo()
            info2.direction = Direction.EAST
            info2.banned = False
            info2.enemy_building_hp = 0
            info2.enemy_bot_hp = 0

            u1, u2 = ecore.x - sx, ecore.y - sy
            mu = math.hypot(u1, u2)
            u1 /= mu
            u2 /= mu
            info2.cosine_sim = u1 * 1.0 + u2 * 0.0

            infos.append(info2)

            info3 = GunnerDirectionInfo()
            info3.direction = Direction.SOUTHEAST
            info3.banned = False
            info3.enemy_building_hp = 0
            info3.enemy_bot_hp = 0

            u1, u2 = ecore.x - sx, ecore.y - sy
            mu = math.hypot(u1, u2)
            u1 /= mu
            u2 /= mu
            info3.cosine_sim = u1 * 0.7071067811865475 + u2 * 0.7071067811865475

            infos.append(info3)

            info4 = GunnerDirectionInfo()
            info4.direction = Direction.SOUTH
            info4.banned = False
            info4.enemy_building_hp = 0
            info4.enemy_bot_hp = 0

            u1, u2 = ecore.x - sx, ecore.y - sy
            mu = math.hypot(u1, u2)
            u1 /= mu
            u2 /= mu
            info4.cosine_sim = u1 * 0.0 + u2 * 1.0

            infos.append(info4)

            info5 = GunnerDirectionInfo()
            info5.direction = Direction.SOUTHWEST
            info5.banned = False
            info5.enemy_building_hp = 0
            info5.enemy_bot_hp = 0

            u1, u2 = ecore.x - sx, ecore.y - sy
            mu = math.hypot(u1, u2)
            u1 /= mu
            u2 /= mu
            info5.cosine_sim = u1 * -0.7071067811865475 + u2 * 0.7071067811865475

            infos.append(info5)

            info6 = GunnerDirectionInfo()
            info6.direction = Direction.WEST
            info6.banned = False
            info6.enemy_building_hp = 0
            info6.enemy_bot_hp = 0

            u1, u2 = ecore.x - sx, ecore.y - sy
            mu = math.hypot(u1, u2)
            u1 /= mu
            u2 /= mu
            info6.cosine_sim = u1 * -1.0 + u2 * 0.0

            infos.append(info6)

            info7 = GunnerDirectionInfo()
            info7.direction = Direction.NORTHWEST
            info7.banned = False
            info7.enemy_building_hp = 0
            info7.enemy_bot_hp = 0

            u1, u2 = ecore.x - sx, ecore.y - sy
            mu = math.hypot(u1, u2)
            u1 /= mu
            u2 /= mu
            info7.cosine_sim = u1 * -0.7071067811865475 + u2 * -0.7071067811865475

            infos.append(info7)



        ti = tile_info[sx + -2][sy + -2]
        if ti is not None:
            if ti.has_building and not ti.is_building_ally:
                e_building_hp = ti.building_hp
                info7.enemy_building_hp += e_building_hp

            if ti.has_bot and not ti.is_bot_ally:
                e_bot_hp = ti.bot_hp
                info7.enemy_bot_hp += e_bot_hp
        ti = tile_info[sx + -2][sy + -1]
        if ti is not None:
            if ti.has_building and not ti.is_building_ally:
                e_building_hp = ti.building_hp
                info6.enemy_building_hp += e_building_hp
                info7.enemy_building_hp += e_building_hp

            if ti.has_bot and not ti.is_bot_ally:
                e_bot_hp = ti.bot_hp
                info6.enemy_bot_hp += e_bot_hp
                info7.enemy_bot_hp += e_bot_hp
        ti = tile_info[sx + -2][sy + 0]
        if ti is not None:
            if ti.has_building and not ti.is_building_ally:
                e_building_hp = ti.building_hp
                info5.enemy_building_hp += e_building_hp
                info6.enemy_building_hp += e_building_hp
                info7.enemy_building_hp += e_building_hp

            if ti.has_bot and not ti.is_bot_ally:
                e_bot_hp = ti.bot_hp
                info5.enemy_bot_hp += e_bot_hp
                info6.enemy_bot_hp += e_bot_hp
                info7.enemy_bot_hp += e_bot_hp
        ti = tile_info[sx + -2][sy + 1]
        if ti is not None:
            if ti.has_building and not ti.is_building_ally:
                e_building_hp = ti.building_hp
                info5.enemy_building_hp += e_building_hp
                info6.enemy_building_hp += e_building_hp

            if ti.has_bot and not ti.is_bot_ally:
                e_bot_hp = ti.bot_hp
                info5.enemy_bot_hp += e_bot_hp
                info6.enemy_bot_hp += e_bot_hp
        ti = tile_info[sx + -2][sy + 2]
        if ti is not None:
            if ti.has_building and not ti.is_building_ally:
                e_building_hp = ti.building_hp
                info5.enemy_building_hp += e_building_hp

            if ti.has_bot and not ti.is_bot_ally:
                e_bot_hp = ti.bot_hp
                info5.enemy_bot_hp += e_bot_hp
        ti = tile_info[sx + -1][sy + -2]
        if ti is not None:
            if ti.has_building and not ti.is_building_ally:
                e_building_hp = ti.building_hp
                info0.enemy_building_hp += e_building_hp
                info7.enemy_building_hp += e_building_hp

            if ti.has_bot and not ti.is_bot_ally:
                e_bot_hp = ti.bot_hp
                info0.enemy_bot_hp += e_bot_hp
                info7.enemy_bot_hp += e_bot_hp
        ti = tile_info[sx + -1][sy + -1]
        if ti is not None:
            if ti.has_building and not ti.is_building_ally:
                e_building_hp = ti.building_hp
                info0.enemy_building_hp += e_building_hp
                info6.enemy_building_hp += e_building_hp
                info7.enemy_building_hp += e_building_hp

            if ti.has_bot and not ti.is_bot_ally:
                e_bot_hp = ti.bot_hp
                info0.enemy_bot_hp += e_bot_hp
                info6.enemy_bot_hp += e_bot_hp
                info7.enemy_bot_hp += e_bot_hp
        ti = tile_info[sx + -1][sy + 0]
        if ti is not None:
            if ti.has_building and not ti.is_building_ally:
                e_building_hp = ti.building_hp
                info0.enemy_building_hp += e_building_hp
                info4.enemy_building_hp += e_building_hp
                info5.enemy_building_hp += e_building_hp
                info6.enemy_building_hp += e_building_hp
                info7.enemy_building_hp += e_building_hp

            if ti.has_bot and not ti.is_bot_ally:
                e_bot_hp = ti.bot_hp
                info0.enemy_bot_hp += e_bot_hp
                info4.enemy_bot_hp += e_bot_hp
                info5.enemy_bot_hp += e_bot_hp
                info6.enemy_bot_hp += e_bot_hp
                info7.enemy_bot_hp += e_bot_hp
        ti = tile_info[sx + -1][sy + 1]
        if ti is not None:
            if ti.has_building and not ti.is_building_ally:
                e_building_hp = ti.building_hp
                info4.enemy_building_hp += e_building_hp
                info5.enemy_building_hp += e_building_hp
                info6.enemy_building_hp += e_building_hp

            if ti.has_bot and not ti.is_bot_ally:
                e_bot_hp = ti.bot_hp
                info4.enemy_bot_hp += e_bot_hp
                info5.enemy_bot_hp += e_bot_hp
                info6.enemy_bot_hp += e_bot_hp
        ti = tile_info[sx + -1][sy + 2]
        if ti is not None:
            if ti.has_building and not ti.is_building_ally:
                e_building_hp = ti.building_hp
                info4.enemy_building_hp += e_building_hp
                info5.enemy_building_hp += e_building_hp

            if ti.has_bot and not ti.is_bot_ally:
                e_bot_hp = ti.bot_hp
                info4.enemy_bot_hp += e_bot_hp
                info5.enemy_bot_hp += e_bot_hp
        ti = tile_info[sx + 0][sy + -2]
        if ti is not None:
            if ti.has_building and not ti.is_building_ally:
                e_building_hp = ti.building_hp
                info0.enemy_building_hp += e_building_hp
                info1.enemy_building_hp += e_building_hp
                info7.enemy_building_hp += e_building_hp

            if ti.has_bot and not ti.is_bot_ally:
                e_bot_hp = ti.bot_hp
                info0.enemy_bot_hp += e_bot_hp
                info1.enemy_bot_hp += e_bot_hp
                info7.enemy_bot_hp += e_bot_hp
        ti = tile_info[sx + 0][sy + -1]
        if ti is not None:
            if ti.has_building and not ti.is_building_ally:
                e_building_hp = ti.building_hp
                info0.enemy_building_hp += e_building_hp
                info1.enemy_building_hp += e_building_hp
                info2.enemy_building_hp += e_building_hp
                info6.enemy_building_hp += e_building_hp
                info7.enemy_building_hp += e_building_hp

            if ti.has_bot and not ti.is_bot_ally:
                e_bot_hp = ti.bot_hp
                info0.enemy_bot_hp += e_bot_hp
                info1.enemy_bot_hp += e_bot_hp
                info2.enemy_bot_hp += e_bot_hp
                info6.enemy_bot_hp += e_bot_hp
                info7.enemy_bot_hp += e_bot_hp
        ti = tile_info[sx + 0][sy + 0]
        if ti is not None:
            if ti.has_building and not ti.is_building_ally:
                e_building_hp = ti.building_hp

            if ti.has_bot and not ti.is_bot_ally:
                e_bot_hp = ti.bot_hp
        ti = tile_info[sx + 0][sy + 1]
        if ti is not None:
            if ti.has_building and not ti.is_building_ally:
                e_building_hp = ti.building_hp
                info2.enemy_building_hp += e_building_hp
                info3.enemy_building_hp += e_building_hp
                info4.enemy_building_hp += e_building_hp
                info5.enemy_building_hp += e_building_hp
                info6.enemy_building_hp += e_building_hp

            if ti.has_bot and not ti.is_bot_ally:
                e_bot_hp = ti.bot_hp
                info2.enemy_bot_hp += e_bot_hp
                info3.enemy_bot_hp += e_bot_hp
                info4.enemy_bot_hp += e_bot_hp
                info5.enemy_bot_hp += e_bot_hp
                info6.enemy_bot_hp += e_bot_hp
        ti = tile_info[sx + 0][sy + 2]
        if ti is not None:
            if ti.has_building and not ti.is_building_ally:
                e_building_hp = ti.building_hp
                info3.enemy_building_hp += e_building_hp
                info4.enemy_building_hp += e_building_hp
                info5.enemy_building_hp += e_building_hp

            if ti.has_bot and not ti.is_bot_ally:
                e_bot_hp = ti.bot_hp
                info3.enemy_bot_hp += e_bot_hp
                info4.enemy_bot_hp += e_bot_hp
                info5.enemy_bot_hp += e_bot_hp
        ti = tile_info[sx + 1][sy + -2]
        if ti is not None:
            if ti.has_building and not ti.is_building_ally:
                e_building_hp = ti.building_hp
                info0.enemy_building_hp += e_building_hp
                info1.enemy_building_hp += e_building_hp

            if ti.has_bot and not ti.is_bot_ally:
                e_bot_hp = ti.bot_hp
                info0.enemy_bot_hp += e_bot_hp
                info1.enemy_bot_hp += e_bot_hp
        ti = tile_info[sx + 1][sy + -1]
        if ti is not None:
            if ti.has_building and not ti.is_building_ally:
                e_building_hp = ti.building_hp
                info0.enemy_building_hp += e_building_hp
                info1.enemy_building_hp += e_building_hp
                info2.enemy_building_hp += e_building_hp

            if ti.has_bot and not ti.is_bot_ally:
                e_bot_hp = ti.bot_hp
                info0.enemy_bot_hp += e_bot_hp
                info1.enemy_bot_hp += e_bot_hp
                info2.enemy_bot_hp += e_bot_hp
        ti = tile_info[sx + 1][sy + 0]
        if ti is not None:
            if ti.has_building and not ti.is_building_ally:
                e_building_hp = ti.building_hp
                info0.enemy_building_hp += e_building_hp
                info1.enemy_building_hp += e_building_hp
                info2.enemy_building_hp += e_building_hp
                info3.enemy_building_hp += e_building_hp
                info4.enemy_building_hp += e_building_hp

            if ti.has_bot and not ti.is_bot_ally:
                e_bot_hp = ti.bot_hp
                info0.enemy_bot_hp += e_bot_hp
                info1.enemy_bot_hp += e_bot_hp
                info2.enemy_bot_hp += e_bot_hp
                info3.enemy_bot_hp += e_bot_hp
                info4.enemy_bot_hp += e_bot_hp
        ti = tile_info[sx + 1][sy + 1]
        if ti is not None:
            if ti.has_building and not ti.is_building_ally:
                e_building_hp = ti.building_hp
                info2.enemy_building_hp += e_building_hp
                info3.enemy_building_hp += e_building_hp
                info4.enemy_building_hp += e_building_hp

            if ti.has_bot and not ti.is_bot_ally:
                e_bot_hp = ti.bot_hp
                info2.enemy_bot_hp += e_bot_hp
                info3.enemy_bot_hp += e_bot_hp
                info4.enemy_bot_hp += e_bot_hp
        ti = tile_info[sx + 1][sy + 2]
        if ti is not None:
            if ti.has_building and not ti.is_building_ally:
                e_building_hp = ti.building_hp
                info3.enemy_building_hp += e_building_hp
                info4.enemy_building_hp += e_building_hp

            if ti.has_bot and not ti.is_bot_ally:
                e_bot_hp = ti.bot_hp
                info3.enemy_bot_hp += e_bot_hp
                info4.enemy_bot_hp += e_bot_hp
        ti = tile_info[sx + 2][sy + -2]
        if ti is not None:
            if ti.has_building and not ti.is_building_ally:
                e_building_hp = ti.building_hp
                info1.enemy_building_hp += e_building_hp

            if ti.has_bot and not ti.is_bot_ally:
                e_bot_hp = ti.bot_hp
                info1.enemy_bot_hp += e_bot_hp
        ti = tile_info[sx + 2][sy + -1]
        if ti is not None:
            if ti.has_building and not ti.is_building_ally:
                e_building_hp = ti.building_hp
                info1.enemy_building_hp += e_building_hp
                info2.enemy_building_hp += e_building_hp

            if ti.has_bot and not ti.is_bot_ally:
                e_bot_hp = ti.bot_hp
                info1.enemy_bot_hp += e_bot_hp
                info2.enemy_bot_hp += e_bot_hp
        ti = tile_info[sx + 2][sy + 0]
        if ti is not None:
            if ti.has_building and not ti.is_building_ally:
                e_building_hp = ti.building_hp
                info1.enemy_building_hp += e_building_hp
                info2.enemy_building_hp += e_building_hp
                info3.enemy_building_hp += e_building_hp

            if ti.has_bot and not ti.is_bot_ally:
                e_bot_hp = ti.bot_hp
                info1.enemy_bot_hp += e_bot_hp
                info2.enemy_bot_hp += e_bot_hp
                info3.enemy_bot_hp += e_bot_hp
        ti = tile_info[sx + 2][sy + 1]
        if ti is not None:
            if ti.has_building and not ti.is_building_ally:
                e_building_hp = ti.building_hp
                info2.enemy_building_hp += e_building_hp
                info3.enemy_building_hp += e_building_hp

            if ti.has_bot and not ti.is_bot_ally:
                e_bot_hp = ti.bot_hp
                info2.enemy_bot_hp += e_bot_hp
                info3.enemy_bot_hp += e_bot_hp
        ti = tile_info[sx + 2][sy + 2]
        if ti is not None:
            if ti.has_building and not ti.is_building_ally:
                e_building_hp = ti.building_hp
                info3.enemy_building_hp += e_building_hp

            if ti.has_bot and not ti.is_bot_ally:
                e_bot_hp = ti.bot_hp
                info3.enemy_bot_hp += e_bot_hp





