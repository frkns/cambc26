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
from Generated.Comms import Comms
from Generated.MarketMaker import MarketMaker
from Generated.RobotPlayer import Entrypoint, Player
from Generated.Unit import Unit
from Generated.builder.BuildManager import BuildManager
from Generated.builder.Builder import BuilderState, Builder
from Generated.builder.OreExecutive import OreExecutive
from Generated.builder.OrePositionPicker import OrePositionPicker
from Generated.builder.RouteToCore import RouteToCore
from Generated.builder.SuicideExecutor import SuicideExecutor
from Generated.core.Core import Core
from Generated.debug.Debug import Color, Debug
from Generated.explore.Explore import Explore
from Generated.heal.HealExecutor import HealExecutor
from Generated.map.DarkForest import TreeNode, DarkForest
from Generated.map.Map import TileInfo, Map
from Generated.map.Symmetry import Sym, Symmetry
from Generated.nav.BfsBureau import BfsBureau
from Generated.nav.DirectionPicker import DirectionPicker
from Generated.nav.Pathfinder import Pathfinder
# ===--- IMPORT




class BfsBureau:
    weight: list[int]
    dist_bridge: list[int]
    passable_int: int
    bridge_passable_int: int
    STRIDE: int
    BRIDGE_STRIDE: int

    @classmethod
    def init(cls):
        W, H = Map.W, Map.H

        dist = [1000001] * 3136
        weight = [1000000] * 3136

        row_inf = [1000000] * H
        row_1 = [1] * H
        for x in range(W):
            base = (x + 3) * 56 + 3
            dist[base:base + H] = row_inf
            weight[base:base + H] = row_1

        cls.dist_bridge = dist
        cls.weight = weight

        S = H + 1
        cls.STRIDE = S
        col_mask = (1 << H) - 1
        p = 0
        for x in range(W):
            p |= col_mask << (x * S)
        cls.passable_int = p

        BS = H + 3
        cls.BRIDGE_STRIDE = BS
        bp = 0
        for x in range(W):
            bp |= col_mask << (x * BS)
        cls.bridge_passable_int = bp


# ---===
    @classmethod
    def update(cls):
        tile_info = Map.tile_info
        _w = cls.weight
        _S = cls.STRIDE
        _BS = cls.BRIDGE_STRIDE

        for pos in chain(Map.nearby_tiles, Map.new_syms):
            x, y = pos.x, pos.y
            ti = tile_info[x][y]

            idx = ((pos.x + 3) * 56 + (pos.y + 3))
            _bit_mask = 1 << (x * _S + y)
            _bridge_bit = 1 << (x * _BS + y)

            if ti.env != Environment.WALL:
                if ti.easily_passable:
                    _w[idx] = 1
                    cls.passable_int |= _bit_mask
                elif ti.has_building:
                    _w[idx] = 1000000
                    cls.passable_int &= ~_bit_mask
                else:
                    _w[idx] = 2
                    cls.passable_int |= _bit_mask
            else:
                _w[idx] = 1000000
                cls.passable_int &= ~_bit_mask

            if (
                ti.env == Environment.EMPTY and
                (
                    (not ti.has_building) or
                    ((etype := ti.entity_type) == EntityType.MARKER) or
                    (ti.is_building_ally and (
                        etype == EntityType.ROAD or etype == EntityType.CORE))
                )
            ):
                cls.dist_bridge[idx] = 1000000
                cls.bridge_passable_int |= _bridge_bit
            else:
                cls.dist_bridge[idx] = 1000001
                cls.bridge_passable_int &= ~_bridge_bit
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

    # BAD! THE FIRST MOVE IS WEIRD!






















    # STILL DOESNT WORK, it doesn't match works behavior.
























    # works. but slow
# ---===
    @classmethod
    def find_bridge_route(cls, start: Position, sink_set: set[int], max_iter: int = 1000):


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

        it = 0
        while q and (it := it + 1) <= max_iter:
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

    # outward depth-limited dijkstra + bitmask bfs
    # ---===
    @classmethod
    def find_route(cls, start: Position, target: Position,
                   ban_target: bool = False) -> tuple[int, Direction | None]:

        sx, sy = start.x, start.y
        _tx, _ty = target.x, target.y

        _w = cls.weight
        _S = cls.STRIDE

        si = ((sx + 3) * 56 + (sy + 3))
        ti = ((_tx + 3) * 56 + (_ty + 3))

        _D = (Direction.NORTH, Direction.NORTHEAST, Direction.EAST, Direction.SOUTHEAST, Direction.SOUTH, Direction.SOUTHWEST, Direction.WEST, Direction.NORTHWEST)

        # ── Same-tile shortcuts ──
        if si == ti:
            if not ban_target:
                return 0, Direction.CENTRE
            ni = si + -1
            if _w[ni] < 1000000 and MoveManager.can_fill_move(Direction.NORTH):
                return 1, Direction.NORTH
            ni = si + 55
            if _w[ni] < 1000000 and MoveManager.can_fill_move(Direction.NORTHEAST):
                return 1, Direction.NORTHEAST
            ni = si + 56
            if _w[ni] < 1000000 and MoveManager.can_fill_move(Direction.EAST):
                return 1, Direction.EAST
            ni = si + 57
            if _w[ni] < 1000000 and MoveManager.can_fill_move(Direction.SOUTHEAST):
                return 1, Direction.SOUTHEAST
            ni = si + 1
            if _w[ni] < 1000000 and MoveManager.can_fill_move(Direction.SOUTH):
                return 1, Direction.SOUTH
            ni = si + -55
            if _w[ni] < 1000000 and MoveManager.can_fill_move(Direction.SOUTHWEST):
                return 1, Direction.SOUTHWEST
            ni = si + -56
            if _w[ni] < 1000000 and MoveManager.can_fill_move(Direction.WEST):
                return 1, Direction.WEST
            ni = si + -57
            if _w[ni] < 1000000 and MoveManager.can_fill_move(Direction.NORTHWEST):
                return 1, Direction.NORTHWEST
            return 1000000, None

        if ban_target:
            _d = si - ti
            _ad = _d if _d >= 0 else -_d
            if _ad == 1 or _ad == 55 or _ad == 56 or _ad == 57:
                return 0, Direction.CENTRE

        _save = _w[ti]
        _w[ti] = 1

        # we do this because try...finally is banned by engine

        # ── Phase 1: weighted Dijkstra up to 8 ──
        dist = [1000000] * 3136
        fhd  = [0]       * 3136
        dist[si] = 0

        heap  = []
        _hp   = heapq.heappush
        _hpop = heapq.heappop

        _settled = [si]
        _sa = _settled.append

        ni = si + -1
        if _w[ni] < 1000000 and MoveManager.can_fill_move(Direction.NORTH):
            w = _w[ni]
            dist[ni] = w
            fhd[ni]  = 0
            if ni == ti:
                _w[ti] = _save; Profiler.end("""BfsBureau.find_route[bfs]""")
                return w, Direction.NORTH
            _hp(heap, (w, ni))
        ni = si + 55
        if _w[ni] < 1000000 and MoveManager.can_fill_move(Direction.NORTHEAST):
            w = _w[ni]
            dist[ni] = w
            fhd[ni]  = 1
            if ni == ti:
                _w[ti] = _save; Profiler.end("""BfsBureau.find_route[bfs]""")
                return w, Direction.NORTHEAST
            _hp(heap, (w, ni))
        ni = si + 56
        if _w[ni] < 1000000 and MoveManager.can_fill_move(Direction.EAST):
            w = _w[ni]
            dist[ni] = w
            fhd[ni]  = 2
            if ni == ti:
                _w[ti] = _save; Profiler.end("""BfsBureau.find_route[bfs]""")
                return w, Direction.EAST
            _hp(heap, (w, ni))
        ni = si + 57
        if _w[ni] < 1000000 and MoveManager.can_fill_move(Direction.SOUTHEAST):
            w = _w[ni]
            dist[ni] = w
            fhd[ni]  = 3
            if ni == ti:
                _w[ti] = _save; Profiler.end("""BfsBureau.find_route[bfs]""")
                return w, Direction.SOUTHEAST
            _hp(heap, (w, ni))
        ni = si + 1
        if _w[ni] < 1000000 and MoveManager.can_fill_move(Direction.SOUTH):
            w = _w[ni]
            dist[ni] = w
            fhd[ni]  = 4
            if ni == ti:
                _w[ti] = _save; Profiler.end("""BfsBureau.find_route[bfs]""")
                return w, Direction.SOUTH
            _hp(heap, (w, ni))
        ni = si + -55
        if _w[ni] < 1000000 and MoveManager.can_fill_move(Direction.SOUTHWEST):
            w = _w[ni]
            dist[ni] = w
            fhd[ni]  = 5
            if ni == ti:
                _w[ti] = _save; Profiler.end("""BfsBureau.find_route[bfs]""")
                return w, Direction.SOUTHWEST
            _hp(heap, (w, ni))
        ni = si + -56
        if _w[ni] < 1000000 and MoveManager.can_fill_move(Direction.WEST):
            w = _w[ni]
            dist[ni] = w
            fhd[ni]  = 6
            if ni == ti:
                _w[ti] = _save; Profiler.end("""BfsBureau.find_route[bfs]""")
                return w, Direction.WEST
            _hp(heap, (w, ni))
        ni = si + -57
        if _w[ni] < 1000000 and MoveManager.can_fill_move(Direction.NORTHWEST):
            w = _w[ni]
            dist[ni] = w
            fhd[ni]  = 7
            if ni == ti:
                _w[ti] = _save; Profiler.end("""BfsBureau.find_route[bfs]""")
                return w, Direction.NORTHWEST
            _hp(heap, (w, ni))

        phase2_seeds = []
        _p2a = phase2_seeds.append

        while heap:
            d, idx = _hpop(heap)
            if d > dist[idx]:
                continue

            _sa(idx)

            if d >= 8:
                _p2a(idx)
                while heap:
                    _dd, _idx = _hpop(heap)
                    if _dd == dist[_idx]:
                        _sa(_idx)
                        _p2a(_idx)
                break

            _fh = fhd[idx]
            ni = idx + -1
            w  = _w[ni]
            if w < 1000000:
                nd = d + w
                if nd < dist[ni]:
                    dist[ni] = nd
                    fhd[ni]  = _fh
                    if ni == ti:
                        _w[ti] = _save; Profiler.end("""BfsBureau.find_route[bfs]""")
                        return nd, _D[_fh]
                    _hp(heap, (nd, ni))
            ni = idx + 55
            w  = _w[ni]
            if w < 1000000:
                nd = d + w
                if nd < dist[ni]:
                    dist[ni] = nd
                    fhd[ni]  = _fh
                    if ni == ti:
                        _w[ti] = _save; Profiler.end("""BfsBureau.find_route[bfs]""")
                        return nd, _D[_fh]
                    _hp(heap, (nd, ni))
            ni = idx + 56
            w  = _w[ni]
            if w < 1000000:
                nd = d + w
                if nd < dist[ni]:
                    dist[ni] = nd
                    fhd[ni]  = _fh
                    if ni == ti:
                        _w[ti] = _save; Profiler.end("""BfsBureau.find_route[bfs]""")
                        return nd, _D[_fh]
                    _hp(heap, (nd, ni))
            ni = idx + 57
            w  = _w[ni]
            if w < 1000000:
                nd = d + w
                if nd < dist[ni]:
                    dist[ni] = nd
                    fhd[ni]  = _fh
                    if ni == ti:
                        _w[ti] = _save; Profiler.end("""BfsBureau.find_route[bfs]""")
                        return nd, _D[_fh]
                    _hp(heap, (nd, ni))
            ni = idx + 1
            w  = _w[ni]
            if w < 1000000:
                nd = d + w
                if nd < dist[ni]:
                    dist[ni] = nd
                    fhd[ni]  = _fh
                    if ni == ti:
                        _w[ti] = _save; Profiler.end("""BfsBureau.find_route[bfs]""")
                        return nd, _D[_fh]
                    _hp(heap, (nd, ni))
            ni = idx + -55
            w  = _w[ni]
            if w < 1000000:
                nd = d + w
                if nd < dist[ni]:
                    dist[ni] = nd
                    fhd[ni]  = _fh
                    if ni == ti:
                        _w[ti] = _save; Profiler.end("""BfsBureau.find_route[bfs]""")
                        return nd, _D[_fh]
                    _hp(heap, (nd, ni))
            ni = idx + -56
            w  = _w[ni]
            if w < 1000000:
                nd = d + w
                if nd < dist[ni]:
                    dist[ni] = nd
                    fhd[ni]  = _fh
                    if ni == ti:
                        _w[ti] = _save; Profiler.end("""BfsBureau.find_route[bfs]""")
                        return nd, _D[_fh]
                    _hp(heap, (nd, ni))
            ni = idx + -57
            w  = _w[ni]
            if w < 1000000:
                nd = d + w
                if nd < dist[ni]:
                    dist[ni] = nd
                    fhd[ni]  = _fh
                    if ni == ti:
                        _w[ti] = _save; Profiler.end("""BfsBureau.find_route[bfs]""")
                        return nd, _D[_fh]
                    _hp(heap, (nd, ni))

        if not phase2_seeds:
            _w[ti] = _save; Profiler.end("""BfsBureau.find_route[bfs]""")
            return 1000000, None

        # ── Phase 2: bitmask BFS from Dijkstra frontier ──
        Profiler.start()
        _tb = _tx * _S + _ty
        _tm = 1 << _tb
        _uc = cls.passable_int | _tm

        _settled_bits = 0
        for _ci in _settled:
            _cx = _ci // 56 - 3
            _cy = _ci % 56 - 3
            _settled_bits |= 1 << (_cx * _S + _cy)
        _uc &= ~_settled_bits

        _fh0 = 0
        _md0 = 1000000
        _fh1 = 0
        _md1 = 1000000
        _fh2 = 0
        _md2 = 1000000
        _fh3 = 0
        _md3 = 1000000
        _fh4 = 0
        _md4 = 1000000
        _fh5 = 0
        _md5 = 1000000
        _fh6 = 0
        _md6 = 1000000
        _fh7 = 0
        _md7 = 1000000

        for _ci in phase2_seeds:
            _cx = _ci // 56 - 3
            _cy = _ci % 56 - 3
            _di = fhd[_ci]
            _bit = 1 << (_cx * _S + _cy)
            if _di == 0:
                _fh0 |= _bit
                if dist[_ci] < _md0:
                    _md0 = dist[_ci]
            elif _di == 1:
                _fh1 |= _bit
                if dist[_ci] < _md1:
                    _md1 = dist[_ci]
            elif _di == 2:
                _fh2 |= _bit
                if dist[_ci] < _md2:
                    _md2 = dist[_ci]
            elif _di == 3:
                _fh3 |= _bit
                if dist[_ci] < _md3:
                    _md3 = dist[_ci]
            elif _di == 4:
                _fh4 |= _bit
                if dist[_ci] < _md4:
                    _md4 = dist[_ci]
            elif _di == 5:
                _fh5 |= _bit
                if dist[_ci] < _md5:
                    _md5 = dist[_ci]
            elif _di == 6:
                _fh6 |= _bit
                if dist[_ci] < _md6:
                    _md6 = dist[_ci]
            elif _di == 7:
                _fh7 |= _bit
                if dist[_ci] < _md7:
                    _md7 = dist[_ci]

        _bfs_d = 0
        while True:
            _any = False

            _f = _fh0
            if _f:
                _v = _f | (_f << 1) | (_f >> 1)
                _e = (_v | (_v << _S) | (_v >> _S)) & _uc
                if _e:
                    _fh0 = _e
                    _uc ^= _e
                    _any = True
                    if _e & _tm:
                        _w[ti] = _save; Profiler.end("""BfsBureau.find_route[bfs]""")
                        return _md0 + _bfs_d + 1, _D[0]
                else:
                    _fh0 = 0
            _f = _fh1
            if _f:
                _v = _f | (_f << 1) | (_f >> 1)
                _e = (_v | (_v << _S) | (_v >> _S)) & _uc
                if _e:
                    _fh1 = _e
                    _uc ^= _e
                    _any = True
                    if _e & _tm:
                        _w[ti] = _save; Profiler.end("""BfsBureau.find_route[bfs]""")
                        return _md1 + _bfs_d + 1, _D[1]
                else:
                    _fh1 = 0
            _f = _fh2
            if _f:
                _v = _f | (_f << 1) | (_f >> 1)
                _e = (_v | (_v << _S) | (_v >> _S)) & _uc
                if _e:
                    _fh2 = _e
                    _uc ^= _e
                    _any = True
                    if _e & _tm:
                        _w[ti] = _save; Profiler.end("""BfsBureau.find_route[bfs]""")
                        return _md2 + _bfs_d + 1, _D[2]
                else:
                    _fh2 = 0
            _f = _fh3
            if _f:
                _v = _f | (_f << 1) | (_f >> 1)
                _e = (_v | (_v << _S) | (_v >> _S)) & _uc
                if _e:
                    _fh3 = _e
                    _uc ^= _e
                    _any = True
                    if _e & _tm:
                        _w[ti] = _save; Profiler.end("""BfsBureau.find_route[bfs]""")
                        return _md3 + _bfs_d + 1, _D[3]
                else:
                    _fh3 = 0
            _f = _fh4
            if _f:
                _v = _f | (_f << 1) | (_f >> 1)
                _e = (_v | (_v << _S) | (_v >> _S)) & _uc
                if _e:
                    _fh4 = _e
                    _uc ^= _e
                    _any = True
                    if _e & _tm:
                        _w[ti] = _save; Profiler.end("""BfsBureau.find_route[bfs]""")
                        return _md4 + _bfs_d + 1, _D[4]
                else:
                    _fh4 = 0
            _f = _fh5
            if _f:
                _v = _f | (_f << 1) | (_f >> 1)
                _e = (_v | (_v << _S) | (_v >> _S)) & _uc
                if _e:
                    _fh5 = _e
                    _uc ^= _e
                    _any = True
                    if _e & _tm:
                        _w[ti] = _save; Profiler.end("""BfsBureau.find_route[bfs]""")
                        return _md5 + _bfs_d + 1, _D[5]
                else:
                    _fh5 = 0
            _f = _fh6
            if _f:
                _v = _f | (_f << 1) | (_f >> 1)
                _e = (_v | (_v << _S) | (_v >> _S)) & _uc
                if _e:
                    _fh6 = _e
                    _uc ^= _e
                    _any = True
                    if _e & _tm:
                        _w[ti] = _save; Profiler.end("""BfsBureau.find_route[bfs]""")
                        return _md6 + _bfs_d + 1, _D[6]
                else:
                    _fh6 = 0
            _f = _fh7
            if _f:
                _v = _f | (_f << 1) | (_f >> 1)
                _e = (_v | (_v << _S) | (_v >> _S)) & _uc
                if _e:
                    _fh7 = _e
                    _uc ^= _e
                    _any = True
                    if _e & _tm:
                        _w[ti] = _save; Profiler.end("""BfsBureau.find_route[bfs]""")
                        return _md7 + _bfs_d + 1, _D[7]
                else:
                    _fh7 = 0

            if not _any:
                break
            _bfs_d += 1

        _w[ti] = _save; Profiler.end("""BfsBureau.find_route[bfs]""")
        return 1000000, None
    # ===---