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

class HealTargetInfo:
    __slots__ = (
        'position', 'building_heal', 'building_hp', 'bot_heal', 'bot_hp',
        'harvester_adjacent', 'is_transporter', 'is_turret',
        'has_enemy_bot', 'bfs_dist_adj', 'entity_type',
    )

    @staticmethod
    def is_better_than(a: HealTargetInfo, b: HealTargetInfo) -> bool:
        adist = a.bfs_dist_adj
        bdist = b.bfs_dist_adj

        if adist >= 100: return False
        if bdist >= 100: return True

        if bool(a.building_heal) != bool(b.building_heal): # Don't compare micro values of healing because of 4 HP roads
            return a.building_heal > b.building_heal
        
        if a.is_turret != b.is_turret:
            return a.is_turret > b.is_turret
            
        
        if a.harvester_adjacent != b.harvester_adjacent:
            return a.harvester_adjacent > b.harvester_adjacent
            
        # Transporters are only more important if not next to a harvester
        if not a.harvester_adjacent:
            if a.is_transporter != b.is_transporter:
                return a.is_transporter > b.is_transporter
    
        if a.has_enemy_bot != b.has_enemy_bot:
            return a.has_enemy_bot > b.has_enemy_bot
        
        ahp = a.building_hp
        bhp = b.building_hp

        # # prevent excessive jittering
        # if abs(ahp - bhp) <= 4 and max(adist, bdist) > 2:
        #     if adist != bdist:
        #         return adist < bdist

        if ahp != bhp:
            return ahp < bhp

        if adist != bdist:
            return adist < bdist

        if a.bot_heal != b.bot_heal:
            return a.bot_heal > b.bot_heal

        if a.bot_hp != b.bot_hp:
            return a.bot_hp < b.bot_hp

        return False


class HealTargeter:
    targets: list[HealTargetInfo] = []


    @classmethod
    def get_best_target_info(cls) -> HealTargetInfo | None:
        targets = cls.targets
        if not targets:
            return None

        best = targets[0]
        for cand in targets[1:]:
            if HealTargetInfo.is_better_than(cand, best):
                best = cand


        total_heal = best.building_heal + best.bot_heal
        if total_heal < 4:
            # Still heal buildings next to harvesters for shielding
            if not best.harvester_adjacent or total_heal == 0:
                return None

        if best.bfs_dist_adj >= 100:
            return None

        # if far away from core and not critical and core hp is high, do other stuff
        core_ti = Map.tile_info[Unit.core_pos.x][Unit.core_pos.y]
        if best.entity_type == EntityType.CORE:
            cond = best.building_hp < 500 - best.bfs_dist_adj * (core_ti.allied_bots_adjacent) * 4
            if not cond:
                return None
            
        # count canonical allies between us and the target
        ally_index = VisionTracker.canonical_ally_index(best.position)
        

        # if there are already enough canonical healers, ignore the target
        if ally_index * GameConstants.HEAL_AMOUNT > max(best.building_heal, best.bot_heal):
            return None


        return best


    @classmethod
    def fill(cls):
        cls.targets = []
        targets = cls.targets

        for pos, x, y, idx, ti in Map.proc_nearby_tiles:
            ti: TileInfo
            has_ally_building = ti.has_building and ti.is_building_ally
            has_ally_bot = ti.has_bot and ti.is_bot_ally
            if not has_ally_building and not has_ally_bot:
                continue

            info = HealTargetInfo()
            info.position = pos
            info.building_heal = 0
            info.bot_heal = 0
            info.building_hp = 1000000
            info.bot_hp = 1000000
            info.is_transporter = (ti.entity_type is not None and ti.entity_type in Constants.TRANSPORTERS_SET)
            # info.is_turret = (ti.entity_type is not None and ti.entity_type in Constants.TURRET_SET)
            info.is_turret = ti.has_turret
            info.has_enemy_bot = False
            info.bfs_dist_adj = BfsBureau.bfs20_dist_adj[idx]
            info.entity_type = ti.entity_type
            info.is_turret = ti.has_turret
            info.harvester_adjacent = ti.harvester_adjacent

            if has_ally_building:
                info.building_heal = min(
                    4,
                    Constants.MAX_HP_MAP[ti.entity_type] - ti.building_hp
                )
                info.building_hp = ti.building_hp

            if ti.has_bot:
                if ti.is_bot_ally:
                    info.bot_heal = min(
                        4,
                        40 - ti.bot_hp
                    )
                    info.bot_hp = ti.bot_hp
                else:
                    info.has_enemy_bot = True


            targets.append(info)

