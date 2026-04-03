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



class HealTargetInfo:
    position: Position
    building_heal: int
    building_hp: int
    bot_heal: int
    bot_hp: int

    @staticmethod
    def is_better_than(a: HealTargetInfo, b: HealTargetInfo) -> bool:
        if a.building_heal != b.building_heal:
            return a.building_heal > b.building_heal

        if a.building_hp != b.building_hp:
            return a.building_hp < b.building_hp

        if a.bot_heal != b.bot_heal:
            return a.bot_heal > b.bot_heal

        if a.bot_hp != b.bot_hp:
            return a.bot_hp < b.bot_hp

        return False


class HealTargeter:
    targets: list[HealTargetInfo] = []


    @classmethod
    def get_best_target(cls) -> Position | None:
        targets = cls.targets
        if not targets:
            return None

        best = targets[0]
        for cand in targets[1:]:
            if HealTargetInfo.is_better_than(cand, best):
                best = cand

        if best.building_heal + best.bot_heal < 4:
            return None


        return best.position


    @classmethod
    def fill(cls):
        cls.targets = []
        targets = cls.targets

        for pos, x, y, idx, ti in Map.proc_nearby_tiles:
            ti: TileInfo

            info = HealTargetInfo()
            info.position = pos
            info.building_heal = 0
            info.bot_heal = 0
            info.building_hp = 1000000
            info.bot_hp = 1000000

            if ti.has_building and ti.is_building_ally:
                info.building_heal = min(
                    4,
                    Constants.MAX_HP_MAP[ti.entity_type] - ti.building_hp
                )
                info.building_hp = ti.building_hp

            if ti.has_bot and ti.is_bot_ally:
                info.bot_heal = min(
                    4,
                    30 - ti.bot_hp
                )
                info.bot_hp = ti.bot_hp


            targets.append(info)

