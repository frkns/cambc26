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

class Breach(Unit):
    @classmethod
    def init(cls):
        Unit.init()
        DarkForest.init()

    @classmethod
    def start_turn(cls):
        Unit.start_turn()
        DarkForest.fcompute()
        DarkForest.debug_kind()

    @classmethod
    def run_turn(cls):
        ct = Globals.ct
        nearbyTiles = ct.get_nearby_tiles()
        nearbyCore = False
        for tile in nearbyTiles:
            daBuildingID = ct.get_tile_building_id(tile)
            if daBuildingID is not None:
                if ct.get_team(daBuildingID) != Globals.my_team and ct.get_entity_type(daBuildingID) == EntityType.CORE:
                    nearbyCore = True
                    break
        RANGE_DIST = 5
        if nearbyCore:
            RANGE_DIST = 2 #nearby core, shoot closer
        print("Nearby core?", nearbyCore, "Range dist:", RANGE_DIST)
        myDir = Globals.ct.get_direction()
        myPos = Globals.my_pos
        newPos = myPos
        for _ in range(RANGE_DIST):
            newPos =newPos.add(myDir)
        opposite = myDir.opposite()
        for _ in range(RANGE_DIST):
            if Globals.ct.can_fire(newPos):
                Globals.ct.fire(newPos)
                print("Yo firing at", newPos)
                return
            newPos = newPos.add(opposite)
    @classmethod
    def end_turn(cls):
        Unit.end_turn()