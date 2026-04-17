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

    @classmethod
    def set_pos(cls, pos: Position, fullReset = True):
        if (((pos.x) + 3) * 56 + ((pos.y) + 3)) in DarkForest.core_sink_set:  # was sink_set
            cls.is_active = False
            cls.prevRoute.clear()
            cls.backTracking = False
            return

        if fullReset:
            cls.prevRoute.clear()
            cls.backTracking = False 
        else:
            cls.prevRoute.append(cls.from_pos)
            cls.backTracking = False # Added here to clear backtracking once we resume forward progress
        cls.is_active = True
        cls.from_pos = pos


    @classmethod
    def try_build_route(cls):
        assert cls.is_active

        # short search to core in case it's close
        bridge_dist, first_target = BfsBureau.find_bridge_route(
            cls.from_pos,
            Unit.core_pos_set,
            max_iter=0,
            avoid_pos = cls.pathFindingKill
        )
        # otherwise allow all sinks
        if first_target is None:
            bridge_dist, first_target = BfsBureau.find_bridge_route(
                cls.from_pos,
                DarkForest.core_sink_set,  # was sink_set
                avoid_pos = cls.pathFindingKill
            )

        

        if first_target is None:
            Debug.tee("first_target is None: giving up")
            if cls.give_up():
                StateMoveTo.run(Explore.get_target()) # new
            return

        target = Position(*first_target)
        Debug.diline(cls.from_pos, target, Color.GREEN)

        if cls.from_pos.distance_squared(target) == 1:
            if BuildManager.can_dbuild_conveyor(cls.from_pos):
                if BuildManager.can_dbuild_armoured_conveyor(cls.from_pos):
                    BuildManager.dbuild_armoured_conveyor(cls.from_pos, cls.from_pos.direction_to(target))
                else:
                    BuildManager.dbuild_conveyor(cls.from_pos, cls.from_pos.direction_to(target))
                cls.set_pos(target,False)
        elif BuildManager.can_dbuild_bridge(cls.from_pos):
            BuildManager.dbuild_bridge(cls.from_pos, target)
            cls.set_pos(target,False)

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

        if ti.has_building:
            if not ti.is_building_ally:
                return True
            if not cls.backTracking:
                if ti.entity_type in Constants.TRANSPORTERS_SET:
                    # Another bot already built here — they've taken over, bow out cleanly
                    cls.is_active = False
                    cls.prevRoute.clear()
                    return True
                if ti.entity_type != EntityType.ROAD:
                    return True
        return False


    @classmethod
    def give_up(cls):
        from_pos = cls.from_pos
        enc = (((from_pos.x) + 3) * 56 + ((from_pos.y) + 3))
        if len(cls.prevRoute) == 0 or DarkForest.node_kind[enc] in \
                (3, 1):
            cls.is_active = False
            cls.killed.add(from_pos)
            Debug.diamond(Color.PURPLE)
            print("RouteToCore: giving up, no previous route to backtrack to or finished")
            if Pathfinder.given_up:
                cls.pathFindingKill.add(enc)
            cls.backTracking = False
            return True
        else:
            cls.killed.add(from_pos)
            if Pathfinder.given_up:
                cls.pathFindingKill.add(enc)
            from_pos = cls.prevRoute.pop()
            print("RouteToCore: backtracking to", cls.from_pos)
            cls.backTracking = True
            return False


    @classmethod
    def do_routing(cls):
        print("RouteToCore: doing routing from", cls.from_pos)
        if cls.should_give_up():
            if cls.give_up():
                StateMoveTo.run(Explore.get_target()) # new
            return

        dsq = Globals.my_pos.distance_squared(cls.from_pos)
        if Globals.ct.get_action_cooldown() == 0 \
                and (dsq == 1 or dsq == 2):
            cls.try_build_route()
            cls.move_to_next()
            # if Globals.ct.can_build_road(cls.from_pos):
            #     Globals.ct.build_road(cls.from_pos)
        else:
            cls.move_to_next()