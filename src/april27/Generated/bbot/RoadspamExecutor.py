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

class RoadspamExecutor:
    @classmethod
    def execute_roadspam_attempt(cls):
        if Globals.ct.get_action_cooldown() != 0:
            return
            
        mx, my = Globals.my_pos.x, Globals.my_pos.y
        
        tile_info = Map.tile_info
        

        pos = Position((mx ), (my -1))

        if not BuildManager.can_afford_gunner() and pos.distance_squared(Symmetry.enemy_core_pos) <= 8:
            nti = tile_info[(mx )][(my -1)]
            if nti is not None:
                if (not nti.has_building) or (nti.is_building_ally and nti.entity_type == EntityType.ROAD):
                    if BuildManager.can_dbuild_barrier(pos):
                        BuildManager.dbuild_barrier(pos)
                        return
            
        if BuildManager.can_build_road(pos):
            BuildManager.build_road(pos)
            return

        pos = Position((mx +1), (my -1))

        if not BuildManager.can_afford_gunner() and pos.distance_squared(Symmetry.enemy_core_pos) <= 8:
            nti = tile_info[(mx +1)][(my -1)]
            if nti is not None:
                if (not nti.has_building) or (nti.is_building_ally and nti.entity_type == EntityType.ROAD):
                    if BuildManager.can_dbuild_barrier(pos):
                        BuildManager.dbuild_barrier(pos)
                        return
            
        if BuildManager.can_build_road(pos):
            BuildManager.build_road(pos)
            return

        pos = Position((mx +1), (my ))

        if not BuildManager.can_afford_gunner() and pos.distance_squared(Symmetry.enemy_core_pos) <= 8:
            nti = tile_info[(mx +1)][(my )]
            if nti is not None:
                if (not nti.has_building) or (nti.is_building_ally and nti.entity_type == EntityType.ROAD):
                    if BuildManager.can_dbuild_barrier(pos):
                        BuildManager.dbuild_barrier(pos)
                        return
            
        if BuildManager.can_build_road(pos):
            BuildManager.build_road(pos)
            return

        pos = Position((mx +1), (my +1))

        if not BuildManager.can_afford_gunner() and pos.distance_squared(Symmetry.enemy_core_pos) <= 8:
            nti = tile_info[(mx +1)][(my +1)]
            if nti is not None:
                if (not nti.has_building) or (nti.is_building_ally and nti.entity_type == EntityType.ROAD):
                    if BuildManager.can_dbuild_barrier(pos):
                        BuildManager.dbuild_barrier(pos)
                        return
            
        if BuildManager.can_build_road(pos):
            BuildManager.build_road(pos)
            return

        pos = Position((mx ), (my +1))

        if not BuildManager.can_afford_gunner() and pos.distance_squared(Symmetry.enemy_core_pos) <= 8:
            nti = tile_info[(mx )][(my +1)]
            if nti is not None:
                if (not nti.has_building) or (nti.is_building_ally and nti.entity_type == EntityType.ROAD):
                    if BuildManager.can_dbuild_barrier(pos):
                        BuildManager.dbuild_barrier(pos)
                        return
            
        if BuildManager.can_build_road(pos):
            BuildManager.build_road(pos)
            return

        pos = Position((mx -1), (my +1))

        if not BuildManager.can_afford_gunner() and pos.distance_squared(Symmetry.enemy_core_pos) <= 8:
            nti = tile_info[(mx -1)][(my +1)]
            if nti is not None:
                if (not nti.has_building) or (nti.is_building_ally and nti.entity_type == EntityType.ROAD):
                    if BuildManager.can_dbuild_barrier(pos):
                        BuildManager.dbuild_barrier(pos)
                        return
            
        if BuildManager.can_build_road(pos):
            BuildManager.build_road(pos)
            return

        pos = Position((mx -1), (my ))

        if not BuildManager.can_afford_gunner() and pos.distance_squared(Symmetry.enemy_core_pos) <= 8:
            nti = tile_info[(mx -1)][(my )]
            if nti is not None:
                if (not nti.has_building) or (nti.is_building_ally and nti.entity_type == EntityType.ROAD):
                    if BuildManager.can_dbuild_barrier(pos):
                        BuildManager.dbuild_barrier(pos)
                        return
            
        if BuildManager.can_build_road(pos):
            BuildManager.build_road(pos)
            return

        pos = Position((mx -1), (my -1))

        if not BuildManager.can_afford_gunner() and pos.distance_squared(Symmetry.enemy_core_pos) <= 8:
            nti = tile_info[(mx -1)][(my -1)]
            if nti is not None:
                if (not nti.has_building) or (nti.is_building_ally and nti.entity_type == EntityType.ROAD):
                    if BuildManager.can_dbuild_barrier(pos):
                        BuildManager.dbuild_barrier(pos)
                        return
            
        if BuildManager.can_build_road(pos):
            BuildManager.build_road(pos)
            return
    
        









