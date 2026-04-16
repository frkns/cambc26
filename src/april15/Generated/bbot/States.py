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
    def run(cls, pos):
        if Globals.my_pos != pos:
            Pathfinder.move_to(pos)

        if Globals.my_pos != pos:
            return

        if Globals.ct.can_fire(pos) and Attacker.should_fire(pos):
            Globals.ct.fire(pos)


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


class StateMoveTo:
    @classmethod
    def run(cls, pos, tag='_'):
        Pathfinder.move_to(pos)


class StateBuildSentinel:
    @classmethod
    def run(cls, pos, banned_dir: Direction | None = None):
        Pathfinder.move_to(pos, ban_target_pos=True)

        if BuildManager.can_dbuild_sentinel(pos):
            dir: Direction = SentinelDirectionPicker.get_best_direction(pos)
            BuildManager.dbuild_sentinel(pos, dir)

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

class StateBuildShield:
    @classmethod
    def run(cls, pos):
        Pathfinder.move_to(pos, ban_target_pos=True)
        
        target_dir = None
        
        tile_info = Map.tile_info
        ally_harvester = False
        
        ti = tile_info[pos.x + 0][pos.y + -1]
        if ti is not None:
            if ti.has_building and ti.entity_type == EntityType.HARVESTER:
                if not ally_harvester or ti.is_building_ally:
                    target_dir = Direction.NORTH
                    Debug.line(pos, pos.add(Direction.NORTH), Color.GREEN)
                    if ti.is_building_ally:
                        ally_harvester = True
        ti = tile_info[pos.x + 1][pos.y + 0]
        if ti is not None:
            if ti.has_building and ti.entity_type == EntityType.HARVESTER:
                if not ally_harvester or ti.is_building_ally:
                    target_dir = Direction.EAST
                    Debug.line(pos, pos.add(Direction.EAST), Color.GREEN)
                    if ti.is_building_ally:
                        ally_harvester = True
        ti = tile_info[pos.x + 0][pos.y + 1]
        if ti is not None:
            if ti.has_building and ti.entity_type == EntityType.HARVESTER:
                if not ally_harvester or ti.is_building_ally:
                    target_dir = Direction.SOUTH
                    Debug.line(pos, pos.add(Direction.SOUTH), Color.GREEN)
                    if ti.is_building_ally:
                        ally_harvester = True
        ti = tile_info[pos.x + -1][pos.y + 0]
        if ti is not None:
            if ti.has_building and ti.entity_type == EntityType.HARVESTER:
                if not ally_harvester or ti.is_building_ally:
                    target_dir = Direction.WEST
                    Debug.line(pos, pos.add(Direction.WEST), Color.GREEN)
                    if ti.is_building_ally:
                        ally_harvester = True


        if target_dir is not None:
            if ally_harvester:
                if BuildManager.can_dbuild_conveyor(pos):
                    BuildManager.dbuild_conveyor(pos, target_dir)
            else:
                if BuildManager.can_dbuild_barrier(pos):
                    BuildManager.dbuild_barrier(pos)
        else:
            if BuildManager.can_dbuild_road(pos):
                BuildManager.dbuild_road(pos)
            