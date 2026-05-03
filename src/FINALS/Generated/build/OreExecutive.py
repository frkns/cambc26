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

class OreExecutive:
    state: dict[Position, int] = defaultdict(int)
    ti_queue: list[tuple[int, Position]] = []
    ax_queue: list[tuple[int, Position]] = []
    # nearby_ti_queue removed (reverted c187f820)

    hard_building_set: set[EntityType] = {EntityType.HARVESTER, EntityType.FOUNDRY, EntityType.SENTINEL, EntityType.GUNNER}

    @classmethod
    def fill(cls):
        for pos, x, y, idx, ti in Map.proc_nearby_tiles:
            # not using Map.harvester_set..?
            
            if ti.entity_type == EntityType.FOUNDRY:
                if idx not in RouteToFoundry.planned_foundry_positions:
                    FoundryBuild.register_foundry(pos)
                continue

            if cls.state[pos] == 2:
                continue

            if cls.state[pos] == 6:
                if BfsBureau.bfs20_dist[idx] >= 1000000: #you can work with this
                    continue
            env = ti.env

            if ti.entity_type in cls.hard_building_set:
                continue


            if ti.has_building and not ti.is_building_ally:
                continue


            if env == Environment.ORE_TITANIUM or env == Environment.ORE_AXIONITE:



                if env == Environment.ORE_TITANIUM:
                    if cls.state[pos] != 1:  # intended: can potentially requeue
                        heapq.heappush(cls.ti_queue, (int(5 * math.sqrt(pos.distance_squared(Unit.core_pos)) + BfsBureau.bfs20_dist[idx]), pos))
                        cls.state[pos] = 1

                if env == Environment.ORE_AXIONITE:
                    if cls.state[pos] != 4:  # intended: can potentially requeue
                        heapq.heappush(cls.ax_queue, (int(5 * math.sqrt(pos.distance_squared(Unit.core_pos)) + BfsBureau.bfs20_dist[idx]), pos))
                        cls.state[pos] = 4


    @classmethod
    def get_titanium_target(cls) -> Position | None:
        ret = None
        while cls.ti_queue:
            dist, pos = cls.ti_queue[0]

            if cls.state[pos] == 2:
                heapq.heappop(cls.ti_queue)
                continue
            if cls.state[pos] == 6:
                if BfsBureau.bfs20_dist[(((pos.x) + 3) * 56 + ((pos.y) + 3))] >= 1000000: #you can work with this
                    heapq.heappop(cls.ti_queue)
                    continue

            ti = Map.tile_info[pos.x][pos.y]

            if ti.entity_type in cls.hard_building_set:
                heapq.heappop(cls.ti_queue)
                cls.state[pos] = 3
                continue
            if ti.entity_type == EntityType.FOUNDRY:
                heapq.heappop(cls.ti_queue)
                cls.state[pos] = 3
                continue

            if ti.has_building and not ti.is_building_ally:
                heapq.heappop(cls.ti_queue)
                cls.state[pos] = 3
                continue
            
            if not VisionTracker.me_is_canonical_ally(pos):
                heapq.heappop(cls.ti_queue)
                cls.state[pos] = 5
                continue

            if not ti.has_bot and MarketMaker.should_build_harvester(pos):  # fixed: was should_build_ax_harvester
                ret = pos
                break
            else:
                break

        if ret is None:
            return None


        # Don't build harvesters next to enemy buildings (because they can destroy them and build a turret)
        ti: TileInfo = Map.tile_info[ret.x + 0][ret.y + -1]
        if ti is not None:
            if ti.has_turret and not ti.is_building_ally:
                cls.state[ret] = 2  # don't want to keep trying to build here
                return None


        # Don't build harvesters next to enemy buildings (because they can destroy them and build a turret)
        ti: TileInfo = Map.tile_info[ret.x + 1][ret.y + 0]
        if ti is not None:
            if ti.has_turret and not ti.is_building_ally:
                cls.state[ret] = 2  # don't want to keep trying to build here
                return None


        # Don't build harvesters next to enemy buildings (because they can destroy them and build a turret)
        ti: TileInfo = Map.tile_info[ret.x + 0][ret.y + 1]
        if ti is not None:
            if ti.has_turret and not ti.is_building_ally:
                cls.state[ret] = 2  # don't want to keep trying to build here
                return None


        # Don't build harvesters next to enemy buildings (because they can destroy them and build a turret)
        ti: TileInfo = Map.tile_info[ret.x + -1][ret.y + 0]
        if ti is not None:
            if ti.has_turret and not ti.is_building_ally:
                cls.state[ret] = 2  # don't want to keep trying to build here
                return None


        return ret

    @classmethod
    def get_axionite_target(cls) -> Position | None:
        if Globals.round < Constants.AXIONITE_START:
            return None  # don't want to waste resources on axionite early on

        ret = None
        while cls.ax_queue:
            dist, pos = cls.ax_queue[0]

            if cls.state[pos] == 2:
                heapq.heappop(cls.ax_queue)
                continue
            if cls.state[pos] == 6:
                if BfsBureau.bfs20_dist[(((pos.x) + 3) * 56 + ((pos.y) + 3))] >= 1000000: #you can work with this
                    heapq.heappop(cls.ax_queue)
                    continue

            ti = Map.tile_info[pos.x][pos.y]

            if ti.entity_type in cls.hard_building_set:
                heapq.heappop(cls.ax_queue)
                cls.state[pos] = 3
                continue

            if ti.has_building and not ti.is_building_ally:
                heapq.heappop(cls.ax_queue)
                cls.state[pos] = 3
                continue

            if ti.is_pointed_to:
                cls.state[pos] = 3  # for ax bug
            
            if not VisionTracker.me_is_canonical_ally(pos):
                heapq.heappop(cls.ax_queue)
                cls.state[pos] = 5
                continue

            if not ti.has_bot and MarketMaker.should_build_ax_harvester(pos):
                ret = pos
                break
            else:
                break

        return ret # can be None


    @classmethod
    def go_build_harvester(cls, pos, isAttack = False):
        Pathfinder.move_to(pos, ban_target_pos=True, orbit=(not BuildManager.can_afford_harvester()))

        if Pathfinder.given_up:
            Debug.line(pos, Color.RED)
            Debug.diamond(Color.RED)
            cls.state[pos] = 6
            return

        if BuildManager.can_dbuild_harvester(pos):
            Debug.line(pos, Color.YELLOW)
            BuildManager.dbuild_harvester(pos)

            # Check if already routed naturally
            for d in Constants.CARDINAL_DIRECTIONS:
                newPos = pos.add(d)
                ti = Map.tile_info[newPos.x][newPos.y]
                if ti is None:
                    continue
                encoded = (((newPos.x) + 3) * 56 + ((newPos.y) + 3))
                if ti.has_building and ti.is_building_ally and ti.entity_type in Constants.TRANSPORTERS_SET and not ti.is_shield and encoded in DarkForest.core_sink_set:
                    break  # already connected, skip
            else:
                target_pos = Unit.core_pos
                cand: OrePositionPicker.Candidate = OrePositionPicker.pick_best_candidate(pos, target_pos=target_pos)
                if cand is not None:
                    RouteToCore.set_pos(cand.position)
                    RouteToCore.isAttack = isAttack

    @classmethod
    def go_build_ax_harvester(cls, pos):
        Pathfinder.move_to(pos, ban_target_pos=True)

        if Pathfinder.given_up:
            Debug.line(pos, Color.RED)
            Debug.diamond(Color.RED)
            cls.state[pos] = 6
            return

        cand: OrePositionPicker.Candidate = OrePositionPicker.pick_best_candidate(pos, forAx=True)
        if cand == None:
            Debug.line(pos, Color.RED)
            Debug.diamond(Color.RED)
            cls.state[pos] = 2
            return
        ti = Map.tile_info[cand.position.x][cand.position.y]
        if ti.entity_type in Constants.TRANSPORTERS_SET and not ti.is_shield:
            cls.state[pos] = 2
            Debug.line(pos, Color.RED)
            Debug.diamond(Color.RED)
            return

        # route to a new foundry leaf
        RouteToFoundry.from_pos = pos

        RouteToFoundry.try_claim_target()
        foundry_enc = RouteToFoundry._foundry_target
        if foundry_enc is None or not RouteToFoundry.axionite_can_reach_foundry(cand.position, foundry_enc):
            cls.state[pos] = 2
            Debug.line(pos, Color.RED)
            Debug.diamond(Color.RED)
            RouteToFoundry.give_up(True)
            return
        if BuildManager.can_dbuild_harvester(pos):
            Debug.line(pos, Color.YELLOW)
            BuildManager.dbuild_harvester(pos)
            # Check if already routed naturally
            for d in Constants.CARDINAL_DIRECTIONS:
                newPos = pos.add(d)
                ti = Map.tile_info[newPos.x][newPos.y]
                if ti is None:
                    continue
                encoded = (((newPos.x) + 3) * 56 + ((newPos.y) + 3))
                if ti.has_building and ti.is_building_ally and ti.entity_type in Constants.TRANSPORTERS_SET and not ti.is_shield:
                    if DarkForest.ax_tagged[encoded]:
                        break  # already connected, skip
                    elif encoded not in DarkForest.refined_ax_line:
                        RouteToFoundry.give_up(True)
                        RouteToFoundry._foundry_target = encoded # to trigger foundry build
                        return
            else:
                RouteToFoundry.set_pos(cand.position)
                return
            RouteToFoundry.give_up(True)
        else:
            RouteToFoundry.give_up(True)