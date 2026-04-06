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


class ShieldTargetInfo:
    position: Position
    harvester_adjacent: bool

    @staticmethod
    def is_better_than(a: ShieldTargetInfo, b: ShieldTargetInfo) -> bool:
        if not a.harvester_adjacent: return False
        if not b.harvester_adjacent: return True

        return False


class ShieldTargeter:
    targets: list[ShieldTargetInfo] = []


    @classmethod
    def get_best_target(cls) -> Position | None:
        targets = cls.targets
        if not targets:
            return None

        best = targets[0]
        for cand in targets[1:]:
            if ShieldTargetInfo.is_better_than(cand, best):
                best = cand

        if not best.harvester_adjacent:
            return None


        return best.position


    @classmethod
    def fill(cls):
        cls.targets = []
        targets = cls.targets

        for pos, x, y, idx, ti in Map.proc_nearby_tiles:
            ti: TileInfo

            if not ti.harvester_adjacent:
                continue

            if ti.has_building:
                if not ti.is_building_ally:
                    continue
                elif ti.entity_type != EntityType.ROAD:
                    continue

            if ti.has_bot:
                continue

            info = ShieldTargetInfo()
            info.position = pos
            info.harvester_adjacent = ti.harvester_adjacent

            targets.append(info)