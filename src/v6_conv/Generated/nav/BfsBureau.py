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
from Awubot.Map import TileInfo, Map
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


class BfsBureau:
    dist_global: list[int]
    dist_bridge: list[int]


    @classmethod
    def init(cls):
        W, H = Map.W, Map.H

        dist = [1000001] * 3136  # all impassable

        row = [1000000] * H  # make passable
        for x in range(W):
            base = (x + 3) * 56 + 3
            dist[base:base + H] = row

        cls.dist_global = dist
        cls.dist_bridge = dist[:]


# ---===
    @classmethod
    def update(cls):
        tile_info = Map.tile_info

        for pos in Map.nearby_tiles:
            ti = tile_info[pos.x][pos.y]


            # normal pathing
            if (
                ti.env != Environment.WALL
                and not (ti.has_building and ti.entity_type not in Constants.PASSABLE_SET)
            ):
                cls.dist_global[((pos.x + 3) * 56 + (pos.y + 3))] = 1000000
            else:
                cls.dist_global[((pos.x + 3) * 56 + (pos.y + 3))] = 1000001

            # bridge
            if (
                ti.env == Environment.EMPTY and
                (
                    # no building unless ally road/core or marker
                    (not ti.has_building) or 
                    ((etype := ti.entity_type) == EntityType.MARKER) or
                    (ti.is_building_ally and (
                        etype == EntityType.ROAD or etype == EntityType.CORE))
                )
            ):
                cls.dist_bridge[((pos.x + 3) * 56 + (pos.y + 3))] = 1000000
            else:
                cls.dist_bridge[((pos.x + 3) * 56 + (pos.y + 3))] = 1000001
# ===---


# ---===
    @classmethod
    def dists_from_pos(cls, pos: Position):
        dist = cls.dist_global[:]

        si = (pos.x + 3) * 56 + (pos.y + 3)
        dist[si] = 0

        frontier = [si]
        d = 1
        while frontier:
            nxt = []
            _a = nxt.append
            for idx in frontier:
                ni = idx + -1
                if dist[ni] == 1000000:
                    dist[ni] = d
                    _a(ni)
                ni = idx + 55
                if dist[ni] == 1000000:
                    dist[ni] = d
                    _a(ni)
                ni = idx + 56
                if dist[ni] == 1000000:
                    dist[ni] = d
                    _a(ni)
                ni = idx + 57
                if dist[ni] == 1000000:
                    dist[ni] = d
                    _a(ni)
                ni = idx + 1
                if dist[ni] == 1000000:
                    dist[ni] = d
                    _a(ni)
                ni = idx + -55
                if dist[ni] == 1000000:
                    dist[ni] = d
                    _a(ni)
                ni = idx + -56
                if dist[ni] == 1000000:
                    dist[ni] = d
                    _a(ni)
                ni = idx + -57
                if dist[ni] == 1000000:
                    dist[ni] = d
                    _a(ni)
            frontier = nxt
            d += 1

        result = [[0] * (Map.H + 1) for _ in range(Map.W + 1)]
        for x in range(Map.W + 1):
            row = result[x]
            base = (x + 3) * 56 + 3
            for y in range(Map.H + 1):
                v = dist[base + y]
                row[y] = 1000000 if v >= 1000000 else v
        return result
# ===---


    @classmethod
    def find_bridge_route(cls, start: Position, core_pos_list: list[tuple[int, int]]):


        dist = cls.dist_bridge[:]
        first_hop = [None] * 3136

        si = (start.x + 3) * 56 + (start.y + 3)
        dist[si] = 0

        core_set = set()
        for cx, cy in core_pos_list:
            core_set.add((cx + 3) * 56 + (cy + 3))

        q = deque()
        _qa = q.append


        # ── Phase 1: conveyor mini-BFS (≤4 cardinal steps from start) ──
        conv_reached = []
        _cra = conv_reached.append

        # First cardinal step: first_hop = that adjacent tile
        conv_front = []
        _cfa = conv_front.append
        ni = si + 56
        if dist[ni] == 1000000:
            dist[ni] = -1
            first_hop[ni] = (start.x + 1, start.y + 0)
            _cfa(ni)
            _cra(ni)
        ni = si + -56
        if dist[ni] == 1000000:
            dist[ni] = -1
            first_hop[ni] = (start.x + -1, start.y + 0)
            _cfa(ni)
            _cra(ni)
        ni = si + 1
        if dist[ni] == 1000000:
            dist[ni] = -1
            first_hop[ni] = (start.x + 0, start.y + 1)
            _cfa(ni)
            _cra(ni)
        ni = si + -1
        if dist[ni] == 1000000:
            dist[ni] = -1
            first_hop[ni] = (start.x + 0, start.y + -1)
            _cfa(ni)
            _cra(ni)

        # Steps 2–4: propagate first_hop from parent
        conv_next = []
        _cna = conv_next.append
        for cidx in conv_front:
            _fh = first_hop[cidx]
            ni = cidx + 56
            if dist[ni] == 1000000:
                dist[ni] = -1
                first_hop[ni] = _fh
                _cna(ni)
                _cra(ni)
            ni = cidx + -56
            if dist[ni] == 1000000:
                dist[ni] = -1
                first_hop[ni] = _fh
                _cna(ni)
                _cra(ni)
            ni = cidx + 1
            if dist[ni] == 1000000:
                dist[ni] = -1
                first_hop[ni] = _fh
                _cna(ni)
                _cra(ni)
            ni = cidx + -1
            if dist[ni] == 1000000:
                dist[ni] = -1
                first_hop[ni] = _fh
                _cna(ni)
                _cra(ni)
        conv_front = conv_next
        conv_next = []
        _cna = conv_next.append
        for cidx in conv_front:
            _fh = first_hop[cidx]
            ni = cidx + 56
            if dist[ni] == 1000000:
                dist[ni] = -1
                first_hop[ni] = _fh
                _cna(ni)
                _cra(ni)
            ni = cidx + -56
            if dist[ni] == 1000000:
                dist[ni] = -1
                first_hop[ni] = _fh
                _cna(ni)
                _cra(ni)
            ni = cidx + 1
            if dist[ni] == 1000000:
                dist[ni] = -1
                first_hop[ni] = _fh
                _cna(ni)
                _cra(ni)
            ni = cidx + -1
            if dist[ni] == 1000000:
                dist[ni] = -1
                first_hop[ni] = _fh
                _cna(ni)
                _cra(ni)
        conv_front = conv_next
        conv_next = []
        _cna = conv_next.append
        for cidx in conv_front:
            _fh = first_hop[cidx]
            ni = cidx + 56
            if dist[ni] == 1000000:
                dist[ni] = -1
                first_hop[ni] = _fh
                _cna(ni)
                _cra(ni)
            ni = cidx + -56
            if dist[ni] == 1000000:
                dist[ni] = -1
                first_hop[ni] = _fh
                _cna(ni)
                _cra(ni)
            ni = cidx + 1
            if dist[ni] == 1000000:
                dist[ni] = -1
                first_hop[ni] = _fh
                _cna(ni)
                _cra(ni)
            ni = cidx + -1
            if dist[ni] == 1000000:
                dist[ni] = -1
                first_hop[ni] = _fh
                _cna(ni)
                _cra(ni)
        conv_front = conv_next

        # ── Phase 2: seed conveyors first (priority over bridges) ──
        for cidx in conv_reached:
            if dist[cidx] == -1:
                dist[cidx] = 1
                if cidx in core_set:
                    return 1, first_hop[cidx]
                _qa(cidx)

        # ── Phase 3: bridge seeds for tiles conveyors couldn't reach ──
        ni = si + 168
        if dist[ni] == 1000000:
            dist[ni] = 1
            first_hop[ni] = (start.x + 3, start.y + 0)
            if ni in core_set:
                return 1, first_hop[ni]
            _qa(ni)
        ni = si + -168
        if dist[ni] == 1000000:
            dist[ni] = 1
            first_hop[ni] = (start.x + -3, start.y + 0)
            if ni in core_set:
                return 1, first_hop[ni]
            _qa(ni)
        ni = si + 3
        if dist[ni] == 1000000:
            dist[ni] = 1
            first_hop[ni] = (start.x + 0, start.y + 3)
            if ni in core_set:
                return 1, first_hop[ni]
            _qa(ni)
        ni = si + -3
        if dist[ni] == 1000000:
            dist[ni] = 1
            first_hop[ni] = (start.x + 0, start.y + -3)
            if ni in core_set:
                return 1, first_hop[ni]
            _qa(ni)
        ni = si + 114
        if dist[ni] == 1000000:
            dist[ni] = 1
            first_hop[ni] = (start.x + 2, start.y + 2)
            if ni in core_set:
                return 1, first_hop[ni]
            _qa(ni)
        ni = si + 110
        if dist[ni] == 1000000:
            dist[ni] = 1
            first_hop[ni] = (start.x + 2, start.y + -2)
            if ni in core_set:
                return 1, first_hop[ni]
            _qa(ni)
        ni = si + -114
        if dist[ni] == 1000000:
            dist[ni] = 1
            first_hop[ni] = (start.x + -2, start.y + -2)
            if ni in core_set:
                return 1, first_hop[ni]
            _qa(ni)
        ni = si + -110
        if dist[ni] == 1000000:
            dist[ni] = 1
            first_hop[ni] = (start.x + -2, start.y + 2)
            if ni in core_set:
                return 1, first_hop[ni]
            _qa(ni)
        ni = si + 58
        if dist[ni] == 1000000:
            dist[ni] = 1
            first_hop[ni] = (start.x + 1, start.y + 2)
            if ni in core_set:
                return 1, first_hop[ni]
            _qa(ni)
        ni = si + 113
        if dist[ni] == 1000000:
            dist[ni] = 1
            first_hop[ni] = (start.x + 2, start.y + 1)
            if ni in core_set:
                return 1, first_hop[ni]
            _qa(ni)
        ni = si + 111
        if dist[ni] == 1000000:
            dist[ni] = 1
            first_hop[ni] = (start.x + 2, start.y + -1)
            if ni in core_set:
                return 1, first_hop[ni]
            _qa(ni)
        ni = si + 54
        if dist[ni] == 1000000:
            dist[ni] = 1
            first_hop[ni] = (start.x + 1, start.y + -2)
            if ni in core_set:
                return 1, first_hop[ni]
            _qa(ni)
        ni = si + -58
        if dist[ni] == 1000000:
            dist[ni] = 1
            first_hop[ni] = (start.x + -1, start.y + -2)
            if ni in core_set:
                return 1, first_hop[ni]
            _qa(ni)
        ni = si + -113
        if dist[ni] == 1000000:
            dist[ni] = 1
            first_hop[ni] = (start.x + -2, start.y + -1)
            if ni in core_set:
                return 1, first_hop[ni]
            _qa(ni)
        ni = si + -111
        if dist[ni] == 1000000:
            dist[ni] = 1
            first_hop[ni] = (start.x + -2, start.y + 1)
            if ni in core_set:
                return 1, first_hop[ni]
            _qa(ni)
        ni = si + -54
        if dist[ni] == 1000000:
            dist[ni] = 1
            first_hop[ni] = (start.x + -1, start.y + 2)
            if ni in core_set:
                return 1, first_hop[ni]
            _qa(ni)

        # ── Phase 4: main bridge BFS ──
        while q:
            idx = q.popleft()
            d = dist[idx] + 1
            fh = first_hop[idx]

            ni = idx + 168
            if dist[ni] == 1000000:
                dist[ni] = d
                first_hop[ni] = fh
                if ni in core_set:
                    return d, fh
                _qa(ni)
            ni = idx + -168
            if dist[ni] == 1000000:
                dist[ni] = d
                first_hop[ni] = fh
                if ni in core_set:
                    return d, fh
                _qa(ni)
            ni = idx + 3
            if dist[ni] == 1000000:
                dist[ni] = d
                first_hop[ni] = fh
                if ni in core_set:
                    return d, fh
                _qa(ni)
            ni = idx + -3
            if dist[ni] == 1000000:
                dist[ni] = d
                first_hop[ni] = fh
                if ni in core_set:
                    return d, fh
                _qa(ni)
            ni = idx + 114
            if dist[ni] == 1000000:
                dist[ni] = d
                first_hop[ni] = fh
                if ni in core_set:
                    return d, fh
                _qa(ni)
            ni = idx + 110
            if dist[ni] == 1000000:
                dist[ni] = d
                first_hop[ni] = fh
                if ni in core_set:
                    return d, fh
                _qa(ni)
            ni = idx + -114
            if dist[ni] == 1000000:
                dist[ni] = d
                first_hop[ni] = fh
                if ni in core_set:
                    return d, fh
                _qa(ni)
            ni = idx + -110
            if dist[ni] == 1000000:
                dist[ni] = d
                first_hop[ni] = fh
                if ni in core_set:
                    return d, fh
                _qa(ni)

        return 1000000, None