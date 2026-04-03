from cambc import Team, EntityType, Direction, Position, ResourceType, Environment, GameConstants, GameError, Controller
import random
import heapq
import array
import time
import math
import sys
from collections import deque, defaultdict
from typing import NamedTuple
from Awubot.Builder import BuilderState, Builder
from Awubot.Constants import Constants
from Awubot.Core import Core
from Awubot.Globals import Globals, Cache
from Awubot.Map import LocalMask, MapMask, TileInfo, Map
from Awubot.MoveManager import MoveManager
from Awubot.RobotPlayer import Entrypoint, Player
from Awubot.Unit import Unit
from Awubot.Util import Util
from Awubot.debug.Profiler import Profiler
from Awubot.explore.Explore import Explore
from Generated.BuildManager import BuildManager
from Generated.debug.Debug import Color, Debug
from Generated.nav.Dials import Dials
from Generated.nav.Dijkstra import Dijkstra
from Generated.nav.DirectionPicker import DirectionPicker
from Generated.nav.FastDijkstra import FastDijkstra
from Generated.nav.FlatDijkstra import FlatDijkstra
from Generated.nav.GlobalBfs import GlobalBfs
from Generated.nav.GlobalBitmaskBfs import GlobalBitmaskBfs


class OmNom:
    cur_target: Position
    cur_target = None
    bug_pos: Position
    bug_pos = None

    last_obstacle_found: Position | None = None
    rotate_right: bool | None = None
    min_dist: int = 1_000_000

    bug_path: list[Position] = []
    bug_min_dist: list[int] = []
    bug_last_obstacle_found: list[Position | None] = []

    bfs_dist: list[int] = [0] * 9

    @classmethod
    def can_move_bug(cls, pos: Position) -> bool:
        if not Util.on_the_map(pos):
            return False
        if (MapMask.encode_bit(pos) & MapMask.wall) != 0:
            return False
        return True

    @classmethod
    def move_bug(cls, pos: Position) -> None:
        cls.bug_pos = pos

        cls.bug_path.append(cls.bug_pos)
        cls.bug_min_dist.append(cls.min_dist)
        cls.bug_last_obstacle_found.append(cls.last_obstacle_found)

    @classmethod
    def restore_bug_in_vision(cls) -> None:
        while cls.bug_path and not Globals.ct.is_in_vision(cls.bug_path[-1]):
            cls.bug_path.pop()
            cls.bug_min_dist.pop()
            cls.bug_last_obstacle_found.pop()

        if cls.bug_path:
            cls.bug_pos = cls.bug_path[-1]
            cls.min_dist = cls.bug_min_dist[-1]
            cls.last_obstacle_found = cls.bug_last_obstacle_found[-1]
        else:
            cls.reset_bug()

    @classmethod
    def reset_bug(cls) -> None:
        cls.bug_pos = Globals.ct.get_position()
        cls.min_dist = 1_000_000
        cls.last_obstacle_found = None
        cls.bug_path = []                
        cls.bug_min_dist = []            
        cls.bug_last_obstacle_found = [] 
        cls.rotate_right = None


    @classmethod
    def bug_step(cls) -> bool:
        # moves bug toward cur_target, returns True if should keep stepping

        dist: int = cls.bug_pos.distance_squared(cls.cur_target)
        if dist < cls.min_dist:
            cls.min_dist = dist
            cls.last_obstacle_found = None

        dir: Direction
        if cls.last_obstacle_found is not None:
            dir = cls.bug_pos.direction_to(cls.last_obstacle_found)
        else:
            dir = cls.bug_pos.direction_to(cls.cur_target)

        new_pos: Position = cls.bug_pos.add(dir)
        if Util.on_the_map(new_pos) and not Globals.ct.is_in_vision(new_pos):
            return False

        if cls.can_move_bug(new_pos):
            # mini-reset, keep min_dist, bug path
            cls.rotate_right = None
            cls.last_obstacle_found = None
            cls.move_bug(new_pos)
            return True

        if cls.rotate_right is None:
            # TODO: do rotation check
            cls.rotate_right = True

        for _ in range(16):
            if cls.rotate_right:
                dir = dir.rotate_right()
            else:
                dir = dir.rotate_left()
            new_pos = cls.bug_pos.add(dir)

            if Util.on_the_map(new_pos) and not Globals.ct.is_in_vision(new_pos):
                return False

            if cls.can_move_bug(new_pos):
                cls.move_bug(new_pos)
                return True

            if Util.on_the_map(new_pos):
                cls.last_obstacle_found = new_pos
            else:
                cls.rotate_right ^= True

        Debug.log("fell off 16 loop")
        return False

    @classmethod
    def bug_loop(cls):
        if cls.bug_pos is None or not Globals.ct.is_in_vision(cls.bug_pos):
            cls.restore_bug_in_vision()
        for _ in range(10):
            if cls.bug_pos.distance_squared(cls.cur_target) <= 2: # adj
                break

            keep_going = cls.bug_step()
            if not keep_going:
                break

    @classmethod
    def move_to(cls, target: Position):
        if cls.cur_target is None or target != cls.cur_target:
            cls.reset_bug()
            cls.cur_target = target
            
        cls.bug_loop()
        # ... BFS + pick

    @classmethod
    def run_bfs(cls):
        pass

# ---===
    @classmethod
    def debug_path(cls):
        path_len = len(cls.bug_path)
        max_len = max(1, path_len - 1)
        for i in range(path_len):
            t = i / max_len
            intensity = int(50 + 205 * t)
            Globals.ct.draw_indicator_dot(
                cls.bug_path[i], 0, intensity, intensity)
        if cls.bug_pos is not None:
            Globals.ct.draw_indicator_dot(cls.bug_pos, 0, 255, 255)
# ===---
