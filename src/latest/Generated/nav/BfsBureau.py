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
from Awubot.Globals import Globals
from Awubot.MoveManager import MoveManager
from Awubot.Util import Util
from Generated.Constants import Constants
from Generated.MarketMaker import MarketMaker
from Generated.RobotPlayer import Entrypoint, Player
from Generated.bbot.Attacker import Attacker
from Generated.bbot.Builder import Builder
from Generated.bbot.HarvesterAdjacent import AdjacentInfo, HarvesterAdjacent
from Generated.bbot.HealExecutor import HealExecutor
from Generated.bbot.HealTargeter import HealTargetInfo, HealTargeter
from Generated.bbot.SentinelDirectionPicker import SentinelDirectionInfo, SentinelDirectionPicker
from Generated.bbot.States import StateBuildHarvester, StateBuildHarvesterAx, StateAttackTransporter, StateRoute, StateMoveTo, StateBuildTurret
from Generated.bbot.VisionTracker import TransporterInfo, ConnectManager, BotInfo, VisionTracker
from Generated.build.BuildManager import BuildManager
from Generated.build.OreExecutive import OreExecutive
from Generated.build.OrePositionPicker import OrePositionPicker
from Generated.build.RouteToCore import RouteToCore
from Generated.build.SuicideExecutor import SuicideExecutor
from Generated.comms.Comms import Comms
from Generated.comms.Marker import Marker
from Generated.comms.MarkerPositionPicker import MarkerPositionPicker
from Generated.core.Core import Core
from Generated.core.CoreHistory import CoreHistory
from Generated.core.SpawnManager import SpawnManager
from Generated.debug.Debug import Color, Debug
from Generated.debug.Profiler import Profiler
from Generated.explore.Explore import Explore
from Generated.map.DarkForest import TreeNode, DarkForest
from Generated.map.Map import TileInfo, Map
from Generated.map.Symmetry import Sym, Symmetry
from Generated.nav.BfsBureau import BfsBureau
from Generated.nav.Pathfinder import Pathfinder
from Generated.sentinel.Sentinel import Sentinel
from Generated.sentinel.SentinelSupervisor import SentinelTargetInfo, SentinelSupervisor
from Generated.units.Unit import Unit
# ===--- IMPORT




class BfsBureau:
    weight: list[int]
    now_weight: list[int]  # copied from weight every turn
    dist_bridge: list[int]

    # bitmask
    passable_int: int
    now_passable_int: int
    enemy_launcher: int = 0
    STRIDE: int

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


# ---===
    @classmethod
    def update(cls):
        tile_info = Map.tile_info
        weight = cls.weight
        stride = cls.STRIDE
        ct = Globals.ct


        # update persistent
        for pos, x, y, idx, ti in Map.proc_nearby_tiles:
            bit = 1 << (x * stride + y)

            if ti.env != Environment.WALL:
                if ti.easily_passable:
                    weight[idx] = 1
                    cls.passable_int |= bit
                elif ti.has_building:
                    weight[idx] = 1000000
                    cls.passable_int &= ~bit
                else:
                    weight[idx] = 2
                    cls.passable_int |= bit
            else:
                weight[idx] = 1000000
                cls.passable_int &= ~bit

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
            else:
                cls.dist_bridge[idx] = 1000001

        cls.now_weight = weight.copy()
        now_weight = cls.now_weight
        cls.now_passable_int = cls.passable_int

        # remove enemy launchers
        wide = cls.enemy_launcher | (cls.enemy_launcher << 1) | (cls.enemy_launcher >> 1)
        expanded = wide | (wide >> stride) | (wide << stride)
        cls.now_passable_int &= ~expanded
# ===---

    # incremental
                        
    @classmethod
    def add_enemy_sentinel(cls, pos, ti):
        for pos in Globals.ct.get_attackable_tiles_from(pos, ti.turret_direction, ti.entity_type):
            cls.weight[(((pos.x) + 3) * 56 + ((pos.y) + 3))] += 2

    @classmethod
    def remove_enemy_sentinel(cls, pos, ti):
        for pos in Globals.ct.get_attackable_tiles_from(pos, ti.turret_direction, ti.entity_type):
            cls.weight[(((pos.x) + 3) * 56 + ((pos.y) + 3))] -= 2

    @classmethod
    def add_enemy_launcher(cls, idx):
        bit = 1 << (x * stride + y)
        cls.enemy_launcher |= bit
        cls.weight[idx + -1] += 1000000
        cls.weight[idx + 55] += 1000000
        cls.weight[idx + 56] += 1000000
        cls.weight[idx + 57] += 1000000
        cls.weight[idx + 1] += 1000000
        cls.weight[idx + -55] += 1000000
        cls.weight[idx + -56] += 1000000
        cls.weight[idx + -57] += 1000000

    @classmethod
    def remove_enemy_launcher(cls, idx):
        bit = 1 << (x * stride + y)
        cls.enemy_launcher &= ~bit
        cls.weight[idx + -1] -= 1000000
        cls.weight[idx + 55] -= 1000000
        cls.weight[idx + 56] -= 1000000
        cls.weight[idx + 57] -= 1000000
        cls.weight[idx + 1] -= 1000000
        cls.weight[idx + -55] -= 1000000
        cls.weight[idx + -56] -= 1000000
        cls.weight[idx + -57] -= 1000000


    # works. but slow
# ---===
    @classmethod
    def find_bridge_route(cls, start: Position, sink_set: set[int], max_iter: int = 1000):


        dist = cls.dist_bridge[:]
        first_hop = [None] * 3136

        sx, sy = start.x, start.y
        si = (((sx) + 3) * 56 + ((sy) + 3))
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
                   ban_target: bool = False,
                   center_weight: int = 1) -> tuple[int, Direction | None]:

        sx, sy = start.x, start.y
        _tx, _ty = target.x, target.y

        weight = cls.now_weight
        stride = cls.STRIDE

        si = (((sx) + 3) * 56 + ((sy) + 3))
        ti = (((_tx) + 3) * 56 + ((_ty) + 3))

        _D = (Direction.NORTH, Direction.NORTHEAST, Direction.EAST, Direction.SOUTHEAST, Direction.SOUTH, Direction.SOUTHWEST, Direction.WEST, Direction.NORTHWEST)

        # ── Same-tile: CENTRE competes with neighbors ──
        if si == ti:
            if ban_target:
                _best_c = 1000000
                _best_d = None
            else:
                _best_c = center_weight
                _best_d = Direction.CENTRE if center_weight < 1000000 else None
            ni = si + -1
            w = weight[ni]
            if w < _best_c and MoveManager.can_fill_move(Direction.NORTH):
                _best_c = w
                _best_d = Direction.NORTH
            ni = si + 55
            w = weight[ni]
            if w < _best_c and MoveManager.can_fill_move(Direction.NORTHEAST):
                _best_c = w
                _best_d = Direction.NORTHEAST
            ni = si + 56
            w = weight[ni]
            if w < _best_c and MoveManager.can_fill_move(Direction.EAST):
                _best_c = w
                _best_d = Direction.EAST
            ni = si + 57
            w = weight[ni]
            if w < _best_c and MoveManager.can_fill_move(Direction.SOUTHEAST):
                _best_c = w
                _best_d = Direction.SOUTHEAST
            ni = si + 1
            w = weight[ni]
            if w < _best_c and MoveManager.can_fill_move(Direction.SOUTH):
                _best_c = w
                _best_d = Direction.SOUTH
            ni = si + -55
            w = weight[ni]
            if w < _best_c and MoveManager.can_fill_move(Direction.SOUTHWEST):
                _best_c = w
                _best_d = Direction.SOUTHWEST
            ni = si + -56
            w = weight[ni]
            if w < _best_c and MoveManager.can_fill_move(Direction.WEST):
                _best_c = w
                _best_d = Direction.WEST
            ni = si + -57
            w = weight[ni]
            if w < _best_c and MoveManager.can_fill_move(Direction.NORTHWEST):
                _best_c = w
                _best_d = Direction.NORTHWEST
            if _best_d is not None:
                return _best_c, _best_d
            return 1000000, None

        # ── Adjacent to banned target: CENTRE competes, but ti is excluded ──
        if ban_target:
            _d = si - ti
            _ad = _d if _d >= 0 else -_d
            if _ad == 1 or _ad == 55 or _ad == 56 or _ad == 57:
                _best_c = center_weight
                _best_d = Direction.CENTRE if center_weight < 1000000 else None
                ni = si + -1
                if ni != ti:
                    w = weight[ni]
                    if w < _best_c and MoveManager.can_fill_move(Direction.NORTH):
                        _best_c = w
                        _best_d = Direction.NORTH
                ni = si + 55
                if ni != ti:
                    w = weight[ni]
                    if w < _best_c and MoveManager.can_fill_move(Direction.NORTHEAST):
                        _best_c = w
                        _best_d = Direction.NORTHEAST
                ni = si + 56
                if ni != ti:
                    w = weight[ni]
                    if w < _best_c and MoveManager.can_fill_move(Direction.EAST):
                        _best_c = w
                        _best_d = Direction.EAST
                ni = si + 57
                if ni != ti:
                    w = weight[ni]
                    if w < _best_c and MoveManager.can_fill_move(Direction.SOUTHEAST):
                        _best_c = w
                        _best_d = Direction.SOUTHEAST
                ni = si + 1
                if ni != ti:
                    w = weight[ni]
                    if w < _best_c and MoveManager.can_fill_move(Direction.SOUTH):
                        _best_c = w
                        _best_d = Direction.SOUTH
                ni = si + -55
                if ni != ti:
                    w = weight[ni]
                    if w < _best_c and MoveManager.can_fill_move(Direction.SOUTHWEST):
                        _best_c = w
                        _best_d = Direction.SOUTHWEST
                ni = si + -56
                if ni != ti:
                    w = weight[ni]
                    if w < _best_c and MoveManager.can_fill_move(Direction.WEST):
                        _best_c = w
                        _best_d = Direction.WEST
                ni = si + -57
                if ni != ti:
                    w = weight[ni]
                    if w < _best_c and MoveManager.can_fill_move(Direction.NORTHWEST):
                        _best_c = w
                        _best_d = Direction.NORTHWEST
                if _best_d is not None:
                    return _best_c, _best_d
                return 1000000, None

        weight[ti] = 1  # allow target

        # we do this because try...finally is banned by engine

        # ── Phase 1: weighted Dijkstra up to 10 ──
        dist = [1000000] * 3136
        fhd  = [0]       * 3136
        dist[si] = 0

        heap  = []
        _hp   = heapq.heappush
        _hpop = heapq.heappop

        _settled = [si]
        _sa = _settled.append

        ni = si + -1
        if weight[ni] < 1000000 and MoveManager.can_fill_move(Direction.NORTH):
            w = weight[ni]
            dist[ni] = w
            fhd[ni]  = 0
            if ni == ti:
                # don't need to save anymore!
                return w, Direction.NORTH
            _hp(heap, (w, ni))
        ni = si + 55
        if weight[ni] < 1000000 and MoveManager.can_fill_move(Direction.NORTHEAST):
            w = weight[ni]
            dist[ni] = w
            fhd[ni]  = 1
            if ni == ti:
                # don't need to save anymore!
                return w, Direction.NORTHEAST
            _hp(heap, (w, ni))
        ni = si + 56
        if weight[ni] < 1000000 and MoveManager.can_fill_move(Direction.EAST):
            w = weight[ni]
            dist[ni] = w
            fhd[ni]  = 2
            if ni == ti:
                # don't need to save anymore!
                return w, Direction.EAST
            _hp(heap, (w, ni))
        ni = si + 57
        if weight[ni] < 1000000 and MoveManager.can_fill_move(Direction.SOUTHEAST):
            w = weight[ni]
            dist[ni] = w
            fhd[ni]  = 3
            if ni == ti:
                # don't need to save anymore!
                return w, Direction.SOUTHEAST
            _hp(heap, (w, ni))
        ni = si + 1
        if weight[ni] < 1000000 and MoveManager.can_fill_move(Direction.SOUTH):
            w = weight[ni]
            dist[ni] = w
            fhd[ni]  = 4
            if ni == ti:
                # don't need to save anymore!
                return w, Direction.SOUTH
            _hp(heap, (w, ni))
        ni = si + -55
        if weight[ni] < 1000000 and MoveManager.can_fill_move(Direction.SOUTHWEST):
            w = weight[ni]
            dist[ni] = w
            fhd[ni]  = 5
            if ni == ti:
                # don't need to save anymore!
                return w, Direction.SOUTHWEST
            _hp(heap, (w, ni))
        ni = si + -56
        if weight[ni] < 1000000 and MoveManager.can_fill_move(Direction.WEST):
            w = weight[ni]
            dist[ni] = w
            fhd[ni]  = 6
            if ni == ti:
                # don't need to save anymore!
                return w, Direction.WEST
            _hp(heap, (w, ni))
        ni = si + -57
        if weight[ni] < 1000000 and MoveManager.can_fill_move(Direction.NORTHWEST):
            w = weight[ni]
            dist[ni] = w
            fhd[ni]  = 7
            if ni == ti:
                # don't need to save anymore!
                return w, Direction.NORTHWEST
            _hp(heap, (w, ni))

        phase2_seeds = []
        _p2a = phase2_seeds.append

        while heap:
            d, idx = _hpop(heap)
            if d > dist[idx]:
                continue

            _sa(idx)

            if d >= 10:
                _p2a(idx)
                while heap:
                    _dd, _idx = _hpop(heap)
                    if _dd == dist[_idx]:
                        _sa(_idx)
                        _p2a(_idx)
                break

            _fh = fhd[idx]
            ni = idx + -1
            w  = weight[ni]
            if w < 1000000:
                nd = d + w
                if nd < dist[ni]:
                    dist[ni] = nd
                    fhd[ni]  = _fh
                    if ni == ti:
                        # don't need to save anymore!
                        return nd, _D[_fh]
                    _hp(heap, (nd, ni))
            ni = idx + 55
            w  = weight[ni]
            if w < 1000000:
                nd = d + w
                if nd < dist[ni]:
                    dist[ni] = nd
                    fhd[ni]  = _fh
                    if ni == ti:
                        # don't need to save anymore!
                        return nd, _D[_fh]
                    _hp(heap, (nd, ni))
            ni = idx + 56
            w  = weight[ni]
            if w < 1000000:
                nd = d + w
                if nd < dist[ni]:
                    dist[ni] = nd
                    fhd[ni]  = _fh
                    if ni == ti:
                        # don't need to save anymore!
                        return nd, _D[_fh]
                    _hp(heap, (nd, ni))
            ni = idx + 57
            w  = weight[ni]
            if w < 1000000:
                nd = d + w
                if nd < dist[ni]:
                    dist[ni] = nd
                    fhd[ni]  = _fh
                    if ni == ti:
                        # don't need to save anymore!
                        return nd, _D[_fh]
                    _hp(heap, (nd, ni))
            ni = idx + 1
            w  = weight[ni]
            if w < 1000000:
                nd = d + w
                if nd < dist[ni]:
                    dist[ni] = nd
                    fhd[ni]  = _fh
                    if ni == ti:
                        # don't need to save anymore!
                        return nd, _D[_fh]
                    _hp(heap, (nd, ni))
            ni = idx + -55
            w  = weight[ni]
            if w < 1000000:
                nd = d + w
                if nd < dist[ni]:
                    dist[ni] = nd
                    fhd[ni]  = _fh
                    if ni == ti:
                        # don't need to save anymore!
                        return nd, _D[_fh]
                    _hp(heap, (nd, ni))
            ni = idx + -56
            w  = weight[ni]
            if w < 1000000:
                nd = d + w
                if nd < dist[ni]:
                    dist[ni] = nd
                    fhd[ni]  = _fh
                    if ni == ti:
                        # don't need to save anymore!
                        return nd, _D[_fh]
                    _hp(heap, (nd, ni))
            ni = idx + -57
            w  = weight[ni]
            if w < 1000000:
                nd = d + w
                if nd < dist[ni]:
                    dist[ni] = nd
                    fhd[ni]  = _fh
                    if ni == ti:
                        # don't need to save anymore!
                        return nd, _D[_fh]
                    _hp(heap, (nd, ni))

        if not phase2_seeds:
            # don't need to save anymore!
            return 1000000, None

        # ── Phase 2: bitmask BFS from Dijkstra frontier ──
        Profiler.start()
        _tb = _tx * stride + _ty
        _tm = 1 << _tb
        _uc = cls.now_passable_int | _tm

        _settled_bits = 0
        for _ci in _settled:
            _cx = _ci // 56 - 3
            _cy = _ci % 56 - 3
            _settled_bits |= 1 << (_cx * stride + _cy)
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
            _bit = 1 << (_cx * stride + _cy)
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
                _e = (_v | (_v << stride) | (_v >> stride)) & _uc
                if _e:
                    _fh0 = _e
                    _uc ^= _e
                    _any = True
                    if _e & _tm:
                        # don't need to save anymore!
                        return _md0 + _bfs_d + 1, _D[0]
                else:
                    _fh0 = 0
            _f = _fh1
            if _f:
                _v = _f | (_f << 1) | (_f >> 1)
                _e = (_v | (_v << stride) | (_v >> stride)) & _uc
                if _e:
                    _fh1 = _e
                    _uc ^= _e
                    _any = True
                    if _e & _tm:
                        # don't need to save anymore!
                        return _md1 + _bfs_d + 1, _D[1]
                else:
                    _fh1 = 0
            _f = _fh2
            if _f:
                _v = _f | (_f << 1) | (_f >> 1)
                _e = (_v | (_v << stride) | (_v >> stride)) & _uc
                if _e:
                    _fh2 = _e
                    _uc ^= _e
                    _any = True
                    if _e & _tm:
                        # don't need to save anymore!
                        return _md2 + _bfs_d + 1, _D[2]
                else:
                    _fh2 = 0
            _f = _fh3
            if _f:
                _v = _f | (_f << 1) | (_f >> 1)
                _e = (_v | (_v << stride) | (_v >> stride)) & _uc
                if _e:
                    _fh3 = _e
                    _uc ^= _e
                    _any = True
                    if _e & _tm:
                        # don't need to save anymore!
                        return _md3 + _bfs_d + 1, _D[3]
                else:
                    _fh3 = 0
            _f = _fh4
            if _f:
                _v = _f | (_f << 1) | (_f >> 1)
                _e = (_v | (_v << stride) | (_v >> stride)) & _uc
                if _e:
                    _fh4 = _e
                    _uc ^= _e
                    _any = True
                    if _e & _tm:
                        # don't need to save anymore!
                        return _md4 + _bfs_d + 1, _D[4]
                else:
                    _fh4 = 0
            _f = _fh5
            if _f:
                _v = _f | (_f << 1) | (_f >> 1)
                _e = (_v | (_v << stride) | (_v >> stride)) & _uc
                if _e:
                    _fh5 = _e
                    _uc ^= _e
                    _any = True
                    if _e & _tm:
                        # don't need to save anymore!
                        return _md5 + _bfs_d + 1, _D[5]
                else:
                    _fh5 = 0
            _f = _fh6
            if _f:
                _v = _f | (_f << 1) | (_f >> 1)
                _e = (_v | (_v << stride) | (_v >> stride)) & _uc
                if _e:
                    _fh6 = _e
                    _uc ^= _e
                    _any = True
                    if _e & _tm:
                        # don't need to save anymore!
                        return _md6 + _bfs_d + 1, _D[6]
                else:
                    _fh6 = 0
            _f = _fh7
            if _f:
                _v = _f | (_f << 1) | (_f >> 1)
                _e = (_v | (_v << stride) | (_v >> stride)) & _uc
                if _e:
                    _fh7 = _e
                    _uc ^= _e
                    _any = True
                    if _e & _tm:
                        # don't need to save anymore!
                        return _md7 + _bfs_d + 1, _D[7]
                else:
                    _fh7 = 0

            if not _any:
                break
            _bfs_d += 1

        # don't need to save anymore!
        return 1000000, None
    # ===---

    # bfs20
# ---===
    bfs20_dist: list[int] = [1000000] * 3136
    _bfs20_touched_indices: list[int] = []
    _BFS20_VALID_OFFSETS = frozenset({
        -226,
        -225,
        -224,
        -223,
        -222,
        -171,
        -170,
        -169,
        -168,
        -167,
        -166,
        -165,
        -116,
        -115,
        -114,
        -113,
        -112,
        -111,
        -110,
        -109,
        -108,
        -60,
        -59,
        -58,
        -57,
        -56,
        -55,
        -54,
        -53,
        -52,
        -4,
        -3,
        -2,
        -1,
        0,
        1,
        2,
        3,
        4,
        52,
        53,
        54,
        55,
        56,
        57,
        58,
        59,
        60,
        108,
        109,
        110,
        111,
        112,
        113,
        114,
        115,
        116,
        165,
        166,
        167,
        168,
        169,
        170,
        171,
        222,
        223,
        224,
        225,
        226,
    })
# ===---
# ---===
    @classmethod
    def bfs20(cls):
        """Weighted Dijkstra from pos, limited to tiles within vision r²≤20."""
        weight = cls.now_weight
        distances = cls.bfs20_dist
        IMPASSABLE = 1000000

        # Reset tiles touched by the previous call
        for touched_index in cls._bfs20_touched_indices:
            distances[touched_index] = IMPASSABLE

        pos = Globals.my_pos
        start_x, start_y = pos.x, pos.y
        start_index = (((start_x) + 3) * 56 + ((start_y) + 3))

        distances[start_index] = 0
        touched_indices = [start_index]
        valid_offsets = cls._BFS20_VALID_OFFSETS

        priority_queue = []
        push_to_queue = heapq.heappush
        pop_from_queue = heapq.heappop

        # Seed immediate neighbours (all within r²≤2, no bounds check needed)
        neighbor_index = start_index + -1
        tile_weight = weight[neighbor_index]
        if tile_weight < IMPASSABLE:
            distances[neighbor_index] = tile_weight
            touched_indices.append(neighbor_index)
            push_to_queue(priority_queue, (tile_weight, neighbor_index))
        neighbor_index = start_index + 55
        tile_weight = weight[neighbor_index]
        if tile_weight < IMPASSABLE:
            distances[neighbor_index] = tile_weight
            touched_indices.append(neighbor_index)
            push_to_queue(priority_queue, (tile_weight, neighbor_index))
        neighbor_index = start_index + 56
        tile_weight = weight[neighbor_index]
        if tile_weight < IMPASSABLE:
            distances[neighbor_index] = tile_weight
            touched_indices.append(neighbor_index)
            push_to_queue(priority_queue, (tile_weight, neighbor_index))
        neighbor_index = start_index + 57
        tile_weight = weight[neighbor_index]
        if tile_weight < IMPASSABLE:
            distances[neighbor_index] = tile_weight
            touched_indices.append(neighbor_index)
            push_to_queue(priority_queue, (tile_weight, neighbor_index))
        neighbor_index = start_index + 1
        tile_weight = weight[neighbor_index]
        if tile_weight < IMPASSABLE:
            distances[neighbor_index] = tile_weight
            touched_indices.append(neighbor_index)
            push_to_queue(priority_queue, (tile_weight, neighbor_index))
        neighbor_index = start_index + -55
        tile_weight = weight[neighbor_index]
        if tile_weight < IMPASSABLE:
            distances[neighbor_index] = tile_weight
            touched_indices.append(neighbor_index)
            push_to_queue(priority_queue, (tile_weight, neighbor_index))
        neighbor_index = start_index + -56
        tile_weight = weight[neighbor_index]
        if tile_weight < IMPASSABLE:
            distances[neighbor_index] = tile_weight
            touched_indices.append(neighbor_index)
            push_to_queue(priority_queue, (tile_weight, neighbor_index))
        neighbor_index = start_index + -57
        tile_weight = weight[neighbor_index]
        if tile_weight < IMPASSABLE:
            distances[neighbor_index] = tile_weight
            touched_indices.append(neighbor_index)
            push_to_queue(priority_queue, (tile_weight, neighbor_index))

        # Main Dijkstra loop
        while priority_queue:
            current_dist, current_index = pop_from_queue(priority_queue)
            if current_dist > distances[current_index]:
                continue
            neighbor_index = current_index + -1
            if (neighbor_index - start_index) in valid_offsets:
                tile_weight = weight[neighbor_index]
                if tile_weight < IMPASSABLE:
                    new_dist = current_dist + tile_weight
                    if new_dist < distances[neighbor_index]:
                        distances[neighbor_index] = new_dist
                        touched_indices.append(neighbor_index)
                        push_to_queue(priority_queue, (new_dist, neighbor_index))
            neighbor_index = current_index + 55
            if (neighbor_index - start_index) in valid_offsets:
                tile_weight = weight[neighbor_index]
                if tile_weight < IMPASSABLE:
                    new_dist = current_dist + tile_weight
                    if new_dist < distances[neighbor_index]:
                        distances[neighbor_index] = new_dist
                        touched_indices.append(neighbor_index)
                        push_to_queue(priority_queue, (new_dist, neighbor_index))
            neighbor_index = current_index + 56
            if (neighbor_index - start_index) in valid_offsets:
                tile_weight = weight[neighbor_index]
                if tile_weight < IMPASSABLE:
                    new_dist = current_dist + tile_weight
                    if new_dist < distances[neighbor_index]:
                        distances[neighbor_index] = new_dist
                        touched_indices.append(neighbor_index)
                        push_to_queue(priority_queue, (new_dist, neighbor_index))
            neighbor_index = current_index + 57
            if (neighbor_index - start_index) in valid_offsets:
                tile_weight = weight[neighbor_index]
                if tile_weight < IMPASSABLE:
                    new_dist = current_dist + tile_weight
                    if new_dist < distances[neighbor_index]:
                        distances[neighbor_index] = new_dist
                        touched_indices.append(neighbor_index)
                        push_to_queue(priority_queue, (new_dist, neighbor_index))
            neighbor_index = current_index + 1
            if (neighbor_index - start_index) in valid_offsets:
                tile_weight = weight[neighbor_index]
                if tile_weight < IMPASSABLE:
                    new_dist = current_dist + tile_weight
                    if new_dist < distances[neighbor_index]:
                        distances[neighbor_index] = new_dist
                        touched_indices.append(neighbor_index)
                        push_to_queue(priority_queue, (new_dist, neighbor_index))
            neighbor_index = current_index + -55
            if (neighbor_index - start_index) in valid_offsets:
                tile_weight = weight[neighbor_index]
                if tile_weight < IMPASSABLE:
                    new_dist = current_dist + tile_weight
                    if new_dist < distances[neighbor_index]:
                        distances[neighbor_index] = new_dist
                        touched_indices.append(neighbor_index)
                        push_to_queue(priority_queue, (new_dist, neighbor_index))
            neighbor_index = current_index + -56
            if (neighbor_index - start_index) in valid_offsets:
                tile_weight = weight[neighbor_index]
                if tile_weight < IMPASSABLE:
                    new_dist = current_dist + tile_weight
                    if new_dist < distances[neighbor_index]:
                        distances[neighbor_index] = new_dist
                        touched_indices.append(neighbor_index)
                        push_to_queue(priority_queue, (new_dist, neighbor_index))
            neighbor_index = current_index + -57
            if (neighbor_index - start_index) in valid_offsets:
                tile_weight = weight[neighbor_index]
                if tile_weight < IMPASSABLE:
                    new_dist = current_dist + tile_weight
                    if new_dist < distances[neighbor_index]:
                        distances[neighbor_index] = new_dist
                        touched_indices.append(neighbor_index)
                        push_to_queue(priority_queue, (new_dist, neighbor_index))

        cls._bfs20_touched_indices = touched_indices
# ===---
# ---===
    @classmethod
    def debug_bfs20(cls):
        """Draw indicator dots for all tiles within r²≤20 of pos.
        WHITE = reachable (finite distance), BLACK = impassable/unreachable."""
        distances = cls.bfs20_dist
        IMPASSABLE = 1000000

        pos = Globals.my_pos
        start_x, start_y = pos.x, pos.y
        start_index = (((start_x) + 3) * 56 + ((start_y) + 3))

        tile_x = start_x + -4
        tile_y = start_y + -2
        if 0 <= tile_x < Map.W and 0 <= tile_y < Map.H:
            tile_index = start_index + -226
            if distances[tile_index] < IMPASSABLE:
                Debug.dot(Position(tile_x, tile_y), Color.WHITE)
            else:
                Debug.dot(Position(tile_x, tile_y), Color.BLACK)
        tile_x = start_x + -4
        tile_y = start_y + -1
        if 0 <= tile_x < Map.W and 0 <= tile_y < Map.H:
            tile_index = start_index + -225
            if distances[tile_index] < IMPASSABLE:
                Debug.dot(Position(tile_x, tile_y), Color.WHITE)
            else:
                Debug.dot(Position(tile_x, tile_y), Color.BLACK)
        tile_x = start_x + -4
        tile_y = start_y + 0
        if 0 <= tile_x < Map.W and 0 <= tile_y < Map.H:
            tile_index = start_index + -224
            if distances[tile_index] < IMPASSABLE:
                Debug.dot(Position(tile_x, tile_y), Color.WHITE)
            else:
                Debug.dot(Position(tile_x, tile_y), Color.BLACK)
        tile_x = start_x + -4
        tile_y = start_y + 1
        if 0 <= tile_x < Map.W and 0 <= tile_y < Map.H:
            tile_index = start_index + -223
            if distances[tile_index] < IMPASSABLE:
                Debug.dot(Position(tile_x, tile_y), Color.WHITE)
            else:
                Debug.dot(Position(tile_x, tile_y), Color.BLACK)
        tile_x = start_x + -4
        tile_y = start_y + 2
        if 0 <= tile_x < Map.W and 0 <= tile_y < Map.H:
            tile_index = start_index + -222
            if distances[tile_index] < IMPASSABLE:
                Debug.dot(Position(tile_x, tile_y), Color.WHITE)
            else:
                Debug.dot(Position(tile_x, tile_y), Color.BLACK)
        tile_x = start_x + -3
        tile_y = start_y + -3
        if 0 <= tile_x < Map.W and 0 <= tile_y < Map.H:
            tile_index = start_index + -171
            if distances[tile_index] < IMPASSABLE:
                Debug.dot(Position(tile_x, tile_y), Color.WHITE)
            else:
                Debug.dot(Position(tile_x, tile_y), Color.BLACK)
        tile_x = start_x + -3
        tile_y = start_y + -2
        if 0 <= tile_x < Map.W and 0 <= tile_y < Map.H:
            tile_index = start_index + -170
            if distances[tile_index] < IMPASSABLE:
                Debug.dot(Position(tile_x, tile_y), Color.WHITE)
            else:
                Debug.dot(Position(tile_x, tile_y), Color.BLACK)
        tile_x = start_x + -3
        tile_y = start_y + -1
        if 0 <= tile_x < Map.W and 0 <= tile_y < Map.H:
            tile_index = start_index + -169
            if distances[tile_index] < IMPASSABLE:
                Debug.dot(Position(tile_x, tile_y), Color.WHITE)
            else:
                Debug.dot(Position(tile_x, tile_y), Color.BLACK)
        tile_x = start_x + -3
        tile_y = start_y + 0
        if 0 <= tile_x < Map.W and 0 <= tile_y < Map.H:
            tile_index = start_index + -168
            if distances[tile_index] < IMPASSABLE:
                Debug.dot(Position(tile_x, tile_y), Color.WHITE)
            else:
                Debug.dot(Position(tile_x, tile_y), Color.BLACK)
        tile_x = start_x + -3
        tile_y = start_y + 1
        if 0 <= tile_x < Map.W and 0 <= tile_y < Map.H:
            tile_index = start_index + -167
            if distances[tile_index] < IMPASSABLE:
                Debug.dot(Position(tile_x, tile_y), Color.WHITE)
            else:
                Debug.dot(Position(tile_x, tile_y), Color.BLACK)
        tile_x = start_x + -3
        tile_y = start_y + 2
        if 0 <= tile_x < Map.W and 0 <= tile_y < Map.H:
            tile_index = start_index + -166
            if distances[tile_index] < IMPASSABLE:
                Debug.dot(Position(tile_x, tile_y), Color.WHITE)
            else:
                Debug.dot(Position(tile_x, tile_y), Color.BLACK)
        tile_x = start_x + -3
        tile_y = start_y + 3
        if 0 <= tile_x < Map.W and 0 <= tile_y < Map.H:
            tile_index = start_index + -165
            if distances[tile_index] < IMPASSABLE:
                Debug.dot(Position(tile_x, tile_y), Color.WHITE)
            else:
                Debug.dot(Position(tile_x, tile_y), Color.BLACK)
        tile_x = start_x + -2
        tile_y = start_y + -4
        if 0 <= tile_x < Map.W and 0 <= tile_y < Map.H:
            tile_index = start_index + -116
            if distances[tile_index] < IMPASSABLE:
                Debug.dot(Position(tile_x, tile_y), Color.WHITE)
            else:
                Debug.dot(Position(tile_x, tile_y), Color.BLACK)
        tile_x = start_x + -2
        tile_y = start_y + -3
        if 0 <= tile_x < Map.W and 0 <= tile_y < Map.H:
            tile_index = start_index + -115
            if distances[tile_index] < IMPASSABLE:
                Debug.dot(Position(tile_x, tile_y), Color.WHITE)
            else:
                Debug.dot(Position(tile_x, tile_y), Color.BLACK)
        tile_x = start_x + -2
        tile_y = start_y + -2
        if 0 <= tile_x < Map.W and 0 <= tile_y < Map.H:
            tile_index = start_index + -114
            if distances[tile_index] < IMPASSABLE:
                Debug.dot(Position(tile_x, tile_y), Color.WHITE)
            else:
                Debug.dot(Position(tile_x, tile_y), Color.BLACK)
        tile_x = start_x + -2
        tile_y = start_y + -1
        if 0 <= tile_x < Map.W and 0 <= tile_y < Map.H:
            tile_index = start_index + -113
            if distances[tile_index] < IMPASSABLE:
                Debug.dot(Position(tile_x, tile_y), Color.WHITE)
            else:
                Debug.dot(Position(tile_x, tile_y), Color.BLACK)
        tile_x = start_x + -2
        tile_y = start_y + 0
        if 0 <= tile_x < Map.W and 0 <= tile_y < Map.H:
            tile_index = start_index + -112
            if distances[tile_index] < IMPASSABLE:
                Debug.dot(Position(tile_x, tile_y), Color.WHITE)
            else:
                Debug.dot(Position(tile_x, tile_y), Color.BLACK)
        tile_x = start_x + -2
        tile_y = start_y + 1
        if 0 <= tile_x < Map.W and 0 <= tile_y < Map.H:
            tile_index = start_index + -111
            if distances[tile_index] < IMPASSABLE:
                Debug.dot(Position(tile_x, tile_y), Color.WHITE)
            else:
                Debug.dot(Position(tile_x, tile_y), Color.BLACK)
        tile_x = start_x + -2
        tile_y = start_y + 2
        if 0 <= tile_x < Map.W and 0 <= tile_y < Map.H:
            tile_index = start_index + -110
            if distances[tile_index] < IMPASSABLE:
                Debug.dot(Position(tile_x, tile_y), Color.WHITE)
            else:
                Debug.dot(Position(tile_x, tile_y), Color.BLACK)
        tile_x = start_x + -2
        tile_y = start_y + 3
        if 0 <= tile_x < Map.W and 0 <= tile_y < Map.H:
            tile_index = start_index + -109
            if distances[tile_index] < IMPASSABLE:
                Debug.dot(Position(tile_x, tile_y), Color.WHITE)
            else:
                Debug.dot(Position(tile_x, tile_y), Color.BLACK)
        tile_x = start_x + -2
        tile_y = start_y + 4
        if 0 <= tile_x < Map.W and 0 <= tile_y < Map.H:
            tile_index = start_index + -108
            if distances[tile_index] < IMPASSABLE:
                Debug.dot(Position(tile_x, tile_y), Color.WHITE)
            else:
                Debug.dot(Position(tile_x, tile_y), Color.BLACK)
        tile_x = start_x + -1
        tile_y = start_y + -4
        if 0 <= tile_x < Map.W and 0 <= tile_y < Map.H:
            tile_index = start_index + -60
            if distances[tile_index] < IMPASSABLE:
                Debug.dot(Position(tile_x, tile_y), Color.WHITE)
            else:
                Debug.dot(Position(tile_x, tile_y), Color.BLACK)
        tile_x = start_x + -1
        tile_y = start_y + -3
        if 0 <= tile_x < Map.W and 0 <= tile_y < Map.H:
            tile_index = start_index + -59
            if distances[tile_index] < IMPASSABLE:
                Debug.dot(Position(tile_x, tile_y), Color.WHITE)
            else:
                Debug.dot(Position(tile_x, tile_y), Color.BLACK)
        tile_x = start_x + -1
        tile_y = start_y + -2
        if 0 <= tile_x < Map.W and 0 <= tile_y < Map.H:
            tile_index = start_index + -58
            if distances[tile_index] < IMPASSABLE:
                Debug.dot(Position(tile_x, tile_y), Color.WHITE)
            else:
                Debug.dot(Position(tile_x, tile_y), Color.BLACK)
        tile_x = start_x + -1
        tile_y = start_y + -1
        if 0 <= tile_x < Map.W and 0 <= tile_y < Map.H:
            tile_index = start_index + -57
            if distances[tile_index] < IMPASSABLE:
                Debug.dot(Position(tile_x, tile_y), Color.WHITE)
            else:
                Debug.dot(Position(tile_x, tile_y), Color.BLACK)
        tile_x = start_x + -1
        tile_y = start_y + 0
        if 0 <= tile_x < Map.W and 0 <= tile_y < Map.H:
            tile_index = start_index + -56
            if distances[tile_index] < IMPASSABLE:
                Debug.dot(Position(tile_x, tile_y), Color.WHITE)
            else:
                Debug.dot(Position(tile_x, tile_y), Color.BLACK)
        tile_x = start_x + -1
        tile_y = start_y + 1
        if 0 <= tile_x < Map.W and 0 <= tile_y < Map.H:
            tile_index = start_index + -55
            if distances[tile_index] < IMPASSABLE:
                Debug.dot(Position(tile_x, tile_y), Color.WHITE)
            else:
                Debug.dot(Position(tile_x, tile_y), Color.BLACK)
        tile_x = start_x + -1
        tile_y = start_y + 2
        if 0 <= tile_x < Map.W and 0 <= tile_y < Map.H:
            tile_index = start_index + -54
            if distances[tile_index] < IMPASSABLE:
                Debug.dot(Position(tile_x, tile_y), Color.WHITE)
            else:
                Debug.dot(Position(tile_x, tile_y), Color.BLACK)
        tile_x = start_x + -1
        tile_y = start_y + 3
        if 0 <= tile_x < Map.W and 0 <= tile_y < Map.H:
            tile_index = start_index + -53
            if distances[tile_index] < IMPASSABLE:
                Debug.dot(Position(tile_x, tile_y), Color.WHITE)
            else:
                Debug.dot(Position(tile_x, tile_y), Color.BLACK)
        tile_x = start_x + -1
        tile_y = start_y + 4
        if 0 <= tile_x < Map.W and 0 <= tile_y < Map.H:
            tile_index = start_index + -52
            if distances[tile_index] < IMPASSABLE:
                Debug.dot(Position(tile_x, tile_y), Color.WHITE)
            else:
                Debug.dot(Position(tile_x, tile_y), Color.BLACK)
        tile_x = start_x + 0
        tile_y = start_y + -4
        if 0 <= tile_x < Map.W and 0 <= tile_y < Map.H:
            tile_index = start_index + -4
            if distances[tile_index] < IMPASSABLE:
                Debug.dot(Position(tile_x, tile_y), Color.WHITE)
            else:
                Debug.dot(Position(tile_x, tile_y), Color.BLACK)
        tile_x = start_x + 0
        tile_y = start_y + -3
        if 0 <= tile_x < Map.W and 0 <= tile_y < Map.H:
            tile_index = start_index + -3
            if distances[tile_index] < IMPASSABLE:
                Debug.dot(Position(tile_x, tile_y), Color.WHITE)
            else:
                Debug.dot(Position(tile_x, tile_y), Color.BLACK)
        tile_x = start_x + 0
        tile_y = start_y + -2
        if 0 <= tile_x < Map.W and 0 <= tile_y < Map.H:
            tile_index = start_index + -2
            if distances[tile_index] < IMPASSABLE:
                Debug.dot(Position(tile_x, tile_y), Color.WHITE)
            else:
                Debug.dot(Position(tile_x, tile_y), Color.BLACK)
        tile_x = start_x + 0
        tile_y = start_y + -1
        if 0 <= tile_x < Map.W and 0 <= tile_y < Map.H:
            tile_index = start_index + -1
            if distances[tile_index] < IMPASSABLE:
                Debug.dot(Position(tile_x, tile_y), Color.WHITE)
            else:
                Debug.dot(Position(tile_x, tile_y), Color.BLACK)
        tile_x = start_x + 0
        tile_y = start_y + 0
        if 0 <= tile_x < Map.W and 0 <= tile_y < Map.H:
            tile_index = start_index + 0
            if distances[tile_index] < IMPASSABLE:
                Debug.dot(Position(tile_x, tile_y), Color.WHITE)
            else:
                Debug.dot(Position(tile_x, tile_y), Color.BLACK)
        tile_x = start_x + 0
        tile_y = start_y + 1
        if 0 <= tile_x < Map.W and 0 <= tile_y < Map.H:
            tile_index = start_index + 1
            if distances[tile_index] < IMPASSABLE:
                Debug.dot(Position(tile_x, tile_y), Color.WHITE)
            else:
                Debug.dot(Position(tile_x, tile_y), Color.BLACK)
        tile_x = start_x + 0
        tile_y = start_y + 2
        if 0 <= tile_x < Map.W and 0 <= tile_y < Map.H:
            tile_index = start_index + 2
            if distances[tile_index] < IMPASSABLE:
                Debug.dot(Position(tile_x, tile_y), Color.WHITE)
            else:
                Debug.dot(Position(tile_x, tile_y), Color.BLACK)
        tile_x = start_x + 0
        tile_y = start_y + 3
        if 0 <= tile_x < Map.W and 0 <= tile_y < Map.H:
            tile_index = start_index + 3
            if distances[tile_index] < IMPASSABLE:
                Debug.dot(Position(tile_x, tile_y), Color.WHITE)
            else:
                Debug.dot(Position(tile_x, tile_y), Color.BLACK)
        tile_x = start_x + 0
        tile_y = start_y + 4
        if 0 <= tile_x < Map.W and 0 <= tile_y < Map.H:
            tile_index = start_index + 4
            if distances[tile_index] < IMPASSABLE:
                Debug.dot(Position(tile_x, tile_y), Color.WHITE)
            else:
                Debug.dot(Position(tile_x, tile_y), Color.BLACK)
        tile_x = start_x + 1
        tile_y = start_y + -4
        if 0 <= tile_x < Map.W and 0 <= tile_y < Map.H:
            tile_index = start_index + 52
            if distances[tile_index] < IMPASSABLE:
                Debug.dot(Position(tile_x, tile_y), Color.WHITE)
            else:
                Debug.dot(Position(tile_x, tile_y), Color.BLACK)
        tile_x = start_x + 1
        tile_y = start_y + -3
        if 0 <= tile_x < Map.W and 0 <= tile_y < Map.H:
            tile_index = start_index + 53
            if distances[tile_index] < IMPASSABLE:
                Debug.dot(Position(tile_x, tile_y), Color.WHITE)
            else:
                Debug.dot(Position(tile_x, tile_y), Color.BLACK)
        tile_x = start_x + 1
        tile_y = start_y + -2
        if 0 <= tile_x < Map.W and 0 <= tile_y < Map.H:
            tile_index = start_index + 54
            if distances[tile_index] < IMPASSABLE:
                Debug.dot(Position(tile_x, tile_y), Color.WHITE)
            else:
                Debug.dot(Position(tile_x, tile_y), Color.BLACK)
        tile_x = start_x + 1
        tile_y = start_y + -1
        if 0 <= tile_x < Map.W and 0 <= tile_y < Map.H:
            tile_index = start_index + 55
            if distances[tile_index] < IMPASSABLE:
                Debug.dot(Position(tile_x, tile_y), Color.WHITE)
            else:
                Debug.dot(Position(tile_x, tile_y), Color.BLACK)
        tile_x = start_x + 1
        tile_y = start_y + 0
        if 0 <= tile_x < Map.W and 0 <= tile_y < Map.H:
            tile_index = start_index + 56
            if distances[tile_index] < IMPASSABLE:
                Debug.dot(Position(tile_x, tile_y), Color.WHITE)
            else:
                Debug.dot(Position(tile_x, tile_y), Color.BLACK)
        tile_x = start_x + 1
        tile_y = start_y + 1
        if 0 <= tile_x < Map.W and 0 <= tile_y < Map.H:
            tile_index = start_index + 57
            if distances[tile_index] < IMPASSABLE:
                Debug.dot(Position(tile_x, tile_y), Color.WHITE)
            else:
                Debug.dot(Position(tile_x, tile_y), Color.BLACK)
        tile_x = start_x + 1
        tile_y = start_y + 2
        if 0 <= tile_x < Map.W and 0 <= tile_y < Map.H:
            tile_index = start_index + 58
            if distances[tile_index] < IMPASSABLE:
                Debug.dot(Position(tile_x, tile_y), Color.WHITE)
            else:
                Debug.dot(Position(tile_x, tile_y), Color.BLACK)
        tile_x = start_x + 1
        tile_y = start_y + 3
        if 0 <= tile_x < Map.W and 0 <= tile_y < Map.H:
            tile_index = start_index + 59
            if distances[tile_index] < IMPASSABLE:
                Debug.dot(Position(tile_x, tile_y), Color.WHITE)
            else:
                Debug.dot(Position(tile_x, tile_y), Color.BLACK)
        tile_x = start_x + 1
        tile_y = start_y + 4
        if 0 <= tile_x < Map.W and 0 <= tile_y < Map.H:
            tile_index = start_index + 60
            if distances[tile_index] < IMPASSABLE:
                Debug.dot(Position(tile_x, tile_y), Color.WHITE)
            else:
                Debug.dot(Position(tile_x, tile_y), Color.BLACK)
        tile_x = start_x + 2
        tile_y = start_y + -4
        if 0 <= tile_x < Map.W and 0 <= tile_y < Map.H:
            tile_index = start_index + 108
            if distances[tile_index] < IMPASSABLE:
                Debug.dot(Position(tile_x, tile_y), Color.WHITE)
            else:
                Debug.dot(Position(tile_x, tile_y), Color.BLACK)
        tile_x = start_x + 2
        tile_y = start_y + -3
        if 0 <= tile_x < Map.W and 0 <= tile_y < Map.H:
            tile_index = start_index + 109
            if distances[tile_index] < IMPASSABLE:
                Debug.dot(Position(tile_x, tile_y), Color.WHITE)
            else:
                Debug.dot(Position(tile_x, tile_y), Color.BLACK)
        tile_x = start_x + 2
        tile_y = start_y + -2
        if 0 <= tile_x < Map.W and 0 <= tile_y < Map.H:
            tile_index = start_index + 110
            if distances[tile_index] < IMPASSABLE:
                Debug.dot(Position(tile_x, tile_y), Color.WHITE)
            else:
                Debug.dot(Position(tile_x, tile_y), Color.BLACK)
        tile_x = start_x + 2
        tile_y = start_y + -1
        if 0 <= tile_x < Map.W and 0 <= tile_y < Map.H:
            tile_index = start_index + 111
            if distances[tile_index] < IMPASSABLE:
                Debug.dot(Position(tile_x, tile_y), Color.WHITE)
            else:
                Debug.dot(Position(tile_x, tile_y), Color.BLACK)
        tile_x = start_x + 2
        tile_y = start_y + 0
        if 0 <= tile_x < Map.W and 0 <= tile_y < Map.H:
            tile_index = start_index + 112
            if distances[tile_index] < IMPASSABLE:
                Debug.dot(Position(tile_x, tile_y), Color.WHITE)
            else:
                Debug.dot(Position(tile_x, tile_y), Color.BLACK)
        tile_x = start_x + 2
        tile_y = start_y + 1
        if 0 <= tile_x < Map.W and 0 <= tile_y < Map.H:
            tile_index = start_index + 113
            if distances[tile_index] < IMPASSABLE:
                Debug.dot(Position(tile_x, tile_y), Color.WHITE)
            else:
                Debug.dot(Position(tile_x, tile_y), Color.BLACK)
        tile_x = start_x + 2
        tile_y = start_y + 2
        if 0 <= tile_x < Map.W and 0 <= tile_y < Map.H:
            tile_index = start_index + 114
            if distances[tile_index] < IMPASSABLE:
                Debug.dot(Position(tile_x, tile_y), Color.WHITE)
            else:
                Debug.dot(Position(tile_x, tile_y), Color.BLACK)
        tile_x = start_x + 2
        tile_y = start_y + 3
        if 0 <= tile_x < Map.W and 0 <= tile_y < Map.H:
            tile_index = start_index + 115
            if distances[tile_index] < IMPASSABLE:
                Debug.dot(Position(tile_x, tile_y), Color.WHITE)
            else:
                Debug.dot(Position(tile_x, tile_y), Color.BLACK)
        tile_x = start_x + 2
        tile_y = start_y + 4
        if 0 <= tile_x < Map.W and 0 <= tile_y < Map.H:
            tile_index = start_index + 116
            if distances[tile_index] < IMPASSABLE:
                Debug.dot(Position(tile_x, tile_y), Color.WHITE)
            else:
                Debug.dot(Position(tile_x, tile_y), Color.BLACK)
        tile_x = start_x + 3
        tile_y = start_y + -3
        if 0 <= tile_x < Map.W and 0 <= tile_y < Map.H:
            tile_index = start_index + 165
            if distances[tile_index] < IMPASSABLE:
                Debug.dot(Position(tile_x, tile_y), Color.WHITE)
            else:
                Debug.dot(Position(tile_x, tile_y), Color.BLACK)
        tile_x = start_x + 3
        tile_y = start_y + -2
        if 0 <= tile_x < Map.W and 0 <= tile_y < Map.H:
            tile_index = start_index + 166
            if distances[tile_index] < IMPASSABLE:
                Debug.dot(Position(tile_x, tile_y), Color.WHITE)
            else:
                Debug.dot(Position(tile_x, tile_y), Color.BLACK)
        tile_x = start_x + 3
        tile_y = start_y + -1
        if 0 <= tile_x < Map.W and 0 <= tile_y < Map.H:
            tile_index = start_index + 167
            if distances[tile_index] < IMPASSABLE:
                Debug.dot(Position(tile_x, tile_y), Color.WHITE)
            else:
                Debug.dot(Position(tile_x, tile_y), Color.BLACK)
        tile_x = start_x + 3
        tile_y = start_y + 0
        if 0 <= tile_x < Map.W and 0 <= tile_y < Map.H:
            tile_index = start_index + 168
            if distances[tile_index] < IMPASSABLE:
                Debug.dot(Position(tile_x, tile_y), Color.WHITE)
            else:
                Debug.dot(Position(tile_x, tile_y), Color.BLACK)
        tile_x = start_x + 3
        tile_y = start_y + 1
        if 0 <= tile_x < Map.W and 0 <= tile_y < Map.H:
            tile_index = start_index + 169
            if distances[tile_index] < IMPASSABLE:
                Debug.dot(Position(tile_x, tile_y), Color.WHITE)
            else:
                Debug.dot(Position(tile_x, tile_y), Color.BLACK)
        tile_x = start_x + 3
        tile_y = start_y + 2
        if 0 <= tile_x < Map.W and 0 <= tile_y < Map.H:
            tile_index = start_index + 170
            if distances[tile_index] < IMPASSABLE:
                Debug.dot(Position(tile_x, tile_y), Color.WHITE)
            else:
                Debug.dot(Position(tile_x, tile_y), Color.BLACK)
        tile_x = start_x + 3
        tile_y = start_y + 3
        if 0 <= tile_x < Map.W and 0 <= tile_y < Map.H:
            tile_index = start_index + 171
            if distances[tile_index] < IMPASSABLE:
                Debug.dot(Position(tile_x, tile_y), Color.WHITE)
            else:
                Debug.dot(Position(tile_x, tile_y), Color.BLACK)
        tile_x = start_x + 4
        tile_y = start_y + -2
        if 0 <= tile_x < Map.W and 0 <= tile_y < Map.H:
            tile_index = start_index + 222
            if distances[tile_index] < IMPASSABLE:
                Debug.dot(Position(tile_x, tile_y), Color.WHITE)
            else:
                Debug.dot(Position(tile_x, tile_y), Color.BLACK)
        tile_x = start_x + 4
        tile_y = start_y + -1
        if 0 <= tile_x < Map.W and 0 <= tile_y < Map.H:
            tile_index = start_index + 223
            if distances[tile_index] < IMPASSABLE:
                Debug.dot(Position(tile_x, tile_y), Color.WHITE)
            else:
                Debug.dot(Position(tile_x, tile_y), Color.BLACK)
        tile_x = start_x + 4
        tile_y = start_y + 0
        if 0 <= tile_x < Map.W and 0 <= tile_y < Map.H:
            tile_index = start_index + 224
            if distances[tile_index] < IMPASSABLE:
                Debug.dot(Position(tile_x, tile_y), Color.WHITE)
            else:
                Debug.dot(Position(tile_x, tile_y), Color.BLACK)
        tile_x = start_x + 4
        tile_y = start_y + 1
        if 0 <= tile_x < Map.W and 0 <= tile_y < Map.H:
            tile_index = start_index + 225
            if distances[tile_index] < IMPASSABLE:
                Debug.dot(Position(tile_x, tile_y), Color.WHITE)
            else:
                Debug.dot(Position(tile_x, tile_y), Color.BLACK)
        tile_x = start_x + 4
        tile_y = start_y + 2
        if 0 <= tile_x < Map.W and 0 <= tile_y < Map.H:
            tile_index = start_index + 226
            if distances[tile_index] < IMPASSABLE:
                Debug.dot(Position(tile_x, tile_y), Color.WHITE)
            else:
                Debug.dot(Position(tile_x, tile_y), Color.BLACK)
# ===---

    @classmethod
    def get_bfs20_dist(cls, pos: Position):
        return cls.bfs20_dist[(((pos.x) + 3) * 56 + ((pos.y) + 3))]