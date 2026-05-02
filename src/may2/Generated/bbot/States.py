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

class StateBuildHarvester:
    @classmethod
    def run(cls, pos):
        OreExecutive.go_build_harvester(pos)

class StateBuildHarvesterAx:
    @classmethod
    def run(cls, pos):
        OreExecutive.go_build_ax_harvester(pos)


class StateAttack:
    @classmethod
    def run(cls, pos, tag='_'):
        
        if Globals.my_pos != pos:
            Pathfinder.move_to(pos)

        if Globals.my_pos != pos:
            return

        if Globals.ct.can_fire(pos) and Attacker.should_fire(pos):
            Globals.ct.fire(pos)


class StateReroute:  # for misrouted ally transporters
    # is_active: bool = False
    # pos: Position = None

    @classmethod
    def run(cls, pos):
        # cls.pos = pos

        # Debug.line(pos, Color.ORANGE)
        if Globals.my_pos.distance_squared(pos) > 2:
            Pathfinder.move_to(pos)

        if Globals.ct.get_action_cooldown() == 0 and Globals.ct.can_destroy(pos):
            BuildManager.destroy(pos)
            if pos.distance_squared(Unit.core_pos) < pos.distance_squared(Symmetry.enemy_core_pos):
                RouteToCore.set_pos(pos)
                
            if BuildManager.can_build_road(pos):
                BuildManager.build_road(pos)


class StateRoute:
    @classmethod
    def run(cls):
        RouteToCore.do_routing()




class StateFoundryBuild:
    @classmethod
    def run(cls, pos):
        FoundryBuild.build_foundry(pos)

class StateBreachBuild:
    @classmethod
    def run(cls, pos):
        BreachBuild.build_breach(pos)

class StateRouteFoundry:
    @classmethod
    def run(cls):
        RouteToFoundry.do_routing()
        
class StateRouteBreach:
    @classmethod
    def run(cls):
        RouteToBreach.do_routing()

class StateRouteFoundryInput:
    @classmethod
    def run(cls):
        RouteToFoundryInput.do_routing()


class StateMoveTo:
    @classmethod
    def run(cls, pos, tag='_'):
        Pathfinder.move_to(pos)

class StateRush:
    @classmethod
    def run(cls, targ: tuple[Position, str]):
        pos = targ[0]
        type = targ[1]
        if type == 'M': #move
            Pathfinder.move_to(pos)
        elif type == 'B': # build
            OreExecutive.go_build_harvester(pos,True)
        elif type == 'R': #route
            Pathfinder.move_to(pos)
            if Pathfinder.given_up:
                RushTargeter.killed.add(pos)
                return
            if Globals.my_pos.distance_squared(pos) <= 4: #sufficiently close
                cand: OrePositionPicker.Candidate = OrePositionPicker.pick_best_candidate(pos)
                if cand is not None and cand.ti.entity_type not in Constants.TRANSPORTERS_SET:
                    RouteToBreach.set_pos(cand.position)
                else:
                    RushTargeter.killed.add(pos)

class StateBuildTurret:
# ---===
    @classmethod
    def gunner_can_hit_core(cls, gunner_pos: MapLocation) -> Direction | None:
        direction = gunner_pos.direction_to(Symmetry.enemy_core_pos)
        dx, dy = direction.delta()    # unit step for this direction

        x, y = gunner_pos.x + dx, gunner_pos.y + dy      # start one step ahead


        while x >= 0 and y >= 0 and x < Map.W and y < Map.H:
            if (x - gunner_pos.x) ** 2 + (y - gunner_pos.y) ** 2 > 13:
                break                                         # out of range — stop ray

            ti = Map.tile_info[x][y]
            if ti == None:
                x += dx
                y += dy
                continue
            if ti.env == Environment.WALL:
                break
            if ti.has_building and ti.is_building_ally and ti.entity_type != EntityType.ROAD:
                break

            if (((x) + 3) * 56 + ((y) + 3)) in Symmetry.enemy_core_pos_set:
                return direction

            x += dx
            y += dy

        return None
# ===---

    @classmethod
    def run(cls, pos, should_build_sentinel=True, gdir=None):
        if Symmetry.is_sym_known and gdir is None:
            gdir = cls.gunner_can_hit_core(pos)
            


        if Globals.my_pos.distance_squared(pos) <= 2:
            if (gdir is not None) and BuildManager.can_smartbuild_gunner(pos):
                BuildManager.smartbuild_gunner(pos, gdir)
            elif should_build_sentinel and BuildManager.can_smartbuild_sentinel(pos):
                
                dir: Direction = SentinelDirectionPicker.get_best_direction(pos)
                
                BuildManager.smartbuild_sentinel(pos, dir)
            elif BuildManager.can_build_road(pos):
                BuildManager.build_road(pos)


        if Globals.ct.get_move_cooldown() == 0:
            Pathfinder.move_to(pos, ban_target_pos=False)

        if Globals.my_pos.distance_squared(pos) <= 2:
            if (gdir is not None) and BuildManager.can_smartbuild_gunner(pos):
                BuildManager.smartbuild_gunner(pos, gdir)
            elif should_build_sentinel and BuildManager.can_smartbuild_sentinel(pos):
                
                dir: Direction = SentinelDirectionPicker.get_best_direction(pos)
                
                BuildManager.smartbuild_sentinel(pos, dir)
            elif BuildManager.can_build_road(pos):
                BuildManager.build_road(pos)



class StateBuildTurretWrapper:
    @classmethod
    def run(cls, pos, is_gunner, info: AdjacentInfo):
        gdir = info.gunner_dir_info.direction if is_gunner else None
        StateBuildTurret.run(pos, gdir=gdir)


class StateBuildAdvancedShield:
    # build barrier shields on enemy harvesters (do not build conveyor shields - interacts badly)

    @classmethod
    def run(cls, pos, info: AdjacentInfo):
        x, y = pos.x, pos.y
        tile_info = Map.tile_info
        GUNNER = EntityType.GUNNER

        ally_gunners_adjacent = 0

        if tile_info[x ][y -1].entity_type == GUNNER:
            ally_gunners_adjacent += 1
        if tile_info[x +1][y -1].entity_type == GUNNER:
            ally_gunners_adjacent += 1
        if tile_info[x +1][y ].entity_type == GUNNER:
            ally_gunners_adjacent += 1
        if tile_info[x +1][y +1].entity_type == GUNNER:
            ally_gunners_adjacent += 1
        if tile_info[x ][y +1].entity_type == GUNNER:
            ally_gunners_adjacent += 1
        if tile_info[x -1][y +1].entity_type == GUNNER:
            ally_gunners_adjacent += 1
        if tile_info[x -1][y ].entity_type == GUNNER:
            ally_gunners_adjacent += 1
        if tile_info[x -1][y -1].entity_type == GUNNER:
            ally_gunners_adjacent += 1

        can_barrier = ally_gunners_adjacent == 0
        dir_to_h = pos.direction_to(info.hpos)



        if Globals.my_pos.distance_squared(pos) <= 2:
            if can_barrier and BuildManager.can_smartbuild_barrier(pos):
                BuildManager.smartbuild_barrier(pos)
            # elif BuildManager.can_smartbuild_armoured_conveyor(pos):
            #     BuildManager.smartbuild_armoured_conveyor(pos, dir_to_h)
            # elif BuildManager.can_smartbuild_conveyor(pos):
            #     BuildManager.smartbuild_conveyor(pos, dir_to_h)


        if Globals.ct.get_move_cooldown() == 0:
            Pathfinder.move_to(pos, ban_target_pos=False)

        if Globals.my_pos.distance_squared(pos) <= 2:
            if can_barrier and BuildManager.can_smartbuild_barrier(pos):
                BuildManager.smartbuild_barrier(pos)
            # elif BuildManager.can_smartbuild_armoured_conveyor(pos):
            #     BuildManager.smartbuild_armoured_conveyor(pos, dir_to_h)
            # elif BuildManager.can_smartbuild_conveyor(pos):
            #     BuildManager.smartbuild_conveyor(pos, dir_to_h)




class StateBuildGunner:
    @classmethod
    def run(cls, pos, banned_dir: Direction | None):
        Pathfinder.move_to(pos, ban_target_pos=True)

        if BuildManager.can_dbuild_gunner(pos):
            dir: Direction = GunnerDirectionPicker.get_best_direction(pos)
            
            BuildManager.dbuild_gunner(pos, dir)

class StateBuildLauncher:
    @classmethod
    def run(cls, pos):
        Pathfinder.move_to(pos, ban_target_pos=True)
        
        if BuildManager.can_dbuild_launcher(pos):            
            BuildManager.dbuild_launcher(pos)
            return

class StateNoOp:
    @staticmethod
    def run(*a, **kw):
        pass

class StateBuildShield:
    @classmethod
    def run(cls, pos):
        if Globals.my_pos.distance_squared(pos) > 0:
            Pathfinder.move_to(pos, ban_target_pos=True)
        
        target_dir = None
        
        tile_info = Map.tile_info
        found_ally_harvester = False
        
        ti = tile_info[pos.x + 0][pos.y + -1]
        if ti is not None:
            if ti.has_building and ti.entity_type == EntityType.HARVESTER:
                if not found_ally_harvester or ti.is_building_ally:
                    target_dir = Direction.NORTH
                    Debug.line(pos, pos.add(Direction.NORTH), Color.GREEN)
                    if ti.is_building_ally:
                        found_ally_harvester = True
        ti = tile_info[pos.x + 1][pos.y + 0]
        if ti is not None:
            if ti.has_building and ti.entity_type == EntityType.HARVESTER:
                if not found_ally_harvester or ti.is_building_ally:
                    target_dir = Direction.EAST
                    Debug.line(pos, pos.add(Direction.EAST), Color.GREEN)
                    if ti.is_building_ally:
                        found_ally_harvester = True
        ti = tile_info[pos.x + 0][pos.y + 1]
        if ti is not None:
            if ti.has_building and ti.entity_type == EntityType.HARVESTER:
                if not found_ally_harvester or ti.is_building_ally:
                    target_dir = Direction.SOUTH
                    Debug.line(pos, pos.add(Direction.SOUTH), Color.GREEN)
                    if ti.is_building_ally:
                        found_ally_harvester = True
        ti = tile_info[pos.x + -1][pos.y + 0]
        if ti is not None:
            if ti.has_building and ti.entity_type == EntityType.HARVESTER:
                if not found_ally_harvester or ti.is_building_ally:
                    target_dir = Direction.WEST
                    Debug.line(pos, pos.add(Direction.WEST), Color.GREEN)
                    if ti.is_building_ally:
                        found_ally_harvester = True
        



        if pos != Globals.my_pos:
            if target_dir is not None:
                if found_ally_harvester:
                    if (pos.distance_squared(Symmetry.enemy_core_pos) < pos.distance_squared(Unit.core_pos)) and BuildManager.can_smartbuild_barrier(pos):
                        BuildManager.smartbuild_barrier(pos)
                    elif (
            Map.num_enemy_buildings > 0
        ) and BuildManager.can_dbuild_armoured_conveyor(pos):
                        BuildManager.dbuild_armoured_conveyor(pos, target_dir)
                    elif BuildManager.can_dbuild_conveyor(pos):
                        BuildManager.dbuild_conveyor(pos, target_dir)
                else:
                    if BuildManager.can_build_road(pos):
                        BuildManager.build_road(pos)
            else:
                if BuildManager.can_build_road(pos):
                    BuildManager.build_road(pos)
        else:
            if target_dir is not None:
                if found_ally_harvester:
                    if (
            Map.num_enemy_buildings > 0
        ) and BuildManager.can_mbuild_armoured_conveyor():
                        BuildManager.dbuild_armoured_conveyor(pos, target_dir)
                    elif BuildManager.can_mbuild_conveyor():
                        BuildManager.dbuild_conveyor(pos, target_dir)  # mbuild check but dbuild
                else:
                    if BuildManager.can_mbuild_road():
                        BuildManager.dbuild_road(pos)
            else:
                if BuildManager.can_mbuild_road():
                    BuildManager.dbuild_road(pos)
            

class StateDestroy:
    @classmethod
    def run(cls, pos):
        ct = Globals.ct

        if ct.can_destroy(pos):
            BuildManager.destroy(pos)
        else:
            Pathfinder.move_to(pos)

        if ct.can_destroy(pos):
            BuildManager.destroy(pos)
    


