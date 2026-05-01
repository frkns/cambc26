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

class HealExecutor:
    last_healed: Candidate | None = None
    last_healed_round: int = -1
        
    class Candidate:
        position: Position
        is_accessible: bool
        building_heal: int
        building_hp: int
        bot_heal: int
        bot_hp: int
        is_turret: bool
        entity_type: EntityType
        harvester_adjacent: bool
        is_launcher: bool
        is_gunner: bool


    cand: list[Candidate | None] = [None] * 9


    @classmethod
    def precompute(cls):
        my_pos = Globals.my_pos
        can_heal = Globals.ct.can_heal
        tile_info = Map.tile_info


        nx, ny = my_pos.x , my_pos.y -1
        npos = Position(nx, ny)

        cand = cls.Candidate()
        cls.cand[0] = cand

        if can_heal(npos):
            cand.is_accessible = True
            cand.position = npos
            cand.building_heal = 0
            cand.bot_heal = 0
            cand.building_hp = 1000000
            cand.bot_hp = 1000000
            cand.is_turret = False

            ti = tile_info[nx][ny]
            cand.entity_type = ti.entity_type
            cand.harvester_adjacent = ti.harvester_adjacent
            cand.is_launcher = cand.entity_type == EntityType.LAUNCHER
            cand.is_gunner = cand.entity_type == EntityType.GUNNER

            if ti.has_building and ti.is_building_ally:
                cand.building_heal = min(
                    4,
                    Constants.MAX_HP_MAP[ti.entity_type] - ti.building_hp
                )
                cand.building_hp = ti.building_hp
                cand.is_turret = ti.has_turret

            if ti.has_bot and ti.is_bot_ally:
                cand.bot_heal = min(
                    4,
                    40 - ti.bot_hp
                )
                cand.bot_hp = ti.bot_hp
        else:
            cand.is_accessible = False

        nx, ny = my_pos.x +1, my_pos.y -1
        npos = Position(nx, ny)

        cand = cls.Candidate()
        cls.cand[1] = cand

        if can_heal(npos):
            cand.is_accessible = True
            cand.position = npos
            cand.building_heal = 0
            cand.bot_heal = 0
            cand.building_hp = 1000000
            cand.bot_hp = 1000000
            cand.is_turret = False

            ti = tile_info[nx][ny]
            cand.entity_type = ti.entity_type
            cand.harvester_adjacent = ti.harvester_adjacent
            cand.is_launcher = cand.entity_type == EntityType.LAUNCHER
            cand.is_gunner = cand.entity_type == EntityType.GUNNER

            if ti.has_building and ti.is_building_ally:
                cand.building_heal = min(
                    4,
                    Constants.MAX_HP_MAP[ti.entity_type] - ti.building_hp
                )
                cand.building_hp = ti.building_hp
                cand.is_turret = ti.has_turret

            if ti.has_bot and ti.is_bot_ally:
                cand.bot_heal = min(
                    4,
                    40 - ti.bot_hp
                )
                cand.bot_hp = ti.bot_hp
        else:
            cand.is_accessible = False

        nx, ny = my_pos.x +1, my_pos.y 
        npos = Position(nx, ny)

        cand = cls.Candidate()
        cls.cand[2] = cand

        if can_heal(npos):
            cand.is_accessible = True
            cand.position = npos
            cand.building_heal = 0
            cand.bot_heal = 0
            cand.building_hp = 1000000
            cand.bot_hp = 1000000
            cand.is_turret = False

            ti = tile_info[nx][ny]
            cand.entity_type = ti.entity_type
            cand.harvester_adjacent = ti.harvester_adjacent
            cand.is_launcher = cand.entity_type == EntityType.LAUNCHER
            cand.is_gunner = cand.entity_type == EntityType.GUNNER

            if ti.has_building and ti.is_building_ally:
                cand.building_heal = min(
                    4,
                    Constants.MAX_HP_MAP[ti.entity_type] - ti.building_hp
                )
                cand.building_hp = ti.building_hp
                cand.is_turret = ti.has_turret

            if ti.has_bot and ti.is_bot_ally:
                cand.bot_heal = min(
                    4,
                    40 - ti.bot_hp
                )
                cand.bot_hp = ti.bot_hp
        else:
            cand.is_accessible = False

        nx, ny = my_pos.x +1, my_pos.y +1
        npos = Position(nx, ny)

        cand = cls.Candidate()
        cls.cand[3] = cand

        if can_heal(npos):
            cand.is_accessible = True
            cand.position = npos
            cand.building_heal = 0
            cand.bot_heal = 0
            cand.building_hp = 1000000
            cand.bot_hp = 1000000
            cand.is_turret = False

            ti = tile_info[nx][ny]
            cand.entity_type = ti.entity_type
            cand.harvester_adjacent = ti.harvester_adjacent
            cand.is_launcher = cand.entity_type == EntityType.LAUNCHER
            cand.is_gunner = cand.entity_type == EntityType.GUNNER

            if ti.has_building and ti.is_building_ally:
                cand.building_heal = min(
                    4,
                    Constants.MAX_HP_MAP[ti.entity_type] - ti.building_hp
                )
                cand.building_hp = ti.building_hp
                cand.is_turret = ti.has_turret

            if ti.has_bot and ti.is_bot_ally:
                cand.bot_heal = min(
                    4,
                    40 - ti.bot_hp
                )
                cand.bot_hp = ti.bot_hp
        else:
            cand.is_accessible = False

        nx, ny = my_pos.x , my_pos.y +1
        npos = Position(nx, ny)

        cand = cls.Candidate()
        cls.cand[4] = cand

        if can_heal(npos):
            cand.is_accessible = True
            cand.position = npos
            cand.building_heal = 0
            cand.bot_heal = 0
            cand.building_hp = 1000000
            cand.bot_hp = 1000000
            cand.is_turret = False

            ti = tile_info[nx][ny]
            cand.entity_type = ti.entity_type
            cand.harvester_adjacent = ti.harvester_adjacent
            cand.is_launcher = cand.entity_type == EntityType.LAUNCHER
            cand.is_gunner = cand.entity_type == EntityType.GUNNER

            if ti.has_building and ti.is_building_ally:
                cand.building_heal = min(
                    4,
                    Constants.MAX_HP_MAP[ti.entity_type] - ti.building_hp
                )
                cand.building_hp = ti.building_hp
                cand.is_turret = ti.has_turret

            if ti.has_bot and ti.is_bot_ally:
                cand.bot_heal = min(
                    4,
                    40 - ti.bot_hp
                )
                cand.bot_hp = ti.bot_hp
        else:
            cand.is_accessible = False

        nx, ny = my_pos.x -1, my_pos.y +1
        npos = Position(nx, ny)

        cand = cls.Candidate()
        cls.cand[5] = cand

        if can_heal(npos):
            cand.is_accessible = True
            cand.position = npos
            cand.building_heal = 0
            cand.bot_heal = 0
            cand.building_hp = 1000000
            cand.bot_hp = 1000000
            cand.is_turret = False

            ti = tile_info[nx][ny]
            cand.entity_type = ti.entity_type
            cand.harvester_adjacent = ti.harvester_adjacent
            cand.is_launcher = cand.entity_type == EntityType.LAUNCHER
            cand.is_gunner = cand.entity_type == EntityType.GUNNER

            if ti.has_building and ti.is_building_ally:
                cand.building_heal = min(
                    4,
                    Constants.MAX_HP_MAP[ti.entity_type] - ti.building_hp
                )
                cand.building_hp = ti.building_hp
                cand.is_turret = ti.has_turret

            if ti.has_bot and ti.is_bot_ally:
                cand.bot_heal = min(
                    4,
                    40 - ti.bot_hp
                )
                cand.bot_hp = ti.bot_hp
        else:
            cand.is_accessible = False

        nx, ny = my_pos.x -1, my_pos.y 
        npos = Position(nx, ny)

        cand = cls.Candidate()
        cls.cand[6] = cand

        if can_heal(npos):
            cand.is_accessible = True
            cand.position = npos
            cand.building_heal = 0
            cand.bot_heal = 0
            cand.building_hp = 1000000
            cand.bot_hp = 1000000
            cand.is_turret = False

            ti = tile_info[nx][ny]
            cand.entity_type = ti.entity_type
            cand.harvester_adjacent = ti.harvester_adjacent
            cand.is_launcher = cand.entity_type == EntityType.LAUNCHER
            cand.is_gunner = cand.entity_type == EntityType.GUNNER

            if ti.has_building and ti.is_building_ally:
                cand.building_heal = min(
                    4,
                    Constants.MAX_HP_MAP[ti.entity_type] - ti.building_hp
                )
                cand.building_hp = ti.building_hp
                cand.is_turret = ti.has_turret

            if ti.has_bot and ti.is_bot_ally:
                cand.bot_heal = min(
                    4,
                    40 - ti.bot_hp
                )
                cand.bot_hp = ti.bot_hp
        else:
            cand.is_accessible = False

        nx, ny = my_pos.x -1, my_pos.y -1
        npos = Position(nx, ny)

        cand = cls.Candidate()
        cls.cand[7] = cand

        if can_heal(npos):
            cand.is_accessible = True
            cand.position = npos
            cand.building_heal = 0
            cand.bot_heal = 0
            cand.building_hp = 1000000
            cand.bot_hp = 1000000
            cand.is_turret = False

            ti = tile_info[nx][ny]
            cand.entity_type = ti.entity_type
            cand.harvester_adjacent = ti.harvester_adjacent
            cand.is_launcher = cand.entity_type == EntityType.LAUNCHER
            cand.is_gunner = cand.entity_type == EntityType.GUNNER

            if ti.has_building and ti.is_building_ally:
                cand.building_heal = min(
                    4,
                    Constants.MAX_HP_MAP[ti.entity_type] - ti.building_hp
                )
                cand.building_hp = ti.building_hp
                cand.is_turret = ti.has_turret

            if ti.has_bot and ti.is_bot_ally:
                cand.bot_heal = min(
                    4,
                    40 - ti.bot_hp
                )
                cand.bot_hp = ti.bot_hp
        else:
            cand.is_accessible = False

        nx, ny = my_pos.x , my_pos.y 
        npos = Position(nx, ny)

        cand = cls.Candidate()
        cls.cand[8] = cand

        if can_heal(npos):
            cand.is_accessible = True
            cand.position = npos
            cand.building_heal = 0
            cand.bot_heal = 0
            cand.building_hp = 1000000
            cand.bot_hp = 1000000
            cand.is_turret = False

            ti = tile_info[nx][ny]
            cand.entity_type = ti.entity_type
            cand.harvester_adjacent = ti.harvester_adjacent
            cand.is_launcher = cand.entity_type == EntityType.LAUNCHER
            cand.is_gunner = cand.entity_type == EntityType.GUNNER

            if ti.has_building and ti.is_building_ally:
                cand.building_heal = min(
                    4,
                    Constants.MAX_HP_MAP[ti.entity_type] - ti.building_hp
                )
                cand.building_hp = ti.building_hp
                cand.is_turret = ti.has_turret

            cand.bot_heal = min(
                4,
                40 - Globals.ct.get_hp()
            )
            cand.bot_hp = Globals.ct.get_hp() 
        else:
            cand.is_accessible = False


    @classmethod
    def is_better_than(cls, a: HealExecutor.Candidate, b: HealExecutor.Candidate) -> bool:
        if not a.is_accessible: return False
        if not b.is_accessible: return True

        if bool(a.building_heal) != bool(b.building_heal):
            return a.building_heal > b.building_heal

        if a.is_launcher != b.is_launcher:
            return a.is_launcher < b.is_launcher  # prefer non-launchers

        if a.is_gunner != b.is_gunner:
            return a.is_gunner > b.is_gunner

        if a.is_turret and (not b.is_turret): return True
        if (not a.is_turret) and b.is_turret: return False

        if a.harvester_adjacent and (not b.harvester_adjacent): return True
        if (not a.harvester_adjacent) and b.harvester_adjacent: return False

        if a.building_hp != b.building_hp:
            return a.building_hp < b.building_hp

        if a.bot_heal != b.bot_heal:
            return a.bot_heal > b.bot_heal

        if a.bot_hp != b.bot_hp:
            return a.bot_hp < b.bot_hp

        return False


    @classmethod
    def execute_heal_attempt(cls):
        if Globals.ct.get_action_cooldown() != 0:
            return

        cls.precompute()

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

        if not best.is_accessible:
            return

        
        if best.building_heal + best.bot_heal < (1 if best.entity_type == EntityType.ROAD or best.harvester_adjacent else 4):
            return

        if best.is_launcher:
            return

        Debug.line(best.position, Color.LIME)
        

        cls.last_healed_round = Globals.round
        cls.last_healed = best
        
        # Replace the conveyor if it's at low health
        if best.entity_type == EntityType.CONVEYOR:
            if best.building_hp < 10:
                if BuildManager.can_dbuild_conveyor(best.position):
                    BuildManager.dbuild_conveyor(best.position, Globals.ct.get_direction(Globals.ct.get_tile_building_id(best.position)))
                    return
        if best.entity_type == EntityType.ARMOURED_CONVEYOR:
            if best.building_hp < 25:
                if BuildManager.can_dbuild_armoured_conveyor(best.position):
                    BuildManager.dbuild_armoured_conveyor(best.position, Globals.ct.get_direction(Globals.ct.get_tile_building_id(best.position)))
                    return
        if best.entity_type == EntityType.SPLITTER:
            if best.building_hp < 10:
                if BuildManager.can_dbuild_splitter(best.position):
                    BuildManager.dbuild_splitter(best.position, Globals.ct.get_direction(Globals.ct.get_tile_building_id(best.position)))
                    return
        if best.entity_type == EntityType.BRIDGE:
            if best.building_hp < 10:
                if BuildManager.can_dbuild_bridge(best.position):
                    ti = Map.tile_info[best.position.x][best.position.y]
                    BuildManager.dbuild_bridge(best.position, ti.target)
                    return
        
        Globals.ct.heal(best.position)
    
        









