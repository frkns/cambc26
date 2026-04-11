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

class LauncherTargetInfo:
    position: Position

    has_bot: bool

    bot_hp: int

    rand_key: float  # for sake of beauty, should almost never matter
    
    harvester_adjacent: bool

    @staticmethod
    def is_better_than(a: LauncherTargetInfo, b: LauncherTargetInfo):
        if a.has_bot and b.has_bot:
            if a.bot_hp != b.bot_hp:
                return a.bot_hp < b.bot_hp
            
        if a.has_bot != b.has_bot:
            return a.has_bot
            
        if a.harvester_adjacent and (not b.harvester_adjacent): return True
        if (not a.harvester_adjacent) and b.harvester_adjacent: return False

        return a.rand_key < b.rand_key

class LauncherSupervisor:
    targets: list[LauncherTargetInfo]

    @classmethod
    def try_launch(cls):
        pos = cls.get_best_target()
        if pos is None or pos == Globals.my_pos:
            return

        target = cls.get_launch_target(pos)
        
        print(f'target launch @ {pos} to {target}')
        Debug.line(pos_a=pos, pos_b=target, color=Color.TEAL)
        
        if target is None:
            return
        
        if Globals.ct.can_launch(pos, target):
            Globals.ct.launch(pos, target)
            
    @classmethod
    def get_launch_target(cls, start: Position) -> Position | None:
        ct = Globals.ct
        
        dir = Globals.my_pos.direction_to(start)
        
        if dir == Direction.CENTRE:
            return
        
        # Find the furthest position we can launch to
        
        best = None
        target = start.add(dir)
        while Util.on_the_map(target) and Globals.ct.is_in_vision(target):
            if ct.can_launch(start, target):
                best = target
                
            target = target.add(dir)
            
        return best


    @classmethod
    def get_best_target(cls) -> Position | None:
        targets = cls.targets
        if not targets:
            return None

        best = targets[0]
        for target in targets[1:]:
            if LauncherTargetInfo.is_better_than(target, best):
                best = target

        if not best.has_bot:
            return None

        return best.position


    @classmethod
    def fill(cls):
        ct = Globals.ct
        cls.targets = []
        tile_info = Map.tile_info
        my_pos = Globals.my_pos
        
        x, y = my_pos.x , my_pos.y -1
        ti = tile_info[x][y]
        
        if ti is not None:
            info = LauncherTargetInfo()
            info.position = Position(x, y)
            info.has_bot = False
            info.rand_key = random.random()

            info.harvester_adjacent = ti.harvester_adjacent

            if ti.has_bot and not ti.is_bot_ally:
                info.has_bot = True
                info.bot_hp = ti.bot_hp

            cls.targets.append(info)
            
        x, y = my_pos.x +1, my_pos.y -1
        ti = tile_info[x][y]
        
        if ti is not None:
            info = LauncherTargetInfo()
            info.position = Position(x, y)
            info.has_bot = False
            info.rand_key = random.random()

            info.harvester_adjacent = ti.harvester_adjacent

            if ti.has_bot and not ti.is_bot_ally:
                info.has_bot = True
                info.bot_hp = ti.bot_hp

            cls.targets.append(info)
            
        x, y = my_pos.x +1, my_pos.y 
        ti = tile_info[x][y]
        
        if ti is not None:
            info = LauncherTargetInfo()
            info.position = Position(x, y)
            info.has_bot = False
            info.rand_key = random.random()

            info.harvester_adjacent = ti.harvester_adjacent

            if ti.has_bot and not ti.is_bot_ally:
                info.has_bot = True
                info.bot_hp = ti.bot_hp

            cls.targets.append(info)
            
        x, y = my_pos.x +1, my_pos.y +1
        ti = tile_info[x][y]
        
        if ti is not None:
            info = LauncherTargetInfo()
            info.position = Position(x, y)
            info.has_bot = False
            info.rand_key = random.random()

            info.harvester_adjacent = ti.harvester_adjacent

            if ti.has_bot and not ti.is_bot_ally:
                info.has_bot = True
                info.bot_hp = ti.bot_hp

            cls.targets.append(info)
            
        x, y = my_pos.x , my_pos.y +1
        ti = tile_info[x][y]
        
        if ti is not None:
            info = LauncherTargetInfo()
            info.position = Position(x, y)
            info.has_bot = False
            info.rand_key = random.random()

            info.harvester_adjacent = ti.harvester_adjacent

            if ti.has_bot and not ti.is_bot_ally:
                info.has_bot = True
                info.bot_hp = ti.bot_hp

            cls.targets.append(info)
            
        x, y = my_pos.x -1, my_pos.y +1
        ti = tile_info[x][y]
        
        if ti is not None:
            info = LauncherTargetInfo()
            info.position = Position(x, y)
            info.has_bot = False
            info.rand_key = random.random()

            info.harvester_adjacent = ti.harvester_adjacent

            if ti.has_bot and not ti.is_bot_ally:
                info.has_bot = True
                info.bot_hp = ti.bot_hp

            cls.targets.append(info)
            
        x, y = my_pos.x -1, my_pos.y 
        ti = tile_info[x][y]
        
        if ti is not None:
            info = LauncherTargetInfo()
            info.position = Position(x, y)
            info.has_bot = False
            info.rand_key = random.random()

            info.harvester_adjacent = ti.harvester_adjacent

            if ti.has_bot and not ti.is_bot_ally:
                info.has_bot = True
                info.bot_hp = ti.bot_hp

            cls.targets.append(info)
            
        x, y = my_pos.x -1, my_pos.y -1
        ti = tile_info[x][y]
        
        if ti is not None:
            info = LauncherTargetInfo()
            info.position = Position(x, y)
            info.has_bot = False
            info.rand_key = random.random()

            info.harvester_adjacent = ti.harvester_adjacent

            if ti.has_bot and not ti.is_bot_ally:
                info.has_bot = True
                info.bot_hp = ti.bot_hp

            cls.targets.append(info)
            
        x, y = my_pos.x , my_pos.y 
        ti = tile_info[x][y]
        
        if ti is not None:
            info = LauncherTargetInfo()
            info.position = Position(x, y)
            info.has_bot = False
            info.rand_key = random.random()

            info.harvester_adjacent = ti.harvester_adjacent

            if ti.has_bot and not ti.is_bot_ally:
                info.has_bot = True
                info.bot_hp = ti.bot_hp

            cls.targets.append(info)
            
