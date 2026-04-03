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
from Awubot.Constants import Constants
from Awubot.Globals import Globals
from Awubot.MoveManager import MoveManager
from Awubot.Util import Util
from Awubot.build.Builder import BuilderState, Builder
from Awubot.core.Core import Core
from Awubot.debug.Profiler import Profiler
from Awubot.explore.Explore import Explore
from Awubot.nav.Pathfinder import Pathfinder
from Generated.MarketMaker import MarketMaker
from Generated.RobotPlayer import Entrypoint, Player
from Generated.Unit import Unit
from Generated.build.BuildManager import BuildManager
from Generated.build.OreExecutive import OreExecutive
from Generated.build.OrePositionPicker import OrePositionPicker
from Generated.build.RouteToCore import RouteToCore
from Generated.build.SuicideExecutor import SuicideExecutor
from Generated.debug.Debug import Color, Debug
from Generated.heal.HealExecutor import HealExecutor
from Generated.nav.BfsBureau import BfsBureau
from Generated.nav.ClaudeGlobalBfs import ClaudeGlobalBfs
from Generated.nav.DirectionPicker import DirectionPicker
from Generated.nav.EgoBridgeBfs import EgoBridgeBfs
from Generated.nav.MyGlobalBfs import MyGlobalBfs
from Generated.nav.MyGlobalBfs2 import MyGlobalBfs2


class TileInfo:
    env: Environment
    round: int

    easily_passable: bool  # (allied core)/road/conveyor/bridge/splitter
    entity_type: EntityType | None

    has_building: bool  # non-marker building
    building_hp: int
    is_building_ally: bool

    has_bot: bool  # non-self builder bot
    bot_hp: int
    is_bot_ally: bool


# ---===
class Map:
    W: int
    H: int
    maxX: int
    maxY: int

    # [x][y], 1 None buffer on bot sides
    tile_info: list[list[TileInfo | None]]
    nearby_tiles: list[Position]
    nearby_ally_bots: int
    nearby_enemy_bots: int

    @staticmethod
    def init():
        Map.W = Globals.ct.get_map_width()
        Map.H = Globals.ct.get_map_height()
        Map.maxX = Map.W - 1
        Map.maxY = Map.H - 1

        Profiler.start()
        Map.tile_info = [[None] * (Map.H+1) for _ in range(Map.W+1)]
        Profiler.end('tile_info init')

    @classmethod
    def fill_tile_info(cls):
        ct = Globals.ct
        round = ct.get_current_round()
        tile_info = cls.tile_info

        cls.nearby_ally_bots = 0
        cls.nearby_enemy_bots = 0
        cls.nearby_tiles = ct.get_nearby_tiles(20)

        for pos in cls.nearby_tiles:
            tile_env: Environment = ct.get_tile_env(pos)

            ti: TileInfo | None = tile_info[pos.x][pos.y]
            if ti is None:
                ti = TileInfo()
                tile_info[pos.x][pos.y] = ti

            ti.env = tile_env
            ti.round = round

            building_id: int | None = ct.get_tile_building_id(pos)
            bot_id: int | None = ct.get_tile_builder_bot_id(pos)

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
                    cls.nearby_ally_bots += 1
                else:
                    cls.nearby_enemy_bots += 1

            ti.easily_passable = False

            if ti.has_building:
                ti.is_building_ally = ct.get_team(
                    building_id) == Globals.my_team
                ti.building_hp = ct.get_hp(building_id)

                if (etype in Constants.PASSABLE_SET or (
                        etype == EntityType.CORE
                        and ti.is_building_ally
                )):
                    ti.easily_passable = True
# ===---
