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

class Building:
    __slots__ = ('team', 'entityType')
    def __init__(self, ct: Controller, id: int):
        self.team = ct.get_team(id)
        self.entityType = ct.get_entity_type(id)

class Launcher(Unit):
    @classmethod
    def init(cls):
        Unit.init()
        DarkForest.init()
        cls.ROUTING_SET.add(EntityType.HARVESTER)
        cls.ROUTING_SET.add(EntityType.FOUNDRY)
        cls.ROUTING_SET.add(EntityType.CORE)

    @classmethod
    def start_turn(cls):
        Unit.start_turn()

    
    ROUTING_SET = Constants.TRANSPORTERS_SET

    @classmethod
    def run_turn(cls):
        ct = Globals.ct
        my_team = ct.get_team()
        my_pos = ct.get_position()
        tiles = ct.get_nearby_tiles()

        BUILDER_BOT = EntityType.BUILDER_BOT
        nearby_enemy_bot = None
        nearby_ally_bot = None
        enemy_buildings = 0
        close_enemy_bots = 0
        get_etype = ct.get_entity_type
        get_team = ct.get_team
        for unit in ct.get_nearby_units(2):
            if get_etype(unit) == BUILDER_BOT:
                if get_team(unit) != my_team:
                    nearby_enemy_bot = ct.get_position(unit)
                else:
                    nearby_ally_bot = ct.get_position(unit)
        
        for building in ct.get_nearby_buildings(2):
            if get_team(building) != my_team:
                enemy_buildings += 1
                
        if nearby_ally_bot is not None:
            print("Nearby Ally Bot:", nearby_ally_bot)
            for unit in ct.get_nearby_units(8):
                if get_etype(unit) == BUILDER_BOT:
                    if get_team(unit) != my_team:
                        if ct.get_position(unit).distance_squared(nearby_ally_bot) <= 2:
                            close_enemy_bots += 1
                
        if nearby_enemy_bot is not None:
            print("Oh no! Nearby Enemy Bot:", nearby_enemy_bot)
            print("Time Elapsed:", ct.get_cpu_time_elapsed())

            ROUTING = cls.ROUTING_SET
            LAUNCHER = EntityType.LAUNCHER
            DIRECTIONS = Constants.DIRECTIONS
            map_w = ct.get_map_width()
            map_h = ct.get_map_height()

            building_cache = {}
            get_bid = ct.get_tile_building_id
            _bc_get = building_cache.get
            scores = []
            _sa = scores.append

            for tile in tiles:
                building_id = get_bid(tile)
                if building_id is not None:
                    building_cache[tile] = Building(ct, building_id)

                if not ct.is_tile_passable(tile):
                    continue

                building = _bc_get(tile)
                if building is not None and building.team == my_team and building.entityType in ROUTING:
                    continue

                score = my_pos.distance_squared(tile)

                for d in DIRECTIONS:
                    new_loc = tile.add(d)
                    nx, ny = new_loc.x, new_loc.y
                    if not (0 <= nx < map_w and 0 <= ny < map_h) or not ct.is_in_vision(new_loc):
                        continue
                    adj_building = _bc_get(new_loc)
                    if adj_building is None:
                        continue
                    if adj_building.team != my_team and adj_building.entityType == LAUNCHER:
                        score -= 50
                    elif adj_building.team == my_team and adj_building.entityType in ROUTING:
                        score -= 50

                _sa((score, tile))
                if ct.get_cpu_time_elapsed() > 1920:
                    break

            best_pos = max(scores, key=lambda x: x[0])[1] if scores else None

            print("Plausible place to throw:", best_pos)

            if nearby_enemy_bot is not None and best_pos is not None and ct.can_launch(nearby_enemy_bot, best_pos):
                ct.launch(nearby_enemy_bot, best_pos)
        elif nearby_ally_bot is not None and enemy_buildings > 1 and close_enemy_bots > 0:
            print("No nearby enemies, but nearby ally bot:", nearby_ally_bot)

            ROUTING = cls.ROUTING_SET
            LAUNCHER = EntityType.LAUNCHER
            DIRECTIONS = Constants.DIRECTIONS
            map_w = ct.get_map_width()
            map_h = ct.get_map_height()

            building_cache = {}
            get_bid = ct.get_tile_building_id
            _bc_get = building_cache.get
            scores = []
            _sa = scores.append
            
            enemy_builder_bots = set()
            enemy_bots_2 = set()
            enemy_bots_8 = set()
            
            for unit in ct.get_nearby_units():
                if ct.get_entity_type(unit) == BUILDER_BOT and ct.get_team(unit) != my_team:
                    upos = ct.get_position(unit)
                    enemy_builder_bots.add(upos)
                    ux, uy = upos.x, upos.y
                    enemy_bots_2.add(Position(ux + -1, uy + -1))
                    enemy_bots_2.add(Position(ux + -1, uy + 0))
                    enemy_bots_2.add(Position(ux + -1, uy + 1))
                    enemy_bots_2.add(Position(ux + 0, uy + -1))
                    enemy_bots_2.add(Position(ux + 0, uy + 1))
                    enemy_bots_2.add(Position(ux + 1, uy + -1))
                    enemy_bots_2.add(Position(ux + 1, uy + 0))
                    enemy_bots_2.add(Position(ux + 1, uy + 1))
                    enemy_bots_8.add(Position(ux + -2, uy + -2))
                    enemy_bots_8.add(Position(ux + -2, uy + -1))
                    enemy_bots_8.add(Position(ux + -2, uy + 0))
                    enemy_bots_8.add(Position(ux + -2, uy + 1))
                    enemy_bots_8.add(Position(ux + -2, uy + 2))
                    enemy_bots_8.add(Position(ux + -1, uy + -2))
                    enemy_bots_8.add(Position(ux + -1, uy + 2))
                    enemy_bots_8.add(Position(ux + 0, uy + -2))
                    enemy_bots_8.add(Position(ux + 0, uy + 2))
                    enemy_bots_8.add(Position(ux + 1, uy + -2))
                    enemy_bots_8.add(Position(ux + 1, uy + 2))
                    enemy_bots_8.add(Position(ux + 2, uy + -2))
                    enemy_bots_8.add(Position(ux + 2, uy + -1))
                    enemy_bots_8.add(Position(ux + 2, uy + 0))
                    enemy_bots_8.add(Position(ux + 2, uy + 1))
                    enemy_bots_8.add(Position(ux + 2, uy + 2))

            for tile in tiles:
                building_id = get_bid(tile)
                if building_id is not None:
                    building_cache[tile] = Building(ct, building_id)

                if not ct.is_tile_passable(tile):
                    continue
                    
                if tile in enemy_builder_bots:
                    continue
                    
                score = 0

                building = _bc_get(tile)
                    
                if building is not None:
                    if building.team != my_team:
                        score += 1
                        if building.entityType in cls.ROUTING_SET:
                            score += 5


                    new_loc = tile.add(Direction.NORTH)
                    nx, ny = new_loc.x, new_loc.y
                    if (0 <= nx < map_w and 0 <= ny < map_h) and ct.is_in_vision(new_loc):
                        adj_building = _bc_get(new_loc)
                        if adj_building is not None:
                            if adj_building.team != my_team and adj_building.entityType == LAUNCHER:
                                score -= 1000
                            elif adj_building.team != my_team and adj_building.entityType in ROUTING:
                                score += 3
                    new_loc = tile.add(Direction.NORTHEAST)
                    nx, ny = new_loc.x, new_loc.y
                    if (0 <= nx < map_w and 0 <= ny < map_h) and ct.is_in_vision(new_loc):
                        adj_building = _bc_get(new_loc)
                        if adj_building is not None:
                            if adj_building.team != my_team and adj_building.entityType == LAUNCHER:
                                score -= 1000
                            elif adj_building.team != my_team and adj_building.entityType in ROUTING:
                                score += 3
                    new_loc = tile.add(Direction.EAST)
                    nx, ny = new_loc.x, new_loc.y
                    if (0 <= nx < map_w and 0 <= ny < map_h) and ct.is_in_vision(new_loc):
                        adj_building = _bc_get(new_loc)
                        if adj_building is not None:
                            if adj_building.team != my_team and adj_building.entityType == LAUNCHER:
                                score -= 1000
                            elif adj_building.team != my_team and adj_building.entityType in ROUTING:
                                score += 3
                    new_loc = tile.add(Direction.SOUTHEAST)
                    nx, ny = new_loc.x, new_loc.y
                    if (0 <= nx < map_w and 0 <= ny < map_h) and ct.is_in_vision(new_loc):
                        adj_building = _bc_get(new_loc)
                        if adj_building is not None:
                            if adj_building.team != my_team and adj_building.entityType == LAUNCHER:
                                score -= 1000
                            elif adj_building.team != my_team and adj_building.entityType in ROUTING:
                                score += 3
                    new_loc = tile.add(Direction.SOUTH)
                    nx, ny = new_loc.x, new_loc.y
                    if (0 <= nx < map_w and 0 <= ny < map_h) and ct.is_in_vision(new_loc):
                        adj_building = _bc_get(new_loc)
                        if adj_building is not None:
                            if adj_building.team != my_team and adj_building.entityType == LAUNCHER:
                                score -= 1000
                            elif adj_building.team != my_team and adj_building.entityType in ROUTING:
                                score += 3
                    new_loc = tile.add(Direction.SOUTHWEST)
                    nx, ny = new_loc.x, new_loc.y
                    if (0 <= nx < map_w and 0 <= ny < map_h) and ct.is_in_vision(new_loc):
                        adj_building = _bc_get(new_loc)
                        if adj_building is not None:
                            if adj_building.team != my_team and adj_building.entityType == LAUNCHER:
                                score -= 1000
                            elif adj_building.team != my_team and adj_building.entityType in ROUTING:
                                score += 3
                    new_loc = tile.add(Direction.WEST)
                    nx, ny = new_loc.x, new_loc.y
                    if (0 <= nx < map_w and 0 <= ny < map_h) and ct.is_in_vision(new_loc):
                        adj_building = _bc_get(new_loc)
                        if adj_building is not None:
                            if adj_building.team != my_team and adj_building.entityType == LAUNCHER:
                                score -= 1000
                            elif adj_building.team != my_team and adj_building.entityType in ROUTING:
                                score += 3
                    new_loc = tile.add(Direction.NORTHWEST)
                    nx, ny = new_loc.x, new_loc.y
                    if (0 <= nx < map_w and 0 <= ny < map_h) and ct.is_in_vision(new_loc):
                        adj_building = _bc_get(new_loc)
                        if adj_building is not None:
                            if adj_building.team != my_team and adj_building.entityType == LAUNCHER:
                                score -= 1000
                            elif adj_building.team != my_team and adj_building.entityType in ROUTING:
                                score += 3

                if tile in enemy_bots_2:
                    score -= 100
                elif tile in enemy_bots_8:
                    score -= 50

                _sa((score, tile))
                if ct.get_cpu_time_elapsed() > 1920:
                    break

            best_pos = max(scores, key=lambda x: x[0])[1] if scores else None

            print("Plausible place to throw:", best_pos)

            if nearby_ally_bot is not None and best_pos is not None and ct.can_launch(nearby_ally_bot, best_pos):
                # return  # -- disable supportive launchers for now --
                ct.launch(nearby_ally_bot, best_pos)

    @classmethod
    def on_map(cls, ct, pos):
        return 0 <= pos.x < ct.get_map_width() and 0 <= pos.y < ct.get_map_height()

    @classmethod
    def end_turn(cls):
        Unit.end_turn()