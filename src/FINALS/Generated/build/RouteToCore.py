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

class RouteToCore:
    is_active: bool = False
    from_pos: Position
    killed: set[Position] = set()
    prevRoute = []
    backTracking = False
    pathFindingKill: set[int] = set()
    isAttack = False
    turretBeenHereTick = 0

    @classmethod
    def set_pos(cls, pos: Position, fullReset = True):
        if (((pos.x) + 3) * 56 + ((pos.y) + 3)) in DarkForest.core_sink_set:
            cls.is_active = False
            cls.prevRoute.clear()
            cls.backTracking = False
            return

        if fullReset:
            cls.prevRoute.clear()
            cls.backTracking = False
        else:
            cls.prevRoute.append(cls.from_pos)
            cls.backTracking = False
        cls.is_active = True
        cls.from_pos = pos
        cls.turretBeenHereTick = 0


    @classmethod
    def try_build_route(cls):

        bridge_dist = 0
        first_target = None
        from_pos = cls.from_pos
        from_pos_enc = (((from_pos.x) + 3) * 56 + ((from_pos.y) + 3))

        if cls.isAttack:
            if from_pos_enc in Symmetry.enemy_core_gunner_set:
                cls.give_up(True)
                StateBuildTurret.run(from_pos)
                return None

            gun_bridge_dist, gun_first_target = BfsBureau.find_bridge_route(
                from_pos,
                Symmetry.enemy_core_gunner_set,
                avoid_pos=cls.pathFindingKill,
                max_iter=100
            )
            sen_bridge_dist, sen_first_target = BfsBureau.find_bridge_route(
                from_pos,
                Symmetry.enemy_core_sentinel_set,
                avoid_pos=cls.pathFindingKill,
                max_iter=100
            )

            if sen_bridge_dist + 2 <= gun_bridge_dist:
                bridge_dist = sen_bridge_dist
                first_target = sen_first_target
                if from_pos_enc in Symmetry.enemy_core_sentinel_set:
                    cls.give_up(True)
                    StateBuildTurret.run(from_pos)
                    return None
            else:
                bridge_dist = gun_bridge_dist
                first_target = gun_first_target

        else:
            bridge_dist, first_target = BfsBureau.find_bridge_route(
                from_pos,
                Unit.core_pos_set,
                max_iter=0,
                avoid_pos=cls.pathFindingKill
            )
            if first_target is None:
                bridge_dist, first_target = BfsBureau.find_bridge_route(
                    from_pos,
                    DarkForest.core_sink_set,
                    avoid_pos=cls.pathFindingKill
                )

        

        if first_target is None:
            if cls.give_up(True):
                StateMoveTo.run(Explore.get_target())
            return None

        target = Position(*first_target)
        Debug.line(from_pos, target, Color.GREEN)

        # Use GunnerDirectionPicker / SentinelDirectionPicker to decide whether
        # and what to place, mirroring HarvesterAdjacent.get_best_turret_info scoring
        turretPossible = False
        turretDir = None
        turretIsGunner = False

        gi = GunnerDirectionPicker.get_best_info(cls.from_pos)
        gun_ok = BuildManager.can_afford_gunner() \
            and not gi.banned \
            and (gi.has_core or gi.has_enemy_turret or gi.enemy_building_hp > 10)
        gun_score = (gi.enemy_building_hp * 5 + gi.has_enemy_turret * 200 + gi.has_core * 1_000_000) if gun_ok else 0

        si = SentinelDirectionPicker.get_best_info(cls.from_pos)
        sen_ok = BuildManager.can_afford_sentinel() \
            and not si.banned \
            and ((si.enemy_building_hp > 30 and si.enemy_bot_hp > 30)
                 or si.enemy_building_hp > 40
                 or si.enemy_turret_hp > 0)
        sen_score = (si.enemy_building_hp + bool(si.enemy_turret_hp) * 100) if sen_ok else 0

        if gun_ok or sen_ok:
            turretPossible = True
            if gun_score >= sen_score:
                turretDir = gi.direction
                turretIsGunner = True
            else:
                turretDir = si.direction
                turretIsGunner = False

        if turretPossible:
            cls.turretBeenHereTick += 1
        else:
            cls.turretBeenHereTick = 0
        if cls.turretBeenHereTick > 20:
            turretPossible = False

        if turretPossible and (
            (turretIsGunner and BuildManager.can_dbuild_gunner(cls.from_pos)) or
            (not turretIsGunner and BuildManager.can_dbuild_sentinel(cls.from_pos))
        ):
            x, y = cls.from_pos
            ti = Map.tile_info[x][y]
            if ti.has_building and ti.entity_type not in (EntityType.GUNNER, EntityType.SENTINEL):
                if turretIsGunner:
                    BuildManager.dbuild_gunner(cls.from_pos, turretDir)
                else:
                    BuildManager.dbuild_sentinel(cls.from_pos, turretDir)
        elif cls.from_pos.distance_squared(target) == 1:
            ti = Map.tile_info[cls.from_pos.x][cls.from_pos.y]
            if not ti.has_building or not ti.is_building_ally or target != ti.target:
                if BuildManager.can_dbuild_conveyor(from_pos):
                    if BuildManager.should_build_armoured(from_pos) and BuildManager.can_dbuild_armoured_conveyor(from_pos):
                        BuildManager.dbuild_armoured_conveyor(from_pos, from_pos.direction_to(target))
                    else:
                        BuildManager.dbuild_conveyor(from_pos, from_pos.direction_to(target))
                    cls.set_pos(target, False)
                    return
        elif BuildManager.can_dbuild_bridge(cls.from_pos):
            BuildManager.dbuild_bridge(cls.from_pos, target)
            cls.set_pos(target, False)
            return


    @classmethod
    def move_to_next(cls):
        Pathfinder.move_to(cls.from_pos, ban_target_pos=True)


    @classmethod
    def should_give_up(cls):
        x, y = cls.from_pos
        ti = Map.tile_info[x][y]
        if ti is None:
            return False
        if not cls.backTracking and Pathfinder.given_up:
            return True
        if len(cls.prevRoute) != 0:
            px, py = cls.prevRoute[-1]
            if DarkForest.flow[(((px) + 3) * 56 + ((py) + 3))] == 0:
                return True
        if ti.has_building:
            if not ti.is_building_ally:
                return True
            if not cls.backTracking:
                if ti.entity_type in Constants.TRANSPORTERS_SET:
                    if ti.target is not None:
                        tx, ty = ti.target.x, ti.target.y
                        ti2 = Map.tile_info[tx][ty]
                        if ti2 is not None and ti2.entity_type == EntityType.HARVESTER:
                            return False  # it is a shield
                    cls.is_active = False
                    cls.prevRoute.clear()
                    return True
                if ti.entity_type != EntityType.ROAD and ti.entity_type not in Constants.TURRET_SET:
                    return True
        return False


    @classmethod
    def give_up(cls, hard = False):
        from_pos = cls.from_pos
        enc = (((from_pos.x) + 3) * 56 + ((from_pos.y) + 3))
        if len(cls.prevRoute) != 0:
            px, py = cls.prevRoute[-1]
            if DarkForest.flow[(((px) + 3) * 56 + ((py) + 3))] == 0:
                hard = True
        if hard or len(cls.prevRoute) == 0 or DarkForest.node_kind[enc] in \
                (3, 1):
            cls.is_active = False
            cls.killed.add(from_pos)
            if Pathfinder.given_up:
                cls.pathFindingKill.add(enc)
            cls.backTracking = False
            return True
        else:
            cls.killed.add(from_pos)
            if Pathfinder.given_up:
                cls.pathFindingKill.add(enc)
            cls.from_pos = cls.prevRoute.pop()
            cls.backTracking = True
            return False


    @classmethod
    def do_routing(cls):

        if cls.should_give_up():
            if cls.give_up():
                StateMoveTo.run(Explore.get_target())
            return

        dsq = Globals.my_pos.distance_squared(cls.from_pos)
        if Globals.ct.get_action_cooldown() == 0 and dsq <= 2:
            cls.try_build_route()
            cls.move_to_next()
        else:
            cls.move_to_next()