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
from Generated.bbot.Attacker import Attacker
from Generated.bbot.Builder import Builder
from Generated.bbot.HarvesterAdjacent import AdjacentInfo, HarvesterAdjacent
from Generated.bbot.HealExecutor import HealExecutor
from Generated.bbot.HealTargeter import HealTargetInfo, HealTargeter
from Generated.bbot.PatrolTargeter import PatrolTargeter
from Generated.bbot.RushTargeter import RushTargeter
from Generated.bbot.ShieldTargeter import ShieldTargetInfo, ShieldTargeter
from Generated.bbot.StalkTargeter import StalkTargeter
from Generated.bbot.States import StateBuildHarvester, StateBuildHarvesterAx, StateAttackTransporter, StateRoute, StateMoveTo, StateBuildTurret, StateBuildBarrier
from Generated.bbot.VisionTracker import TransporterInfo, ConnectManager, BotInfo, VisionTracker
from Generated.build.BuildManager import BuildManager
from Generated.build.OreExecutive import OreExecutive
from Generated.build.OrePositionPicker import OrePositionPicker
from Generated.build.RouteToCore import RouteToCore
from Generated.build.SuicideExecutor import SuicideExecutor
from Generated.comms.Comms import Comms
from Generated.comms.Marker import Marker
from Generated.comms.MarkerPositionPicker import MarkerPositionPicker
from Generated.Constants import Constants
from Generated.core.Core import Core
from Generated.core.CoreHistory import CoreHistory
from Generated.core.SpawnManager import SpawnManager
from Generated.debug.Debug import Color, Debug
from Generated.debug.Profiler import Profiler
from Generated.explore.Explore import Explore
from Generated.map.DarkForest import TreeNode, DarkForest
from Generated.map.Map import TileInfo, Map
from Generated.map.Symmetry import Sym, Symmetry
from Generated.MarketMaker import MarketMaker
from Generated.nav.BfsBureau import BfsBureau
from Generated.nav.Pathfinder import Pathfinder
from Generated.RobotPlayer import Entrypoint, Player
from Generated.sentinel.Sentinel import Sentinel
from Generated.sentinel.SentinelSupervisor import SentinelTargetInfo, SentinelSupervisor
from Generated.units.Unit import Unit
# ===--- IMPORT



class TileInfo:

    env: Environment
    round: int

    easily_passable: bool  # (allied core)/road/conveyor/bridge/splitter, maybe deprecated?
    harvester_adjacent: bool

    has_building: bool  # non-marker building
    building_hp: int
    building_id: int
    is_building_ally: bool  # lol, includes markers
    entity_type: EntityType | None
    target: Position | None  # for transporters

    has_bot: bool  # non-self builder bot
    bot_hp: int
    bot_id: int
    is_bot_ally: bool

    has_turret: bool
    turret_direction: Direction


class Map:
    W: int
    H: int
    maxX: int
    maxY: int

    # [x][y], some buffer right/bot side
    tile_info: list[list[TileInfo | None]]
    nearby_tiles: list[Position]
    proc_nearby_tiles: list[tuple[Position, int, int, int, TileInfo]]
    num_allies: int
    num_enemies: int
    harvester_set: set[int] = set()

    # cleared every turn
    new_syms: list[Position] = []

    @staticmethod
    def init():
        Map.W = Globals.ct.get_map_width()
        Map.H = Globals.ct.get_map_height()
        Map.maxX = Map.W - 1
        Map.maxY = Map.H - 1

        Map.tile_info = [[None] * (Map.H + 5) for _ in range(Map.W + 5)]


    @classmethod 
    def fill_tile_info(cls):
        sym = Symmetry.map_sym

        if sym == Sym.UNKNOWN:
            cls.fill_tile_infoUNKNOWN()
            return
        if sym == Sym.VERTICAL:
            cls.fill_tile_infoV()
            return
        if sym == Sym.HORIZONTAL:
            cls.fill_tile_infoH()
            return
        cls.fill_tile_infoR()


    @classmethod
    def fill_tile_infoV(cls):
        ct = Globals.ct
        round = ct.get_current_round()
        tile_info = cls.tile_info

        cls.num_allies = 0
        cls.num_enemies = 0
        cls.nearby_tiles = ct.get_nearby_tiles()

        maxX, maxY = cls.maxX, cls.maxY
        new_syms = cls.new_syms
        new_syms.clear()

        cls.proc_nearby_tiles = []
        for pos in cls.nearby_tiles:
            x, y = pos.x, pos.y
            idx = (((x) + 3) * 56 + ((y) + 3))
            ti: TileInfo | None = tile_info[x][y]
            if ti is None:
                ti = TileInfo()
                tile_info[x][y] = ti

            cls.proc_nearby_tiles.append(
                (pos, x, y, idx, ti)
            )


        for pos, x, y, pos_idx, ti in cls.proc_nearby_tiles:
            tile_env: Environment = ct.get_tile_env(pos)

            ox, oy = maxX - x, y

            opp_ti = tile_info[ox][oy]
            if opp_ti is None:
                opp_ti = TileInfo()
                opp_ti.env = tile_env
                opp_ti.has_bot = False
                opp_ti.has_turret = False
                opp_ti.has_building = False
                opp_ti.easily_passable = False
                opp_ti.harvester_adjacent = False
                tile_info[ox][oy] = opp_ti
                new_syms.append(Position(ox, oy))

            ti.env = tile_env
            ti.round = round

            building_id: int | None = ct.get_tile_building_id(pos)
            bot_id: int | None = ct.get_tile_builder_bot_id(pos)
            ti.building_id = building_id
            ti.bot_id = bot_id

            etype = None
            ti.has_building = (
                building_id is not None and 
                (etype := ct.get_entity_type(building_id)) != EntityType.MARKER
            )
            ti.entity_type = etype
            ti.has_bot = bot_id is not None and bot_id != Globals.my_id

            if ti.has_bot:
                ti.bot_hp = ct.get_hp(bot_id)
                ti.is_bot_ally = ct.get_team(bot_id) == Globals.my_team

                if ti.is_bot_ally:
                    cls.num_allies += 1
                else:
                    cls.num_enemies += 1

            ti.easily_passable = False

            if etype == EntityType.MARKER:
                ti.is_building_ally = ct.get_team(building_id) == Globals.my_team

            if ti.has_building:
                ti.is_building_ally = ct.get_team(building_id) == Globals.my_team

                ti.building_hp = ct.get_hp(building_id)
                if (etype in Constants.PASSABLE_SET or (
                        etype == EntityType.CORE
                        and ti.is_building_ally
                )):
                    ti.easily_passable = True

            ti.has_turret = False
                    
            if etype == EntityType.CONVEYOR or etype == EntityType.ARMOURED_CONVEYOR:
                tpos = pos.add(ct.get_direction(building_id))
                ti.target = tpos
                DarkForest.add_edge(pos_idx, (((tpos.x) + 3) * 56 + ((tpos.y) + 3)))
            elif etype == EntityType.BRIDGE:
                tpos = ct.get_bridge_target(building_id)
                ti.target = tpos
                DarkForest.add_edge(pos_idx, (((tpos.x) + 3) * 56 + ((tpos.y) + 3)))
            else:
                ti.target = None

                if etype in (EntityType.SENTINEL, EntityType.GUNNER, EntityType.FOUNDRY):
                    if etype in (EntityType.SENTINEL, EntityType.GUNNER):
                        ti.has_turret = True
                        ti.turret_direction = ct.get_direction(building_id)

                    if ti.is_building_ally:
                        DarkForest.register_sink(pos_idx, 3)
                    else:
                        DarkForest.register_sink(pos_idx, 4)
                else:
                    DarkForest.remove_node(pos_idx)

            # maybe check ti/ax?
            if etype == EntityType.HARVESTER:
                cls.harvester_set.add(pos_idx)
            else:
                cls.harvester_set.discard(pos_idx)

            if etype == EntityType.MARKER and ti.is_building_ally:
                Comms.handle_message(ct.get_marker_value(building_id))


        HARVESTER = EntityType.HARVESTER

        for pos, x, y, idx, ti in cls.proc_nearby_tiles:
            ti.harvester_adjacent = \
                ((nti := tile_info[x-1][y]) is not None and nti.has_building and nti.entity_type == HARVESTER) or \
                ((nti := tile_info[x+1][y]) is not None and nti.has_building and nti.entity_type == HARVESTER) or \
                ((nti := tile_info[x][y-1]) is not None and nti.has_building and nti.entity_type == HARVESTER) or \
                ((nti := tile_info[x][y+1]) is not None and nti.has_building and nti.entity_type == HARVESTER)

    @classmethod
    def fill_tile_infoH(cls):
        ct = Globals.ct
        round = ct.get_current_round()
        tile_info = cls.tile_info

        cls.num_allies = 0
        cls.num_enemies = 0
        cls.nearby_tiles = ct.get_nearby_tiles()

        maxX, maxY = cls.maxX, cls.maxY
        new_syms = cls.new_syms
        new_syms.clear()

        cls.proc_nearby_tiles = []
        for pos in cls.nearby_tiles:
            x, y = pos.x, pos.y
            idx = (((x) + 3) * 56 + ((y) + 3))
            ti: TileInfo | None = tile_info[x][y]
            if ti is None:
                ti = TileInfo()
                tile_info[x][y] = ti

            cls.proc_nearby_tiles.append(
                (pos, x, y, idx, ti)
            )


        for pos, x, y, pos_idx, ti in cls.proc_nearby_tiles:
            tile_env: Environment = ct.get_tile_env(pos)

            ox, oy = x, maxY - y 

            opp_ti = tile_info[ox][oy]
            if opp_ti is None:
                opp_ti = TileInfo()
                opp_ti.env = tile_env
                opp_ti.has_bot = False
                opp_ti.has_turret = False
                opp_ti.has_building = False
                opp_ti.easily_passable = False
                opp_ti.harvester_adjacent = False
                tile_info[ox][oy] = opp_ti
                new_syms.append(Position(ox, oy))

            ti.env = tile_env
            ti.round = round

            building_id: int | None = ct.get_tile_building_id(pos)
            bot_id: int | None = ct.get_tile_builder_bot_id(pos)
            ti.building_id = building_id
            ti.bot_id = bot_id

            etype = None
            ti.has_building = (
                building_id is not None and 
                (etype := ct.get_entity_type(building_id)) != EntityType.MARKER
            )
            ti.entity_type = etype
            ti.has_bot = bot_id is not None and bot_id != Globals.my_id

            if ti.has_bot:
                ti.bot_hp = ct.get_hp(bot_id)
                ti.is_bot_ally = ct.get_team(bot_id) == Globals.my_team

                if ti.is_bot_ally:
                    cls.num_allies += 1
                else:
                    cls.num_enemies += 1

            ti.easily_passable = False

            if etype == EntityType.MARKER:
                ti.is_building_ally = ct.get_team(building_id) == Globals.my_team

            if ti.has_building:
                ti.is_building_ally = ct.get_team(building_id) == Globals.my_team

                ti.building_hp = ct.get_hp(building_id)
                if (etype in Constants.PASSABLE_SET or (
                        etype == EntityType.CORE
                        and ti.is_building_ally
                )):
                    ti.easily_passable = True

            ti.has_turret = False
                    
            if etype == EntityType.CONVEYOR or etype == EntityType.ARMOURED_CONVEYOR:
                tpos = pos.add(ct.get_direction(building_id))
                ti.target = tpos
                DarkForest.add_edge(pos_idx, (((tpos.x) + 3) * 56 + ((tpos.y) + 3)))
            elif etype == EntityType.BRIDGE:
                tpos = ct.get_bridge_target(building_id)
                ti.target = tpos
                DarkForest.add_edge(pos_idx, (((tpos.x) + 3) * 56 + ((tpos.y) + 3)))
            else:
                ti.target = None

                if etype in (EntityType.SENTINEL, EntityType.GUNNER, EntityType.FOUNDRY):
                    if etype in (EntityType.SENTINEL, EntityType.GUNNER):
                        ti.has_turret = True
                        ti.turret_direction = ct.get_direction(building_id)

                    if ti.is_building_ally:
                        DarkForest.register_sink(pos_idx, 3)
                    else:
                        DarkForest.register_sink(pos_idx, 4)
                else:
                    DarkForest.remove_node(pos_idx)

            # maybe check ti/ax?
            if etype == EntityType.HARVESTER:
                cls.harvester_set.add(pos_idx)
            else:
                cls.harvester_set.discard(pos_idx)

            if etype == EntityType.MARKER and ti.is_building_ally:
                Comms.handle_message(ct.get_marker_value(building_id))


        HARVESTER = EntityType.HARVESTER

        for pos, x, y, idx, ti in cls.proc_nearby_tiles:
            ti.harvester_adjacent = \
                ((nti := tile_info[x-1][y]) is not None and nti.has_building and nti.entity_type == HARVESTER) or \
                ((nti := tile_info[x+1][y]) is not None and nti.has_building and nti.entity_type == HARVESTER) or \
                ((nti := tile_info[x][y-1]) is not None and nti.has_building and nti.entity_type == HARVESTER) or \
                ((nti := tile_info[x][y+1]) is not None and nti.has_building and nti.entity_type == HARVESTER)

    @classmethod
    def fill_tile_infoR(cls):
        ct = Globals.ct
        round = ct.get_current_round()
        tile_info = cls.tile_info

        cls.num_allies = 0
        cls.num_enemies = 0
        cls.nearby_tiles = ct.get_nearby_tiles()

        maxX, maxY = cls.maxX, cls.maxY
        new_syms = cls.new_syms
        new_syms.clear()

        cls.proc_nearby_tiles = []
        for pos in cls.nearby_tiles:
            x, y = pos.x, pos.y
            idx = (((x) + 3) * 56 + ((y) + 3))
            ti: TileInfo | None = tile_info[x][y]
            if ti is None:
                ti = TileInfo()
                tile_info[x][y] = ti

            cls.proc_nearby_tiles.append(
                (pos, x, y, idx, ti)
            )


        for pos, x, y, pos_idx, ti in cls.proc_nearby_tiles:
            tile_env: Environment = ct.get_tile_env(pos)

            ox, oy = maxX - x, maxY - y 

            opp_ti = tile_info[ox][oy]
            if opp_ti is None:
                opp_ti = TileInfo()
                opp_ti.env = tile_env
                opp_ti.has_bot = False
                opp_ti.has_turret = False
                opp_ti.has_building = False
                opp_ti.easily_passable = False
                opp_ti.harvester_adjacent = False
                tile_info[ox][oy] = opp_ti
                new_syms.append(Position(ox, oy))

            ti.env = tile_env
            ti.round = round

            building_id: int | None = ct.get_tile_building_id(pos)
            bot_id: int | None = ct.get_tile_builder_bot_id(pos)
            ti.building_id = building_id
            ti.bot_id = bot_id

            etype = None
            ti.has_building = (
                building_id is not None and 
                (etype := ct.get_entity_type(building_id)) != EntityType.MARKER
            )
            ti.entity_type = etype
            ti.has_bot = bot_id is not None and bot_id != Globals.my_id

            if ti.has_bot:
                ti.bot_hp = ct.get_hp(bot_id)
                ti.is_bot_ally = ct.get_team(bot_id) == Globals.my_team

                if ti.is_bot_ally:
                    cls.num_allies += 1
                else:
                    cls.num_enemies += 1

            ti.easily_passable = False

            if etype == EntityType.MARKER:
                ti.is_building_ally = ct.get_team(building_id) == Globals.my_team

            if ti.has_building:
                ti.is_building_ally = ct.get_team(building_id) == Globals.my_team

                ti.building_hp = ct.get_hp(building_id)
                if (etype in Constants.PASSABLE_SET or (
                        etype == EntityType.CORE
                        and ti.is_building_ally
                )):
                    ti.easily_passable = True

            ti.has_turret = False
                    
            if etype == EntityType.CONVEYOR or etype == EntityType.ARMOURED_CONVEYOR:
                tpos = pos.add(ct.get_direction(building_id))
                ti.target = tpos
                DarkForest.add_edge(pos_idx, (((tpos.x) + 3) * 56 + ((tpos.y) + 3)))
            elif etype == EntityType.BRIDGE:
                tpos = ct.get_bridge_target(building_id)
                ti.target = tpos
                DarkForest.add_edge(pos_idx, (((tpos.x) + 3) * 56 + ((tpos.y) + 3)))
            else:
                ti.target = None

                if etype in (EntityType.SENTINEL, EntityType.GUNNER, EntityType.FOUNDRY):
                    if etype in (EntityType.SENTINEL, EntityType.GUNNER):
                        ti.has_turret = True
                        ti.turret_direction = ct.get_direction(building_id)

                    if ti.is_building_ally:
                        DarkForest.register_sink(pos_idx, 3)
                    else:
                        DarkForest.register_sink(pos_idx, 4)
                else:
                    DarkForest.remove_node(pos_idx)

            # maybe check ti/ax?
            if etype == EntityType.HARVESTER:
                cls.harvester_set.add(pos_idx)
            else:
                cls.harvester_set.discard(pos_idx)

            if etype == EntityType.MARKER and ti.is_building_ally:
                Comms.handle_message(ct.get_marker_value(building_id))


        HARVESTER = EntityType.HARVESTER

        for pos, x, y, idx, ti in cls.proc_nearby_tiles:
            ti.harvester_adjacent = \
                ((nti := tile_info[x-1][y]) is not None and nti.has_building and nti.entity_type == HARVESTER) or \
                ((nti := tile_info[x+1][y]) is not None and nti.has_building and nti.entity_type == HARVESTER) or \
                ((nti := tile_info[x][y-1]) is not None and nti.has_building and nti.entity_type == HARVESTER) or \
                ((nti := tile_info[x][y+1]) is not None and nti.has_building and nti.entity_type == HARVESTER)

    @classmethod
    def fill_tile_infoUNKNOWN(cls):
        ct = Globals.ct
        round = ct.get_current_round()
        tile_info = cls.tile_info

        cls.num_allies = 0
        cls.num_enemies = 0
        cls.nearby_tiles = ct.get_nearby_tiles()


        cls.proc_nearby_tiles = []
        for pos in cls.nearby_tiles:
            x, y = pos.x, pos.y
            idx = (((x) + 3) * 56 + ((y) + 3))
            ti: TileInfo | None = tile_info[x][y]
            if ti is None:
                ti = TileInfo()
                tile_info[x][y] = ti

            cls.proc_nearby_tiles.append(
                (pos, x, y, idx, ti)
            )


        for pos, x, y, pos_idx, ti in cls.proc_nearby_tiles:
            tile_env: Environment = ct.get_tile_env(pos)



            ti.env = tile_env
            ti.round = round

            building_id: int | None = ct.get_tile_building_id(pos)
            bot_id: int | None = ct.get_tile_builder_bot_id(pos)
            ti.building_id = building_id
            ti.bot_id = bot_id

            etype = None
            ti.has_building = (
                building_id is not None and 
                (etype := ct.get_entity_type(building_id)) != EntityType.MARKER
            )
            ti.entity_type = etype
            ti.has_bot = bot_id is not None and bot_id != Globals.my_id

            if ti.has_bot:
                ti.bot_hp = ct.get_hp(bot_id)
                ti.is_bot_ally = ct.get_team(bot_id) == Globals.my_team

                if ti.is_bot_ally:
                    cls.num_allies += 1
                else:
                    cls.num_enemies += 1

            ti.easily_passable = False

            if etype == EntityType.MARKER:
                ti.is_building_ally = ct.get_team(building_id) == Globals.my_team

            if ti.has_building:
                ti.is_building_ally = ct.get_team(building_id) == Globals.my_team

                ti.building_hp = ct.get_hp(building_id)
                if (etype in Constants.PASSABLE_SET or (
                        etype == EntityType.CORE
                        and ti.is_building_ally
                )):
                    ti.easily_passable = True

            ti.has_turret = False
                    
            if etype == EntityType.CONVEYOR or etype == EntityType.ARMOURED_CONVEYOR:
                tpos = pos.add(ct.get_direction(building_id))
                ti.target = tpos
                DarkForest.add_edge(pos_idx, (((tpos.x) + 3) * 56 + ((tpos.y) + 3)))
            elif etype == EntityType.BRIDGE:
                tpos = ct.get_bridge_target(building_id)
                ti.target = tpos
                DarkForest.add_edge(pos_idx, (((tpos.x) + 3) * 56 + ((tpos.y) + 3)))
            else:
                ti.target = None

                if etype in (EntityType.SENTINEL, EntityType.GUNNER, EntityType.FOUNDRY):
                    if etype in (EntityType.SENTINEL, EntityType.GUNNER):
                        ti.has_turret = True
                        ti.turret_direction = ct.get_direction(building_id)

                    if ti.is_building_ally:
                        DarkForest.register_sink(pos_idx, 3)
                    else:
                        DarkForest.register_sink(pos_idx, 4)
                else:
                    DarkForest.remove_node(pos_idx)

            # maybe check ti/ax?
            if etype == EntityType.HARVESTER:
                cls.harvester_set.add(pos_idx)
            else:
                cls.harvester_set.discard(pos_idx)

            if etype == EntityType.MARKER and ti.is_building_ally:
                Comms.handle_message(ct.get_marker_value(building_id))


        HARVESTER = EntityType.HARVESTER

        for pos, x, y, idx, ti in cls.proc_nearby_tiles:
            ti.harvester_adjacent = \
                ((nti := tile_info[x-1][y]) is not None and nti.has_building and nti.entity_type == HARVESTER) or \
                ((nti := tile_info[x+1][y]) is not None and nti.has_building and nti.entity_type == HARVESTER) or \
                ((nti := tile_info[x][y-1]) is not None and nti.has_building and nti.entity_type == HARVESTER) or \
                ((nti := tile_info[x][y+1]) is not None and nti.has_building and nti.entity_type == HARVESTER)



# ---===
    @classmethod
    def debug_tile_info(cls):
        """Debug all tile infos: wall=GREEN, titan ore=BLUE, axium ore=ORANGE, unseen=BLACK"""
        tile_info = cls.tile_info
        
        for x in range(cls.W):
            for y in range(cls.H):
                pos = Position(x, y)
                ti = tile_info[x][y]
                
                if ti is None:
                    # Unseen tile
                    Debug.dot(pos, Color.BLACK)
                else:
                    # Seen tile - only show walls and ores
                    env = ti.env
                    if env == Environment.WALL:
                        Debug.dot(pos, Color.GREEN)
                    elif env == Environment.ORE_TITANIUM:
                        Debug.dot(pos, Color.BLUE)
                    elif env == Environment.ORE_AXIONITE:
                        Debug.dot(pos, Color.ORANGE)
# ===---

# ---===
    @classmethod
    def sync_tile_infos(cls):
        # can be made more efficient

        tile_info = cls.tile_info
        maxX, maxY = cls.maxX, cls.maxY
        sym = Symmetry.map_sym
        new_syms = cls.new_syms

        for x in range(cls.W):
            row = tile_info[x]
            if sym == Sym.VERTICAL:
                ox = maxX - x
            elif sym == Sym.HORIZONTAL:
                ox = x
            else:
                ox = maxX - x
            orow = tile_info[ox]
            
            for y in range(cls.H):
                ti = row[y]
                if ti is None:
                    continue

                if sym == Sym.VERTICAL:
                    oy = y
                elif sym == Sym.HORIZONTAL:
                    oy = maxY - y
                else:
                    oy = maxY - y

                opp_ti = tile_info[ox][oy]
                if opp_ti is None:
                    opp_ti = TileInfo()
                    opp_ti.env = ti.env
                    opp_ti.has_bot = False
                    opp_ti.has_turret = False
                    opp_ti.has_building = False
                    opp_ti.easily_passable = False
                    opp_ti.harvester_adjacent = False
                    orow[oy] = opp_ti
                    new_syms.append(Position(ox, oy))
# ===---