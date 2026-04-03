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
from Awubot.Constants import Constants
from Awubot.Globals import Globals
from Awubot.MoveManager import MoveManager
from Awubot.Util import Util
from Awubot.debug.Profiler import Profiler
from Generated.MarketMaker import MarketMaker
from Generated.RobotPlayer import Entrypoint, Player
from Generated.bbot.Attacker import Attacker
from Generated.bbot.Builder import Builder
from Generated.bbot.States import StateBuildHarvester, StateAttackTransporter, StateRoute, StateExplore
from Generated.bbot.VisionTracker import TransporterInfo, VisionTracker
from Generated.build.BuildManager import BuildManager
from Generated.build.OreExecutive import OreExecutive
from Generated.build.OrePositionPicker import OrePositionPicker
from Generated.build.RouteToCore import RouteToCore
from Generated.build.SuicideExecutor import SuicideExecutor
from Generated.comms.Comms import Comms
from Generated.comms.Marker import Marker
from Generated.comms.MarkerPositionPicker import MarkerPositionPicker
from Generated.debug.Debug import Color, Debug
from Generated.explore.Explore import Explore
from Generated.heal.HealExecutor import HealExecutor
from Generated.map.DarkForest import TreeNode, DarkForest
from Generated.map.Map import TileInfo, Map
from Generated.map.Symmetry import Sym, Symmetry
from Generated.nav.BfsBureau import BfsBureau
from Generated.nav.Pathfinder import Pathfinder
from Generated.units.Core import Core
from Generated.units.Unit import Unit
# ===--- IMPORT



class Sym(Enum):
    VERTICAL = 1
    HORIZONTAL = 2
    ROTATIONAL = 3
    UNKNOWN = 4


class Symmetry:
    V: int = 1
    H: int = 1
    R: int = 1
    is_sym_known: bool = False
    map_sym: Sym = Sym.UNKNOWN
    check_map: list

    enemy_core_pos_set: set[int]
    enemy_core_pos: Position

    @classmethod
    def predict_enemy_core(cls):
        cls.enemy_core_pos = cls.sym_pos(Unit.core_pos)
        idx = (((cls.enemy_core_pos.x) + 3) * 56 + ((cls.enemy_core_pos.y) + 3))
        cls.enemy_core_pos_set = {
            idx -1,
            idx +55,
            idx +56,
            idx +57,
            idx +1,
            idx -55,
            idx -56,
            idx -57,
            idx ,
        }

    @classmethod
    def and_sym(cls, V, H, R):
        cls.V &= V
        cls.H &= H
        cls.R &= R

    @classmethod
    def run_sym_check(cls):
        if cls.is_sym_known: 
            return

        cls.check_map[cls.V + (cls.H * 2) + (cls.R * 4)]()

        if cls.V + cls.H + cls.R == 1: 
            cls.do_sym_found_stuff()


    @classmethod
    def do_sym_found_stuff(cls):
        cls.is_sym_known = True

        if cls.V:
            cls.map_sym = Sym.VERTICAL
        elif cls.H:
            cls.map_sym = Sym.HORIZONTAL
        else:
            cls.map_sym = Sym.ROTATIONAL
        cls.predict_enemy_core()

        Profiler.start()
        Map.sync_tile_infos()
        Profiler.end_now("""Map.sync_tile_infos""")


# ---===
    @staticmethod
    def sym_posV(pos: Position):
        return Position(Map.maxX - pos.x, pos.y)
# ===---
# ---===
    @staticmethod
    def sym_posH(pos: Position):
        return Position(pos.x, Map.maxY - pos.y)
# ===---
# ---===
    @staticmethod
    def sym_posR(pos: Position):
        return Position(Map.maxX - pos.x, Map.maxY - pos.y)
# ===---

    @classmethod
    def sym_pos(cls, pos: Position):
        # guess: R > V > H
        if cls.R:
            return Position(Map.maxX - pos.x, Map.maxY - pos.y)
        if cls.V:
            return Position(Map.maxX - pos.x, pos.y)
        return Position(pos.x, Map.maxY - pos.y)


    @classmethod
    def debug(cls):
        print(f"sym: {' V'[cls.V]}{' H'[cls.H]}{' R'[cls.R]}")



    @staticmethod
    def checkV():
        CORE = EntityType.CORE
        maxX, maxY = Map.maxX, Map.maxY
        tile_info = Map.tile_info
        for pos in Map.nearby_tiles:
            x, y = pos.x, pos.y
            ti = tile_info[x][y]
            env = ti.env
            etype = ti.entity_type


            opp_ti = tile_info[maxX - x][y]
            if opp_ti is not None:
                if env != opp_ti.env:
                    Symmetry.V = 0

                opp_etype = opp_ti.entity_type
                if (etype == CORE or opp_etype == CORE) and etype != opp_etype:
                    Symmetry.V = 0




    @staticmethod
    def checkH():
        CORE = EntityType.CORE
        maxX, maxY = Map.maxX, Map.maxY
        tile_info = Map.tile_info
        for pos in Map.nearby_tiles:
            x, y = pos.x, pos.y
            ti = tile_info[x][y]
            env = ti.env
            etype = ti.entity_type



            opp_ti = tile_info[x][maxY - y]
            if opp_ti is not None:
                if env != opp_ti.env:
                    Symmetry.H = 0

                opp_etype = opp_ti.entity_type
                if (etype == CORE or opp_etype == CORE) and etype != opp_etype:
                    Symmetry.H = 0



    @staticmethod
    def checkVH():
        CORE = EntityType.CORE
        maxX, maxY = Map.maxX, Map.maxY
        tile_info = Map.tile_info
        for pos in Map.nearby_tiles:
            x, y = pos.x, pos.y
            ti = tile_info[x][y]
            env = ti.env
            etype = ti.entity_type


            opp_ti = tile_info[maxX - x][y]
            if opp_ti is not None:
                if env != opp_ti.env:
                    Symmetry.V = 0

                opp_etype = opp_ti.entity_type
                if (etype == CORE or opp_etype == CORE) and etype != opp_etype:
                    Symmetry.V = 0


            opp_ti = tile_info[x][maxY - y]
            if opp_ti is not None:
                if env != opp_ti.env:
                    Symmetry.H = 0

                opp_etype = opp_ti.entity_type
                if (etype == CORE or opp_etype == CORE) and etype != opp_etype:
                    Symmetry.H = 0



    @staticmethod
    def checkR():
        CORE = EntityType.CORE
        maxX, maxY = Map.maxX, Map.maxY
        tile_info = Map.tile_info
        for pos in Map.nearby_tiles:
            x, y = pos.x, pos.y
            ti = tile_info[x][y]
            env = ti.env
            etype = ti.entity_type




            opp_ti = tile_info[maxX - x][maxY - y]
            if opp_ti is not None:
                if env != opp_ti.env:
                    Symmetry.R = 0

                opp_etype = opp_ti.entity_type
                if (etype == CORE or opp_etype == CORE) and etype != opp_etype:
                    Symmetry.R = 0


    @staticmethod
    def checkVR():
        CORE = EntityType.CORE
        maxX, maxY = Map.maxX, Map.maxY
        tile_info = Map.tile_info
        for pos in Map.nearby_tiles:
            x, y = pos.x, pos.y
            ti = tile_info[x][y]
            env = ti.env
            etype = ti.entity_type


            opp_ti = tile_info[maxX - x][y]
            if opp_ti is not None:
                if env != opp_ti.env:
                    Symmetry.V = 0

                opp_etype = opp_ti.entity_type
                if (etype == CORE or opp_etype == CORE) and etype != opp_etype:
                    Symmetry.V = 0



            opp_ti = tile_info[maxX - x][maxY - y]
            if opp_ti is not None:
                if env != opp_ti.env:
                    Symmetry.R = 0

                opp_etype = opp_ti.entity_type
                if (etype == CORE or opp_etype == CORE) and etype != opp_etype:
                    Symmetry.R = 0


    @staticmethod
    def checkHR():
        CORE = EntityType.CORE
        maxX, maxY = Map.maxX, Map.maxY
        tile_info = Map.tile_info
        for pos in Map.nearby_tiles:
            x, y = pos.x, pos.y
            ti = tile_info[x][y]
            env = ti.env
            etype = ti.entity_type



            opp_ti = tile_info[x][maxY - y]
            if opp_ti is not None:
                if env != opp_ti.env:
                    Symmetry.H = 0

                opp_etype = opp_ti.entity_type
                if (etype == CORE or opp_etype == CORE) and etype != opp_etype:
                    Symmetry.H = 0


            opp_ti = tile_info[maxX - x][maxY - y]
            if opp_ti is not None:
                if env != opp_ti.env:
                    Symmetry.R = 0

                opp_etype = opp_ti.entity_type
                if (etype == CORE or opp_etype == CORE) and etype != opp_etype:
                    Symmetry.R = 0


    @staticmethod
    def checkVHR():
        CORE = EntityType.CORE
        maxX, maxY = Map.maxX, Map.maxY
        tile_info = Map.tile_info
        for pos in Map.nearby_tiles:
            x, y = pos.x, pos.y
            ti = tile_info[x][y]
            env = ti.env
            etype = ti.entity_type


            opp_ti = tile_info[maxX - x][y]
            if opp_ti is not None:
                if env != opp_ti.env:
                    Symmetry.V = 0

                opp_etype = opp_ti.entity_type
                if (etype == CORE or opp_etype == CORE) and etype != opp_etype:
                    Symmetry.V = 0


            opp_ti = tile_info[x][maxY - y]
            if opp_ti is not None:
                if env != opp_ti.env:
                    Symmetry.H = 0

                opp_etype = opp_ti.entity_type
                if (etype == CORE or opp_etype == CORE) and etype != opp_etype:
                    Symmetry.H = 0


            opp_ti = tile_info[maxX - x][maxY - y]
            if opp_ti is not None:
                if env != opp_ti.env:
                    Symmetry.R = 0

                opp_etype = opp_ti.entity_type
                if (etype == CORE or opp_etype == CORE) and etype != opp_etype:
                    Symmetry.R = 0


    check_map: list = [
        lambda: Debug.warn('all syms eliminated!'),
        checkV,
        checkH,
        checkVH,
        checkR,
        checkVR,
        checkHR,
        checkVHR,
    ]
