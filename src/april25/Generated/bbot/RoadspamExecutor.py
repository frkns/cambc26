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
            
        my_pos = Globals.my_pos
        
        if BuildManager.can_build_road(my_pos.add(Direction.NORTH)):
            BuildManager.build_road(my_pos.add(Direction.NORTH))
        if BuildManager.can_build_road(my_pos.add(Direction.NORTHEAST)):
            BuildManager.build_road(my_pos.add(Direction.NORTHEAST))
        if BuildManager.can_build_road(my_pos.add(Direction.EAST)):
            BuildManager.build_road(my_pos.add(Direction.EAST))
        if BuildManager.can_build_road(my_pos.add(Direction.SOUTHEAST)):
            BuildManager.build_road(my_pos.add(Direction.SOUTHEAST))
        if BuildManager.can_build_road(my_pos.add(Direction.SOUTH)):
            BuildManager.build_road(my_pos.add(Direction.SOUTH))
        if BuildManager.can_build_road(my_pos.add(Direction.SOUTHWEST)):
            BuildManager.build_road(my_pos.add(Direction.SOUTHWEST))
        if BuildManager.can_build_road(my_pos.add(Direction.WEST)):
            BuildManager.build_road(my_pos.add(Direction.WEST))
        if BuildManager.can_build_road(my_pos.add(Direction.NORTHWEST)):
            BuildManager.build_road(my_pos.add(Direction.NORTHWEST))
    
        









