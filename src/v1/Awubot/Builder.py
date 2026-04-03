from cambc import Team, EntityType, Direction, Position, ResourceType, Environment, GameConstants, GameError, Controller
import random
import heapq
import array
import time
import math
import sys
from collections import deque, defaultdict
from typing import NamedTuple
from Awubot.Constants import Constants
from Awubot.Core import Core
from Awubot.Globals import Globals, Cache
from Awubot.Map import LocalMask, MapMask, TileInfo, Map
from Awubot.MoveManager import MoveManager
from Awubot.RobotPlayer import Entrypoint, Player
from Awubot.Unit import Unit
from Awubot.Util import Util
from Awubot.debug.Debug import Color, Debug
from Awubot.debug.Profiler import Profiler
from Awubot.explore.Explore import Explore
from Awubot.nav.DirectionPicker import DirectionPicker
from Awubot.nav.OmNom import OmNom


class BuilderState:
    UNKNOWN = 0
    EXPLORE = 1


class Builder(Unit):
    explore_target: Position
    state_map: dict
    core_pos: Position

    def __init__(self):
        super().__init__()
        Explore.init()

        self.state_map = {
            BuilderState.EXPLORE: self.state_explore
        }
        self.state = BuilderState.EXPLORE

        core_id = Globals.ct.get_tile_building_id(Globals.ct.get_position())
        self.core_pos = Globals.ct.get_position(core_id)


    def start_turn(self):
        super().start_turn()
        self.explore_target = Explore.get_target()

    def run_turn(self):
        self.state_map[self.state]()

    def end_turn(self):
        super().end_turn()

    def state_explore(self):
        target = Explore.get_target()
        Debug.line(target)


        # Profiler.start()
        # dist = GlobalBitmaskBfs.dists_from_pos(target)
        # Profiler.end("GlobalBitmaskBfs")

        # Profiler.start()
        # dist = GlobalBfs.dists_from_pos(target)
        # Profiler.end("GlobalBfs")

        Profiler.start()
        dist = FlatDijkstra.dists_from_pos(target)
        Profiler.end("FlatDijkstra")

        Profiler.start()
        dist = FastDijkstra.dists_from_pos(target)
        Profiler.end("FastDijkstra")

        Profiler.start()
        dist = Dijkstra.dists_from_pos(target)
        Profiler.end("Dijkstra")


        cur_pos = Globals.ct.get_position()

        # Build harvester if possible
        for d in Constants.DIRECTIONS:
            check_pos = cur_pos.add(d)
            if Globals.ct.can_build_harvester(check_pos):
                Globals.ct.build_harvester(check_pos)
                break

        # Rank directions by dist of neighbor cell
        candidates = []
        for d in Constants.DIRECTIONS:
            np = cur_pos.add(d)
            if Util.on_the_map(np):
                candidates.append((dist[np.x][np.y], d))
        candidates.sort(key=lambda e: e[0])

        # Try moving toward lowest dist, building road if blocked
        for nd, d in candidates:
            move_pos = cur_pos.add(d)

            if Globals.ct.can_move(d):
                Globals.ct.move(d)
                break

            if Globals.ct.can_build_road(move_pos):
                Globals.ct.build_road(move_pos)

                if Globals.ct.can_move(d):
                    Globals.ct.move(d)
                    break
