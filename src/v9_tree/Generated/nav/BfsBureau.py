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
from Awubot.explore.Explore import Explore
from Generated.MarketMaker import MarketMaker
from Generated.RobotPlayer import Entrypoint, Player
from Generated.Unit import Unit
from Generated.build.BuildManager import BuildManager
from Generated.build.Builder import BuilderState, Builder
from Generated.build.OreExecutive import OreExecutive
from Generated.build.OrePositionPicker import OrePositionPicker
from Generated.build.RouteToCore import RouteToCore
from Generated.build.SuicideExecutor import SuicideExecutor
from Generated.core.Core import Core
from Generated.debug.Debug import Color, Debug
from Generated.heal.HealExecutor import HealExecutor
from Generated.map.DarkForest import TreeNode, DarkForest
from Generated.map.Map import TileInfo, Map
from Generated.map.Symmetry import Sym, Symmetry
from Generated.nav.BfsBureau import BfsBureau
from Generated.nav.DirectionPicker import DirectionPicker
from Generated.nav.Pathfinder import Pathfinder



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

        for pos in chain(Map.nearby_tiles, Map.new_syms):
            ti = tile_info[pos.x][pos.y]


            # normal pathing
            if (
                ti.env != Environment.WALL
                and (not ti.has_building or ti.easily_passable)
            ):                            # ^^^^^^^^^^^^^^^^^^ will be short-circuited for sym
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

    # deprecate soon?
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


# ---===
    @classmethod
    def find_bridge_route(cls, start: Position, sink_set: set[int]):


        dist = cls.dist_bridge[:]
        first_hop = [None] * 3136

        sx, sy = start.x, start.y
        si = ((sx + 3) * 56 + (sy + 3))
        dist[si] = 0

        # sink nodes are destinations, not transit — make them visible to BFS
        # we return immediately on first hit, so they're never traversed through
        for s in sink_set:
            if dist[s] == 1000001:  # redundant check?
                dist[s] = 1000000

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
            first_hop[ni] = (sx +1, sy )
            _cfa(ni)
            _cra(ni)
        ni = si + -56
        if dist[ni] == 1000000:
            dist[ni] = -1
            first_hop[ni] = (sx -1, sy )
            _cfa(ni)
            _cra(ni)
        ni = si + 1
        if dist[ni] == 1000000:
            dist[ni] = -1
            first_hop[ni] = (sx , sy +1)
            _cfa(ni)
            _cra(ni)
        ni = si + -1
        if dist[ni] == 1000000:
            dist[ni] = -1
            first_hop[ni] = (sx , sy -1)
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
                if cidx in sink_set:
                    return 1, first_hop[cidx]
                _qa(cidx)

        # ── Phase 3: bridge seeds for tiles conveyors couldn't reach ──
        ni = si + 168
        if dist[ni] == 1000000:
            dist[ni] = 1
            first_hop[ni] = (sx +3, sy )
            if ni in sink_set:
                return 1, first_hop[ni]
            _qa(ni)
        ni = si + -168
        if dist[ni] == 1000000:
            dist[ni] = 1
            first_hop[ni] = (sx -3, sy )
            if ni in sink_set:
                return 1, first_hop[ni]
            _qa(ni)
        ni = si + 3
        if dist[ni] == 1000000:
            dist[ni] = 1
            first_hop[ni] = (sx , sy +3)
            if ni in sink_set:
                return 1, first_hop[ni]
            _qa(ni)
        ni = si + -3
        if dist[ni] == 1000000:
            dist[ni] = 1
            first_hop[ni] = (sx , sy -3)
            if ni in sink_set:
                return 1, first_hop[ni]
            _qa(ni)
        ni = si + 114
        if dist[ni] == 1000000:
            dist[ni] = 1
            first_hop[ni] = (sx +2, sy +2)
            if ni in sink_set:
                return 1, first_hop[ni]
            _qa(ni)
        ni = si + 110
        if dist[ni] == 1000000:
            dist[ni] = 1
            first_hop[ni] = (sx +2, sy -2)
            if ni in sink_set:
                return 1, first_hop[ni]
            _qa(ni)
        ni = si + -114
        if dist[ni] == 1000000:
            dist[ni] = 1
            first_hop[ni] = (sx -2, sy -2)
            if ni in sink_set:
                return 1, first_hop[ni]
            _qa(ni)
        ni = si + -110
        if dist[ni] == 1000000:
            dist[ni] = 1
            first_hop[ni] = (sx -2, sy +2)
            if ni in sink_set:
                return 1, first_hop[ni]
            _qa(ni)
        ni = si + 58
        if dist[ni] == 1000000:
            dist[ni] = 1
            first_hop[ni] = (sx +1, sy +2)
            if ni in sink_set:
                return 1, first_hop[ni]
            _qa(ni)
        ni = si + 113
        if dist[ni] == 1000000:
            dist[ni] = 1
            first_hop[ni] = (sx +2, sy +1)
            if ni in sink_set:
                return 1, first_hop[ni]
            _qa(ni)
        ni = si + 111
        if dist[ni] == 1000000:
            dist[ni] = 1
            first_hop[ni] = (sx +2, sy -1)
            if ni in sink_set:
                return 1, first_hop[ni]
            _qa(ni)
        ni = si + 54
        if dist[ni] == 1000000:
            dist[ni] = 1
            first_hop[ni] = (sx +1, sy -2)
            if ni in sink_set:
                return 1, first_hop[ni]
            _qa(ni)
        ni = si + -58
        if dist[ni] == 1000000:
            dist[ni] = 1
            first_hop[ni] = (sx -1, sy -2)
            if ni in sink_set:
                return 1, first_hop[ni]
            _qa(ni)
        ni = si + -113
        if dist[ni] == 1000000:
            dist[ni] = 1
            first_hop[ni] = (sx -2, sy -1)
            if ni in sink_set:
                return 1, first_hop[ni]
            _qa(ni)
        ni = si + -111
        if dist[ni] == 1000000:
            dist[ni] = 1
            first_hop[ni] = (sx -2, sy +1)
            if ni in sink_set:
                return 1, first_hop[ni]
            _qa(ni)
        ni = si + -54
        if dist[ni] == 1000000:
            dist[ni] = 1
            first_hop[ni] = (sx -1, sy +2)
            if ni in sink_set:
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
                if ni in sink_set:
                    return d, fh
                _qa(ni)
            ni = idx + -168
            if dist[ni] == 1000000:
                dist[ni] = d
                first_hop[ni] = fh
                if ni in sink_set:
                    return d, fh
                _qa(ni)
            ni = idx + 3
            if dist[ni] == 1000000:
                dist[ni] = d
                first_hop[ni] = fh
                if ni in sink_set:
                    return d, fh
                _qa(ni)
            ni = idx + -3
            if dist[ni] == 1000000:
                dist[ni] = d
                first_hop[ni] = fh
                if ni in sink_set:
                    return d, fh
                _qa(ni)
            ni = idx + 114
            if dist[ni] == 1000000:
                dist[ni] = d
                first_hop[ni] = fh
                if ni in sink_set:
                    return d, fh
                _qa(ni)
            ni = idx + 110
            if dist[ni] == 1000000:
                dist[ni] = d
                first_hop[ni] = fh
                if ni in sink_set:
                    return d, fh
                _qa(ni)
            ni = idx + -114
            if dist[ni] == 1000000:
                dist[ni] = d
                first_hop[ni] = fh
                if ni in sink_set:
                    return d, fh
                _qa(ni)
            ni = idx + -110
            if dist[ni] == 1000000:
                dist[ni] = d
                first_hop[ni] = fh
                if ni in sink_set:
                    return d, fh
                _qa(ni)

        return 1000000, None
# ===---
