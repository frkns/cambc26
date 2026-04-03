# === main.py ===

from __future__ import annotations
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

# ============================================================
# BfsBureau
# ============================================================

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


# ============================================================
# BuildManager
# ============================================================

class BuildManager:
    reserve_ti: int = 100  # scale this
    reserve_ax: int = 0

    @staticmethod
    def scale(cost: int) -> int:
        return int(cost * MarketMaker.scale_ratio)

    @staticmethod
    def is_buildable(pos: Position):
        dsq = Globals.ct.get_position().distance_squared(pos)
        if dsq > 2 or dsq == 0:
            return False

        ti = Map.tile_info[pos.x][pos.y]
        return (
            ti.env != Environment.WALL 
            and not ti.has_building
            and not ti.has_bot
        )

    @staticmethod
    def is_dbuildable(pos: Position):
        dsq = Globals.ct.get_position().distance_squared(pos)
        if dsq > 2 or dsq == 0:
            return False

        ti = Map.tile_info[pos.x][pos.y]

        if Globals.ct.can_destroy(pos) and not ti.has_bot:
            return True

        return (
            ti.env != Environment.WALL
            and not ti.has_bot
            and (not ti.has_building or (ti.is_building_ally and ti.entity_type != EntityType.CORE))
        )



    @staticmethod
    def build_builder_bot(*a):
        Globals.ct.build_builder_bot(*a)

    @staticmethod
    def dbuild_builder_bot(pos, *a):
        if Globals.ct.can_destroy(pos):
            Globals.ct.destroy(pos)
        Globals.ct.build_builder_bot(pos, *a)

    @staticmethod
    def can_dbuild_builder_bot(pos) -> bool:
        return (
            Globals.ct.get_action_cooldown() == 0 and
            BuildManager.is_dbuildable(pos) and 
            BuildManager.can_afford_builder_bot()
        )

    @staticmethod
    def can_build_builder_bot(*a) -> bool:
        return Globals.ct.can_build_builder_bot(*a)

    @staticmethod
    def can_afford_builder_bot() -> bool:
        ti_cost, ax_cost = Globals.ct.get_builder_bot_cost()
        return MarketMaker.ti >= ti_cost and MarketMaker.ax >= ax_cost

    @classmethod
    def reserve_check_builder_bot(cls) -> bool:
        ti_cost, ax_cost = Globals.ct.get_builder_bot_cost()
        if (MarketMaker.ti - ti_cost) < cls.reserve_ti * MarketMaker.scale_ratio:
            return False
        if (MarketMaker.ax - ax_cost) < cls.reserve_ax * MarketMaker.scale_ratio:
            Debug.log('ax branch triggered')
            return False
        return True


    @staticmethod
    def build_gunner(*a):
        Globals.ct.build_gunner(*a)

    @staticmethod
    def dbuild_gunner(pos, *a):
        if Globals.ct.can_destroy(pos):
            Globals.ct.destroy(pos)
        Globals.ct.build_gunner(pos, *a)

    @staticmethod
    def can_dbuild_gunner(pos) -> bool:
        return (
            Globals.ct.get_action_cooldown() == 0 and
            BuildManager.is_dbuildable(pos) and 
            BuildManager.can_afford_gunner()
        )

    @staticmethod
    def can_build_gunner(*a) -> bool:
        return Globals.ct.can_build_gunner(*a)

    @staticmethod
    def can_afford_gunner() -> bool:
        ti_cost, ax_cost = Globals.ct.get_gunner_cost()
        return MarketMaker.ti >= ti_cost and MarketMaker.ax >= ax_cost

    @classmethod
    def reserve_check_gunner(cls) -> bool:
        ti_cost, ax_cost = Globals.ct.get_gunner_cost()
        if (MarketMaker.ti - ti_cost) < cls.reserve_ti * MarketMaker.scale_ratio:
            return False
        if (MarketMaker.ax - ax_cost) < cls.reserve_ax * MarketMaker.scale_ratio:
            Debug.log('ax branch triggered')
            return False
        return True


    @staticmethod
    def build_sentinel(*a):
        Globals.ct.build_sentinel(*a)

    @staticmethod
    def dbuild_sentinel(pos, *a):
        if Globals.ct.can_destroy(pos):
            Globals.ct.destroy(pos)
        Globals.ct.build_sentinel(pos, *a)

    @staticmethod
    def can_dbuild_sentinel(pos) -> bool:
        return (
            Globals.ct.get_action_cooldown() == 0 and
            BuildManager.is_dbuildable(pos) and 
            BuildManager.can_afford_sentinel()
        )

    @staticmethod
    def can_build_sentinel(*a) -> bool:
        return Globals.ct.can_build_sentinel(*a)

    @staticmethod
    def can_afford_sentinel() -> bool:
        ti_cost, ax_cost = Globals.ct.get_sentinel_cost()
        return MarketMaker.ti >= ti_cost and MarketMaker.ax >= ax_cost

    @classmethod
    def reserve_check_sentinel(cls) -> bool:
        ti_cost, ax_cost = Globals.ct.get_sentinel_cost()
        if (MarketMaker.ti - ti_cost) < cls.reserve_ti * MarketMaker.scale_ratio:
            return False
        if (MarketMaker.ax - ax_cost) < cls.reserve_ax * MarketMaker.scale_ratio:
            Debug.log('ax branch triggered')
            return False
        return True


    @staticmethod
    def build_breach(*a):
        Globals.ct.build_breach(*a)

    @staticmethod
    def dbuild_breach(pos, *a):
        if Globals.ct.can_destroy(pos):
            Globals.ct.destroy(pos)
        Globals.ct.build_breach(pos, *a)

    @staticmethod
    def can_dbuild_breach(pos) -> bool:
        return (
            Globals.ct.get_action_cooldown() == 0 and
            BuildManager.is_dbuildable(pos) and 
            BuildManager.can_afford_breach()
        )

    @staticmethod
    def can_build_breach(*a) -> bool:
        return Globals.ct.can_build_breach(*a)

    @staticmethod
    def can_afford_breach() -> bool:
        ti_cost, ax_cost = Globals.ct.get_breach_cost()
        return MarketMaker.ti >= ti_cost and MarketMaker.ax >= ax_cost

    @classmethod
    def reserve_check_breach(cls) -> bool:
        ti_cost, ax_cost = Globals.ct.get_breach_cost()
        if (MarketMaker.ti - ti_cost) < cls.reserve_ti * MarketMaker.scale_ratio:
            return False
        if (MarketMaker.ax - ax_cost) < cls.reserve_ax * MarketMaker.scale_ratio:
            Debug.log('ax branch triggered')
            return False
        return True


    @staticmethod
    def build_launcher(*a):
        Globals.ct.build_launcher(*a)

    @staticmethod
    def dbuild_launcher(pos, *a):
        if Globals.ct.can_destroy(pos):
            Globals.ct.destroy(pos)
        Globals.ct.build_launcher(pos, *a)

    @staticmethod
    def can_dbuild_launcher(pos) -> bool:
        return (
            Globals.ct.get_action_cooldown() == 0 and
            BuildManager.is_dbuildable(pos) and 
            BuildManager.can_afford_launcher()
        )

    @staticmethod
    def can_build_launcher(*a) -> bool:
        return Globals.ct.can_build_launcher(*a)

    @staticmethod
    def can_afford_launcher() -> bool:
        ti_cost, ax_cost = Globals.ct.get_launcher_cost()
        return MarketMaker.ti >= ti_cost and MarketMaker.ax >= ax_cost

    @classmethod
    def reserve_check_launcher(cls) -> bool:
        ti_cost, ax_cost = Globals.ct.get_launcher_cost()
        if (MarketMaker.ti - ti_cost) < cls.reserve_ti * MarketMaker.scale_ratio:
            return False
        if (MarketMaker.ax - ax_cost) < cls.reserve_ax * MarketMaker.scale_ratio:
            Debug.log('ax branch triggered')
            return False
        return True


    @staticmethod
    def build_conveyor(*a):
        Globals.ct.build_conveyor(*a)

    @staticmethod
    def dbuild_conveyor(pos, *a):
        if Globals.ct.can_destroy(pos):
            Globals.ct.destroy(pos)
        Globals.ct.build_conveyor(pos, *a)

    @staticmethod
    def can_dbuild_conveyor(pos) -> bool:
        return (
            Globals.ct.get_action_cooldown() == 0 and
            BuildManager.is_dbuildable(pos) and 
            BuildManager.can_afford_conveyor()
        )

    @staticmethod
    def can_build_conveyor(*a) -> bool:
        return Globals.ct.can_build_conveyor(*a)

    @staticmethod
    def can_afford_conveyor() -> bool:
        ti_cost, ax_cost = Globals.ct.get_conveyor_cost()
        return MarketMaker.ti >= ti_cost and MarketMaker.ax >= ax_cost

    @classmethod
    def reserve_check_conveyor(cls) -> bool:
        ti_cost, ax_cost = Globals.ct.get_conveyor_cost()
        if (MarketMaker.ti - ti_cost) < cls.reserve_ti * MarketMaker.scale_ratio:
            return False
        if (MarketMaker.ax - ax_cost) < cls.reserve_ax * MarketMaker.scale_ratio:
            Debug.log('ax branch triggered')
            return False
        return True


    @staticmethod
    def build_splitter(*a):
        Globals.ct.build_splitter(*a)

    @staticmethod
    def dbuild_splitter(pos, *a):
        if Globals.ct.can_destroy(pos):
            Globals.ct.destroy(pos)
        Globals.ct.build_splitter(pos, *a)

    @staticmethod
    def can_dbuild_splitter(pos) -> bool:
        return (
            Globals.ct.get_action_cooldown() == 0 and
            BuildManager.is_dbuildable(pos) and 
            BuildManager.can_afford_splitter()
        )

    @staticmethod
    def can_build_splitter(*a) -> bool:
        return Globals.ct.can_build_splitter(*a)

    @staticmethod
    def can_afford_splitter() -> bool:
        ti_cost, ax_cost = Globals.ct.get_splitter_cost()
        return MarketMaker.ti >= ti_cost and MarketMaker.ax >= ax_cost

    @classmethod
    def reserve_check_splitter(cls) -> bool:
        ti_cost, ax_cost = Globals.ct.get_splitter_cost()
        if (MarketMaker.ti - ti_cost) < cls.reserve_ti * MarketMaker.scale_ratio:
            return False
        if (MarketMaker.ax - ax_cost) < cls.reserve_ax * MarketMaker.scale_ratio:
            Debug.log('ax branch triggered')
            return False
        return True


    @staticmethod
    def build_armoured_conveyor(*a):
        Globals.ct.build_armoured_conveyor(*a)

    @staticmethod
    def dbuild_armoured_conveyor(pos, *a):
        if Globals.ct.can_destroy(pos):
            Globals.ct.destroy(pos)
        Globals.ct.build_armoured_conveyor(pos, *a)

    @staticmethod
    def can_dbuild_armoured_conveyor(pos) -> bool:
        return (
            Globals.ct.get_action_cooldown() == 0 and
            BuildManager.is_dbuildable(pos) and 
            BuildManager.can_afford_armoured_conveyor()
        )

    @staticmethod
    def can_build_armoured_conveyor(*a) -> bool:
        return Globals.ct.can_build_armoured_conveyor(*a)

    @staticmethod
    def can_afford_armoured_conveyor() -> bool:
        ti_cost, ax_cost = Globals.ct.get_armoured_conveyor_cost()
        return MarketMaker.ti >= ti_cost and MarketMaker.ax >= ax_cost

    @classmethod
    def reserve_check_armoured_conveyor(cls) -> bool:
        ti_cost, ax_cost = Globals.ct.get_armoured_conveyor_cost()
        if (MarketMaker.ti - ti_cost) < cls.reserve_ti * MarketMaker.scale_ratio:
            return False
        if (MarketMaker.ax - ax_cost) < cls.reserve_ax * MarketMaker.scale_ratio:
            Debug.log('ax branch triggered')
            return False
        return True


    @staticmethod
    def build_bridge(*a):
        Globals.ct.build_bridge(*a)

    @staticmethod
    def dbuild_bridge(pos, *a):
        if Globals.ct.can_destroy(pos):
            Globals.ct.destroy(pos)
        Globals.ct.build_bridge(pos, *a)

    @staticmethod
    def can_dbuild_bridge(pos) -> bool:
        return (
            Globals.ct.get_action_cooldown() == 0 and
            BuildManager.is_dbuildable(pos) and 
            BuildManager.can_afford_bridge()
        )

    @staticmethod
    def can_build_bridge(*a) -> bool:
        return Globals.ct.can_build_bridge(*a)

    @staticmethod
    def can_afford_bridge() -> bool:
        ti_cost, ax_cost = Globals.ct.get_bridge_cost()
        return MarketMaker.ti >= ti_cost and MarketMaker.ax >= ax_cost

    @classmethod
    def reserve_check_bridge(cls) -> bool:
        ti_cost, ax_cost = Globals.ct.get_bridge_cost()
        if (MarketMaker.ti - ti_cost) < cls.reserve_ti * MarketMaker.scale_ratio:
            return False
        if (MarketMaker.ax - ax_cost) < cls.reserve_ax * MarketMaker.scale_ratio:
            Debug.log('ax branch triggered')
            return False
        return True


    @staticmethod
    def build_harvester(*a):
        Globals.ct.build_harvester(*a)

    @staticmethod
    def dbuild_harvester(pos, *a):
        if Globals.ct.can_destroy(pos):
            Globals.ct.destroy(pos)
        Globals.ct.build_harvester(pos, *a)

    @staticmethod
    def can_dbuild_harvester(pos) -> bool:
        return (
            Globals.ct.get_action_cooldown() == 0 and
            BuildManager.is_dbuildable(pos) and 
            BuildManager.can_afford_harvester()
        )

    @staticmethod
    def can_build_harvester(*a) -> bool:
        return Globals.ct.can_build_harvester(*a)

    @staticmethod
    def can_afford_harvester() -> bool:
        ti_cost, ax_cost = Globals.ct.get_harvester_cost()
        return MarketMaker.ti >= ti_cost and MarketMaker.ax >= ax_cost

    @classmethod
    def reserve_check_harvester(cls) -> bool:
        ti_cost, ax_cost = Globals.ct.get_harvester_cost()
        if (MarketMaker.ti - ti_cost) < cls.reserve_ti * MarketMaker.scale_ratio:
            return False
        if (MarketMaker.ax - ax_cost) < cls.reserve_ax * MarketMaker.scale_ratio:
            Debug.log('ax branch triggered')
            return False
        return True


    @staticmethod
    def build_foundry(*a):
        Globals.ct.build_foundry(*a)

    @staticmethod
    def dbuild_foundry(pos, *a):
        if Globals.ct.can_destroy(pos):
            Globals.ct.destroy(pos)
        Globals.ct.build_foundry(pos, *a)

    @staticmethod
    def can_dbuild_foundry(pos) -> bool:
        return (
            Globals.ct.get_action_cooldown() == 0 and
            BuildManager.is_dbuildable(pos) and 
            BuildManager.can_afford_foundry()
        )

    @staticmethod
    def can_build_foundry(*a) -> bool:
        return Globals.ct.can_build_foundry(*a)

    @staticmethod
    def can_afford_foundry() -> bool:
        ti_cost, ax_cost = Globals.ct.get_foundry_cost()
        return MarketMaker.ti >= ti_cost and MarketMaker.ax >= ax_cost

    @classmethod
    def reserve_check_foundry(cls) -> bool:
        ti_cost, ax_cost = Globals.ct.get_foundry_cost()
        if (MarketMaker.ti - ti_cost) < cls.reserve_ti * MarketMaker.scale_ratio:
            return False
        if (MarketMaker.ax - ax_cost) < cls.reserve_ax * MarketMaker.scale_ratio:
            Debug.log('ax branch triggered')
            return False
        return True


    @staticmethod
    def build_road(*a):
        Globals.ct.build_road(*a)

    @staticmethod
    def dbuild_road(pos, *a):
        if Globals.ct.can_destroy(pos):
            Globals.ct.destroy(pos)
        Globals.ct.build_road(pos, *a)

    @staticmethod
    def can_dbuild_road(pos) -> bool:
        return (
            Globals.ct.get_action_cooldown() == 0 and
            BuildManager.is_dbuildable(pos) and 
            BuildManager.can_afford_road()
        )

    @staticmethod
    def can_build_road(*a) -> bool:
        return Globals.ct.can_build_road(*a)

    @staticmethod
    def can_afford_road() -> bool:
        ti_cost, ax_cost = Globals.ct.get_road_cost()
        return MarketMaker.ti >= ti_cost and MarketMaker.ax >= ax_cost

    @classmethod
    def reserve_check_road(cls) -> bool:
        ti_cost, ax_cost = Globals.ct.get_road_cost()
        if (MarketMaker.ti - ti_cost) < cls.reserve_ti * MarketMaker.scale_ratio:
            return False
        if (MarketMaker.ax - ax_cost) < cls.reserve_ax * MarketMaker.scale_ratio:
            Debug.log('ax branch triggered')
            return False
        return True


    @staticmethod
    def build_barrier(*a):
        Globals.ct.build_barrier(*a)

    @staticmethod
    def dbuild_barrier(pos, *a):
        if Globals.ct.can_destroy(pos):
            Globals.ct.destroy(pos)
        Globals.ct.build_barrier(pos, *a)

    @staticmethod
    def can_dbuild_barrier(pos) -> bool:
        return (
            Globals.ct.get_action_cooldown() == 0 and
            BuildManager.is_dbuildable(pos) and 
            BuildManager.can_afford_barrier()
        )

    @staticmethod
    def can_build_barrier(*a) -> bool:
        return Globals.ct.can_build_barrier(*a)

    @staticmethod
    def can_afford_barrier() -> bool:
        ti_cost, ax_cost = Globals.ct.get_barrier_cost()
        return MarketMaker.ti >= ti_cost and MarketMaker.ax >= ax_cost

    @classmethod
    def reserve_check_barrier(cls) -> bool:
        ti_cost, ax_cost = Globals.ct.get_barrier_cost()
        if (MarketMaker.ti - ti_cost) < cls.reserve_ti * MarketMaker.scale_ratio:
            return False
        if (MarketMaker.ax - ax_cost) < cls.reserve_ax * MarketMaker.scale_ratio:
            Debug.log('ax branch triggered')
            return False
        return True


# ============================================================
# BuilderState
# ============================================================

class BuilderState(Enum):
    UNKNOWN = 0
    EXPLORE = 1
    ROUTE = 2
    BUILD_HARVESTER = 3


# ============================================================
# ClaudeGlobalBfs
# ============================================================

class ClaudeGlobalBfs:
    @classmethod
    def dists_from_pos(cls, pos: Position):
        W, H = Map.W, Map.H
        tile_info = Map.tile_info
        cur_round = Globals.ct.get_current_round()

        PH = H + 2
        INF = 1000000

        dist = [1000001] * ((W + 2) * PH)

        for x in range(W):
            col = tile_info[x]
            b = (x + 1) * PH + 1
            for y in range(H):
                ti = col[y]
                if ti is None or (
                    ti.env != Environment.WALL
                    and not (ti.has_bot and ti.round == cur_round)
                    and not (ti.has_building and ti.entity_type not in Constants.PASSABLE_SET)
                ):
                    # passable
                    dist[b + y] = 1000000

        si = (pos.x + 1) * PH + (pos.y + 1)
        dist[si] = 0

        _o0 = -1
        _o1 = PH-1
        _o2 = PH
        _o3 = PH+1
        _o4 = +1
        _o5 = -PH+1
        _o6 = -PH
        _o7 = -PH-1

        frontier = [si]
        d = 1
        while frontier:
            nxt = []
            _a = nxt.append
            for idx in frontier:
                ni = idx + _o0
                if dist[ni] == 1000000:
                    dist[ni] = d
                    _a(ni)
                ni = idx + _o1
                if dist[ni] == 1000000:
                    dist[ni] = d
                    _a(ni)
                ni = idx + _o2
                if dist[ni] == 1000000:
                    dist[ni] = d
                    _a(ni)
                ni = idx + _o3
                if dist[ni] == 1000000:
                    dist[ni] = d
                    _a(ni)
                ni = idx + _o4
                if dist[ni] == 1000000:
                    dist[ni] = d
                    _a(ni)
                ni = idx + _o5
                if dist[ni] == 1000000:
                    dist[ni] = d
                    _a(ni)
                ni = idx + _o6
                if dist[ni] == 1000000:
                    dist[ni] = d
                    _a(ni)
                ni = idx + _o7
                if dist[ni] == 1000000:
                    dist[ni] = d
                    _a(ni)
            frontier = nxt
            d += 1

        result = [[0] * (H + 1) for _ in range(W + 1)]
        for x in range(W + 1):
            row = result[x]
            base = (x + 1) * PH + 1
            for y in range(H + 1):
                v = dist[base + y]
                row[y] = 1000000 if v >= 1000000 else v
        return result


# ============================================================
# Color
# ============================================================

class Color:
    WHITE = (255, 255, 255)
    RED = (255, 0, 0)
    GREEN = (0, 255, 0)
    BLUE = (0, 0, 255)
    BLACK = (0, 0, 0)
    YELLOW = (255, 255, 0)
    CYAN = (0, 255, 255)
    MAGENTA = (255, 0, 255)
    ORANGE = (255, 165, 0)
    PINK = (255, 105, 180)
    PURPLE = (128, 0, 128)
    GRAY = (128, 128, 128)
    LIME = (0, 255, 128)
    TEAL = (0, 128, 128)
    BROWN = (139, 69, 19)


# ============================================================
# Constants
# ============================================================

class Constants:
    ALL_DIRECTIONS: list[Direction] = [
        Direction.NORTH,
        Direction.NORTHEAST,
        Direction.EAST,
        Direction.SOUTHEAST,
        Direction.SOUTH,
        Direction.SOUTHWEST,
        Direction.WEST,
        Direction.NORTHWEST,
        Direction.CENTRE
    ]
    DIRECTIONS: list[Direction] = [
        Direction.NORTH,
        Direction.NORTHEAST,
        Direction.EAST,
        Direction.SOUTHEAST,
        Direction.SOUTH,
        Direction.SOUTHWEST,
        Direction.WEST,
        Direction.NORTHWEST,
    ]
    TRANSPORTERS_SET: set[EntityType] = {
        EntityType.CONVEYOR,
        EntityType.ARMOURED_CONVEYOR,
        EntityType.BRIDGE,
        EntityType.SPLITTER,
    }
    PASSABLE_SET: set[EntityType] = {
        EntityType.ROAD,
        EntityType.CONVEYOR,
        EntityType.ARMOURED_CONVEYOR,
        EntityType.BRIDGE,
        EntityType.SPLITTER,
    }


# ============================================================
# Debug
# ============================================================

class Debug:
    @staticmethod
    def line(pos_a: Position, pos_b: Position | tuple | None = None, color: tuple = Color.WHITE):
        if pos_b is None:
            pos_b = pos_a
            pos_a = Globals.ct.get_position()
        elif isinstance(pos_b, tuple) and not isinstance(pos_b, Position):  # color tuple, not Position
            color = pos_b
            pos_b = pos_a
            pos_a = Globals.ct.get_position()
        Globals.ct.draw_indicator_line(pos_a, pos_b, *color)

    @staticmethod
    def diline(a: Position, b: Position, color: tuple = Color.WHITE):
        Globals.ct.draw_indicator_line(a, b, *color)
        Globals.ct.draw_indicator_dot(b, *color)

    @staticmethod
    def dot(pos: Position, color: tuple = Color.WHITE):
        Globals.ct.draw_indicator_dot(pos, *color)

    @staticmethod
    def log(*a, **kw):
        print(*a, **kw, file=sys.stderr)

    @staticmethod
    def tee(*a, **kw):
        print(*a, **kw)
        print(*a, **kw, file=sys.stderr)

    @staticmethod
    def error(thing):
        raise Exception(thing)

    @staticmethod
    def transpose[T](mat: list[list[T]]) -> str:
        if not mat or not mat[0]:
            return "[empty matrix]"

        rows = len(mat)
        cols = len(mat[0])

        return "\n".join(
            " ".join(str(mat[r][c]) for r in range(rows))
            for c in range(cols)
        )

    @staticmethod
    def debug_dist(dist: list[list[int]]):
        my_pos = Globals.ct.get_position()
        print("N:", 
              dist[my_pos.x +0][my_pos.y -1], end=', ')
        print("NE:", 
              dist[my_pos.x +1][my_pos.y -1], end=', ')
        print("E:", 
              dist[my_pos.x +1][my_pos.y +0], end=', ')
        print("SE:", 
              dist[my_pos.x +1][my_pos.y +1], end=', ')
        print("S:", 
              dist[my_pos.x +0][my_pos.y +1], end=', ')
        print("SW:", 
              dist[my_pos.x -1][my_pos.y +1], end=', ')
        print("W:", 
              dist[my_pos.x -1][my_pos.y +0], end=', ')
        print("NW:", 
              dist[my_pos.x -1][my_pos.y -1], end=', ')
        print("C:", 
              dist[my_pos.x +0][my_pos.y +0], end=', ')
        print()

    @staticmethod
    def diamond(color: tuple = Color.WHITE):
        c = Globals.ct.get_position()
        x, y = c.x, c.y

        top    = Position(x, y - 1)
        right  = Position(x + 1, y)
        bottom = Position(x, y + 1)
        left   = Position(x - 1, y)

        Globals.ct.draw_indicator_line(top, right, *color)
        Globals.ct.draw_indicator_line(right, bottom, *color)
        Globals.ct.draw_indicator_line(bottom, left, *color)
        Globals.ct.draw_indicator_line(left, top, *color)


# ============================================================
# DirectionPicker
# ============================================================

class DirectionPicker:
    class Candidate(NamedTuple):
        direction: Direction
        position: Position
        banned: bool
        moveable: bool
        fill_moveable: bool
        dist: int
        closer_than_center: bool
        rand_key: float

    cand: list[Candidate | None] = [None] * 9

    @classmethod
    def precompute(cls, dist: list[list[int]], ban_target_pos: bool = False):
        my_pos = Globals.ct.get_position()
        center_dist = dist[my_pos.x][my_pos.y]

        d = dist[my_pos.x +0][my_pos.y +0]
        cls.cand[8] = cls.Candidate(
            Direction.CENTRE,
            my_pos.add(Direction.CENTRE),
            ban_target_pos and d == 0,
            MoveManager.can_move(Direction.CENTRE),
            MoveManager.can_fill_move(Direction.CENTRE),
            d,
            d < center_dist,
            random.random(),
        )
        d = dist[my_pos.x -1][my_pos.y -1]
        cls.cand[7] = cls.Candidate(
            Direction.NORTHWEST,
            my_pos.add(Direction.NORTHWEST),
            ban_target_pos and d == 0,
            MoveManager.can_move(Direction.NORTHWEST),
            MoveManager.can_fill_move(Direction.NORTHWEST),
            d,
            d < center_dist,
            random.random(),
        )
        d = dist[my_pos.x -1][my_pos.y +0]
        cls.cand[6] = cls.Candidate(
            Direction.WEST,
            my_pos.add(Direction.WEST),
            ban_target_pos and d == 0,
            MoveManager.can_move(Direction.WEST),
            MoveManager.can_fill_move(Direction.WEST),
            d,
            d < center_dist,
            random.random(),
        )
        d = dist[my_pos.x -1][my_pos.y +1]
        cls.cand[5] = cls.Candidate(
            Direction.SOUTHWEST,
            my_pos.add(Direction.SOUTHWEST),
            ban_target_pos and d == 0,
            MoveManager.can_move(Direction.SOUTHWEST),
            MoveManager.can_fill_move(Direction.SOUTHWEST),
            d,
            d < center_dist,
            random.random(),
        )
        d = dist[my_pos.x +0][my_pos.y +1]
        cls.cand[4] = cls.Candidate(
            Direction.SOUTH,
            my_pos.add(Direction.SOUTH),
            ban_target_pos and d == 0,
            MoveManager.can_move(Direction.SOUTH),
            MoveManager.can_fill_move(Direction.SOUTH),
            d,
            d < center_dist,
            random.random(),
        )
        d = dist[my_pos.x +1][my_pos.y +1]
        cls.cand[3] = cls.Candidate(
            Direction.SOUTHEAST,
            my_pos.add(Direction.SOUTHEAST),
            ban_target_pos and d == 0,
            MoveManager.can_move(Direction.SOUTHEAST),
            MoveManager.can_fill_move(Direction.SOUTHEAST),
            d,
            d < center_dist,
            random.random(),
        )
        d = dist[my_pos.x +1][my_pos.y +0]
        cls.cand[2] = cls.Candidate(
            Direction.EAST,
            my_pos.add(Direction.EAST),
            ban_target_pos and d == 0,
            MoveManager.can_move(Direction.EAST),
            MoveManager.can_fill_move(Direction.EAST),
            d,
            d < center_dist,
            random.random(),
        )
        d = dist[my_pos.x +1][my_pos.y -1]
        cls.cand[1] = cls.Candidate(
            Direction.NORTHEAST,
            my_pos.add(Direction.NORTHEAST),
            ban_target_pos and d == 0,
            MoveManager.can_move(Direction.NORTHEAST),
            MoveManager.can_fill_move(Direction.NORTHEAST),
            d,
            d < center_dist,
            random.random(),
        )
        d = dist[my_pos.x +0][my_pos.y -1]
        cls.cand[0] = cls.Candidate(
            Direction.NORTH,
            my_pos.add(Direction.NORTH),
            ban_target_pos and d == 0,
            MoveManager.can_move(Direction.NORTH),
            MoveManager.can_fill_move(Direction.NORTH),
            d,
            d < center_dist,
            random.random(),
        )

    @classmethod
    def is_better_than(cls, a: Candidate, b: Candidate) -> bool:
        if a.banned and (not b.banned):
            return False
        if (not a.banned) and b.banned:
            return True

        if a.fill_moveable and (not b.fill_moveable):
            return True
        if (not a.fill_moveable) and b.fill_moveable:
            return False

        if a.closer_than_center and (not b.closer_than_center):
             return True
        if (not a.closer_than_center) and b.closer_than_center:
             return False

        if a.moveable and (not b.moveable):
             return True
        if (not a.moveable) and b.moveable:
             return False

        if a.dist != b.dist:
            return a.dist < b.dist

        return a.rand_key < b.rand_key

    @classmethod
    def pick_best_candidate(cls, dist: list[list[int]], ban_target_pos: bool = False) -> Candidate:
        cls.precompute(dist, ban_target_pos)

        best = cls.cand[8]
        if cls.is_better_than(cls.cand[7], best):
            best = cls.cand[7]
        if cls.is_better_than(cls.cand[6], best):
            best = cls.cand[6]
        if cls.is_better_than(cls.cand[5], best):
            best = cls.cand[5]
        if cls.is_better_than(cls.cand[4], best):
            best = cls.cand[4]
        if cls.is_better_than(cls.cand[3], best):
            best = cls.cand[3]
        if cls.is_better_than(cls.cand[2], best):
            best = cls.cand[2]
        if cls.is_better_than(cls.cand[1], best):
            best = cls.cand[1]
        if cls.is_better_than(cls.cand[0], best):
            best = cls.cand[0]

        return best


# ============================================================
# EgoBridgeBfs
# ============================================================

class EgoBridgeBfs:
    # also unrolled

    @classmethod
    def find_bridge_route(cls, start: Position, core_pos_list: list[tuple[int, int]]):
        W, H = Map.W, Map.H
        WALL = Environment.WALL
        EMPTY = Environment.EMPTY

        tile_info = Map.tile_info
        PW = W + 2 * 3
        PH = H + 2 * 3

        # Initialize everything as blocked (INF+1), including padding border.
        # Then mark only passable game tiles as INF (unvisited).
        # This mirrors: blocked = [[True]*PH ...] then setting inner tiles.
        dist = [[1000001] * PH for _ in range(PW)]
        first_hop = [[None] * PH for _ in range(PW)]

        for x in range(W):
            col = tile_info[x]
            for y in range(H):
                ti = col[y]
                if not ((ti is not None) and (
                    ti.env != EMPTY or
                    (
                        ti.has_building and ti.entity_type != EntityType.MARKER and
                        (
                            (not ti.easily_passable) or
                            (not ti.is_building_ally)
                        )
                    )
                )):
                    dist[x + 3][y + 3] = 1000000

        sx, sy = start.x + 3, start.y + 3
        dist[sx][sy] = 0

        core_set = set()
        for cx, cy in core_pos_list:
            core_set.add((cx + 3, cy + 3))

        # First hop: knight moves + diagonal jumps + straight jumps (all bridge-range offsets we care about)

        q = deque()

        nx, ny = sx +3, sy 
        if dist[nx][ny] == 1000000:
            dist[nx][ny] = 1
            first_hop[nx][ny] = (nx - 3, ny - 3)
            if (nx, ny) in core_set:
                return 1, first_hop[nx][ny]
            q.append((nx, ny))
        nx, ny = sx -3, sy 
        if dist[nx][ny] == 1000000:
            dist[nx][ny] = 1
            first_hop[nx][ny] = (nx - 3, ny - 3)
            if (nx, ny) in core_set:
                return 1, first_hop[nx][ny]
            q.append((nx, ny))
        nx, ny = sx , sy +3
        if dist[nx][ny] == 1000000:
            dist[nx][ny] = 1
            first_hop[nx][ny] = (nx - 3, ny - 3)
            if (nx, ny) in core_set:
                return 1, first_hop[nx][ny]
            q.append((nx, ny))
        nx, ny = sx , sy -3
        if dist[nx][ny] == 1000000:
            dist[nx][ny] = 1
            first_hop[nx][ny] = (nx - 3, ny - 3)
            if (nx, ny) in core_set:
                return 1, first_hop[nx][ny]
            q.append((nx, ny))
        nx, ny = sx +2, sy +2
        if dist[nx][ny] == 1000000:
            dist[nx][ny] = 1
            first_hop[nx][ny] = (nx - 3, ny - 3)
            if (nx, ny) in core_set:
                return 1, first_hop[nx][ny]
            q.append((nx, ny))
        nx, ny = sx +2, sy -2
        if dist[nx][ny] == 1000000:
            dist[nx][ny] = 1
            first_hop[nx][ny] = (nx - 3, ny - 3)
            if (nx, ny) in core_set:
                return 1, first_hop[nx][ny]
            q.append((nx, ny))
        nx, ny = sx -2, sy -2
        if dist[nx][ny] == 1000000:
            dist[nx][ny] = 1
            first_hop[nx][ny] = (nx - 3, ny - 3)
            if (nx, ny) in core_set:
                return 1, first_hop[nx][ny]
            q.append((nx, ny))
        nx, ny = sx -2, sy +2
        if dist[nx][ny] == 1000000:
            dist[nx][ny] = 1
            first_hop[nx][ny] = (nx - 3, ny - 3)
            if (nx, ny) in core_set:
                return 1, first_hop[nx][ny]
            q.append((nx, ny))
        nx, ny = sx +1, sy +2
        if dist[nx][ny] == 1000000:
            dist[nx][ny] = 1
            first_hop[nx][ny] = (nx - 3, ny - 3)
            if (nx, ny) in core_set:
                return 1, first_hop[nx][ny]
            q.append((nx, ny))
        nx, ny = sx +2, sy +1
        if dist[nx][ny] == 1000000:
            dist[nx][ny] = 1
            first_hop[nx][ny] = (nx - 3, ny - 3)
            if (nx, ny) in core_set:
                return 1, first_hop[nx][ny]
            q.append((nx, ny))
        nx, ny = sx +2, sy -1
        if dist[nx][ny] == 1000000:
            dist[nx][ny] = 1
            first_hop[nx][ny] = (nx - 3, ny - 3)
            if (nx, ny) in core_set:
                return 1, first_hop[nx][ny]
            q.append((nx, ny))
        nx, ny = sx +1, sy -2
        if dist[nx][ny] == 1000000:
            dist[nx][ny] = 1
            first_hop[nx][ny] = (nx - 3, ny - 3)
            if (nx, ny) in core_set:
                return 1, first_hop[nx][ny]
            q.append((nx, ny))
        nx, ny = sx -1, sy -2
        if dist[nx][ny] == 1000000:
            dist[nx][ny] = 1
            first_hop[nx][ny] = (nx - 3, ny - 3)
            if (nx, ny) in core_set:
                return 1, first_hop[nx][ny]
            q.append((nx, ny))
        nx, ny = sx -2, sy -1
        if dist[nx][ny] == 1000000:
            dist[nx][ny] = 1
            first_hop[nx][ny] = (nx - 3, ny - 3)
            if (nx, ny) in core_set:
                return 1, first_hop[nx][ny]
            q.append((nx, ny))
        nx, ny = sx -2, sy +1
        if dist[nx][ny] == 1000000:
            dist[nx][ny] = 1
            first_hop[nx][ny] = (nx - 3, ny - 3)
            if (nx, ny) in core_set:
                return 1, first_hop[nx][ny]
            q.append((nx, ny))
        nx, ny = sx -1, sy +2
        if dist[nx][ny] == 1000000:
            dist[nx][ny] = 1
            first_hop[nx][ny] = (nx - 3, ny - 3)
            if (nx, ny) in core_set:
                return 1, first_hop[nx][ny]
            q.append((nx, ny))

        # Subsequent hops: (±2,±2) diagonals + (±3,0) and (0,±3) straights

        while q:
            x, y = q.popleft()
            d = dist[x][y] + 1

            nx, ny = x +3, y 
            if dist[nx][ny] == 1000000:
                dist[nx][ny] = d
                first_hop[nx][ny] = first_hop[x][y]

                if (nx, ny) in core_set:
                    return d, first_hop[nx][ny]

                q.append((nx, ny))
            nx, ny = x -3, y 
            if dist[nx][ny] == 1000000:
                dist[nx][ny] = d
                first_hop[nx][ny] = first_hop[x][y]

                if (nx, ny) in core_set:
                    return d, first_hop[nx][ny]

                q.append((nx, ny))
            nx, ny = x , y +3
            if dist[nx][ny] == 1000000:
                dist[nx][ny] = d
                first_hop[nx][ny] = first_hop[x][y]

                if (nx, ny) in core_set:
                    return d, first_hop[nx][ny]

                q.append((nx, ny))
            nx, ny = x , y -3
            if dist[nx][ny] == 1000000:
                dist[nx][ny] = d
                first_hop[nx][ny] = first_hop[x][y]

                if (nx, ny) in core_set:
                    return d, first_hop[nx][ny]

                q.append((nx, ny))
            nx, ny = x +2, y +2
            if dist[nx][ny] == 1000000:
                dist[nx][ny] = d
                first_hop[nx][ny] = first_hop[x][y]

                if (nx, ny) in core_set:
                    return d, first_hop[nx][ny]

                q.append((nx, ny))
            nx, ny = x +2, y -2
            if dist[nx][ny] == 1000000:
                dist[nx][ny] = d
                first_hop[nx][ny] = first_hop[x][y]

                if (nx, ny) in core_set:
                    return d, first_hop[nx][ny]

                q.append((nx, ny))
            nx, ny = x -2, y -2
            if dist[nx][ny] == 1000000:
                dist[nx][ny] = d
                first_hop[nx][ny] = first_hop[x][y]

                if (nx, ny) in core_set:
                    return d, first_hop[nx][ny]

                q.append((nx, ny))
            nx, ny = x -2, y +2
            if dist[nx][ny] == 1000000:
                dist[nx][ny] = d
                first_hop[nx][ny] = first_hop[x][y]

                if (nx, ny) in core_set:
                    return d, first_hop[nx][ny]

                q.append((nx, ny))

        return 1000000, None


# ============================================================
# Entrypoint
# ============================================================

class Entrypoint:
    me: type[Core | Builder]
    needs_init = True

    @classmethod
    def init(cls, ct: Controller):
        Globals.init(ct)
        Map.init()

        match ct.get_entity_type():
            case EntityType.CORE:
                Core.init()
                cls.me = Core
            case EntityType.BUILDER_BOT:
                Builder.init()
                cls.me = Builder

    @classmethod
    def run(cls, ct: Controller):
        Globals.ct = ct  # in case not fixed...
        if cls.needs_init:
            cls.init(ct)
            cls.needs_init = False

        cls.me.start_turn()
        cls.me.run_turn()
        cls.me.end_turn()


# ============================================================
# Explore
# ============================================================

class Explore:
    target: Position
    target = None

    @classmethod
    def init(cls) -> None:
        cls.target = cls.new_target()

    @classmethod
    def new_target(cls) -> Position:
        # return random.choice((Position(0, 0), Position(Map.W - 1, Map.H - 1)))
        # return Util.rand_pos()
        return random.choice((
            Position(0, 0),
            Position(0, Map.maxY),
            Position(Map.maxX, 0),
            Position(Map.maxX, Map.maxY),
        ))

    @classmethod
    def get_target(cls) -> Position:
        if Globals.ct.get_position().distance_squared(cls.target) <= 2:
            cls.target = cls.new_target()

        return cls.target


# ============================================================
# Globals
# ============================================================

class Globals:
    # const
    ct: Controller
    my_id: int
    my_team: Team
    
    # updating
    round: int

    @classmethod
    def init(cls, ct: Controller):
        cls.ct = ct
        cls.my_id = ct.get_id()
        cls.my_team = ct.get_team()

    @classmethod
    def start_tick(cls):
        cls.round = Globals.ct.get_current_round()


# ============================================================
# HealExecutor
# ============================================================

class HealExecutor:

    class Candidate(NamedTuple):
        position: Position
        score: int

    cand: list[Candidate | None] = [None] * 9

    max_hp_map: dict = {
        EntityType.BUILDER_BOT: 30,
        EntityType.CORE: 500,
        EntityType.GUNNER: 40,
        EntityType.SENTINEL: 30,
        EntityType.BREACH: 60,
        EntityType.LAUNCHER: 30,
        EntityType.CONVEYOR: 20,
        EntityType.SPLITTER: 20,
        EntityType.ARMOURED_CONVEYOR: 50,
        EntityType.BRIDGE: 20,
        EntityType.HARVESTER: 30,
        EntityType.FOUNDRY: 50,
        EntityType.ROAD: 10,
        EntityType.BARRIER: 30,
        EntityType.MARKER: 1,
    }

    @classmethod
    def precompute(cls):
        my_pos = Globals.ct.get_position()


        nx, ny = my_pos.x , my_pos.y -1
        npos = Position(nx, ny)

        if Globals.ct.can_heal(npos):
            ti = Map.tile_info[nx][ny]
            score = 0

            if ti.has_building:
                heal_hp = min(
                    10,  # should be 10
                    cls.max_hp_map[ti.entity_type] - ti.building_hp
                )
                score += heal_hp * 2 * (1 if ti.is_building_ally else -1)

            if ti.has_bot:
                heal_hp = min(
                    10,
                    30 - ti.bot_hp
                )
                score += heal_hp * (1 if ti.is_bot_ally else -1)

            cls.cand[0] = cls.Candidate(
                npos,
                score,
            )

        else:
            # cannot heal
            cls.cand[0] = cls.Candidate(
                npos,
                0,
            )

        nx, ny = my_pos.x +1, my_pos.y -1
        npos = Position(nx, ny)

        if Globals.ct.can_heal(npos):
            ti = Map.tile_info[nx][ny]
            score = 0

            if ti.has_building:
                heal_hp = min(
                    10,  # should be 10
                    cls.max_hp_map[ti.entity_type] - ti.building_hp
                )
                score += heal_hp * 2 * (1 if ti.is_building_ally else -1)

            if ti.has_bot:
                heal_hp = min(
                    10,
                    30 - ti.bot_hp
                )
                score += heal_hp * (1 if ti.is_bot_ally else -1)

            cls.cand[1] = cls.Candidate(
                npos,
                score,
            )

        else:
            # cannot heal
            cls.cand[1] = cls.Candidate(
                npos,
                0,
            )

        nx, ny = my_pos.x +1, my_pos.y 
        npos = Position(nx, ny)

        if Globals.ct.can_heal(npos):
            ti = Map.tile_info[nx][ny]
            score = 0

            if ti.has_building:
                heal_hp = min(
                    10,  # should be 10
                    cls.max_hp_map[ti.entity_type] - ti.building_hp
                )
                score += heal_hp * 2 * (1 if ti.is_building_ally else -1)

            if ti.has_bot:
                heal_hp = min(
                    10,
                    30 - ti.bot_hp
                )
                score += heal_hp * (1 if ti.is_bot_ally else -1)

            cls.cand[2] = cls.Candidate(
                npos,
                score,
            )

        else:
            # cannot heal
            cls.cand[2] = cls.Candidate(
                npos,
                0,
            )

        nx, ny = my_pos.x +1, my_pos.y +1
        npos = Position(nx, ny)

        if Globals.ct.can_heal(npos):
            ti = Map.tile_info[nx][ny]
            score = 0

            if ti.has_building:
                heal_hp = min(
                    10,  # should be 10
                    cls.max_hp_map[ti.entity_type] - ti.building_hp
                )
                score += heal_hp * 2 * (1 if ti.is_building_ally else -1)

            if ti.has_bot:
                heal_hp = min(
                    10,
                    30 - ti.bot_hp
                )
                score += heal_hp * (1 if ti.is_bot_ally else -1)

            cls.cand[3] = cls.Candidate(
                npos,
                score,
            )

        else:
            # cannot heal
            cls.cand[3] = cls.Candidate(
                npos,
                0,
            )

        nx, ny = my_pos.x , my_pos.y +1
        npos = Position(nx, ny)

        if Globals.ct.can_heal(npos):
            ti = Map.tile_info[nx][ny]
            score = 0

            if ti.has_building:
                heal_hp = min(
                    10,  # should be 10
                    cls.max_hp_map[ti.entity_type] - ti.building_hp
                )
                score += heal_hp * 2 * (1 if ti.is_building_ally else -1)

            if ti.has_bot:
                heal_hp = min(
                    10,
                    30 - ti.bot_hp
                )
                score += heal_hp * (1 if ti.is_bot_ally else -1)

            cls.cand[4] = cls.Candidate(
                npos,
                score,
            )

        else:
            # cannot heal
            cls.cand[4] = cls.Candidate(
                npos,
                0,
            )

        nx, ny = my_pos.x -1, my_pos.y +1
        npos = Position(nx, ny)

        if Globals.ct.can_heal(npos):
            ti = Map.tile_info[nx][ny]
            score = 0

            if ti.has_building:
                heal_hp = min(
                    10,  # should be 10
                    cls.max_hp_map[ti.entity_type] - ti.building_hp
                )
                score += heal_hp * 2 * (1 if ti.is_building_ally else -1)

            if ti.has_bot:
                heal_hp = min(
                    10,
                    30 - ti.bot_hp
                )
                score += heal_hp * (1 if ti.is_bot_ally else -1)

            cls.cand[5] = cls.Candidate(
                npos,
                score,
            )

        else:
            # cannot heal
            cls.cand[5] = cls.Candidate(
                npos,
                0,
            )

        nx, ny = my_pos.x -1, my_pos.y 
        npos = Position(nx, ny)

        if Globals.ct.can_heal(npos):
            ti = Map.tile_info[nx][ny]
            score = 0

            if ti.has_building:
                heal_hp = min(
                    10,  # should be 10
                    cls.max_hp_map[ti.entity_type] - ti.building_hp
                )
                score += heal_hp * 2 * (1 if ti.is_building_ally else -1)

            if ti.has_bot:
                heal_hp = min(
                    10,
                    30 - ti.bot_hp
                )
                score += heal_hp * (1 if ti.is_bot_ally else -1)

            cls.cand[6] = cls.Candidate(
                npos,
                score,
            )

        else:
            # cannot heal
            cls.cand[6] = cls.Candidate(
                npos,
                0,
            )

        nx, ny = my_pos.x -1, my_pos.y -1
        npos = Position(nx, ny)

        if Globals.ct.can_heal(npos):
            ti = Map.tile_info[nx][ny]
            score = 0

            if ti.has_building:
                heal_hp = min(
                    10,  # should be 10
                    cls.max_hp_map[ti.entity_type] - ti.building_hp
                )
                score += heal_hp * 2 * (1 if ti.is_building_ally else -1)

            if ti.has_bot:
                heal_hp = min(
                    10,
                    30 - ti.bot_hp
                )
                score += heal_hp * (1 if ti.is_bot_ally else -1)

            cls.cand[7] = cls.Candidate(
                npos,
                score,
            )

        else:
            # cannot heal
            cls.cand[7] = cls.Candidate(
                npos,
                0,
            )

        nx, ny = my_pos.x , my_pos.y 
        npos = Position(nx, ny)

        if Globals.ct.can_heal(npos):
            ti = Map.tile_info[nx][ny]
            score = 0

            if ti.has_building:
                heal_hp = min(
                    10,  # should be 10
                    cls.max_hp_map[ti.entity_type] - ti.building_hp
                )
                score += heal_hp * 2 * (1 if ti.is_building_ally else -1)

            heal_hp = min(
                10,
                30 - Globals.ct.get_hp()
            )
            score += heal_hp

            cls.cand[8] = cls.Candidate(
                npos,
                score,
            )

        else:
            # cannot heal
            cls.cand[8] = cls.Candidate(
                npos,
                0,
            )
    

    @classmethod
    def execute_heal_attempt(cls):
        if Globals.ct.get_action_cooldown() != 0:
            return

        cls.precompute()

        cand: HealExecutor.Candidate = max(cls.cand, key=lambda c: c.score)
        if cand.score <= 0:
            return

        Debug.line(cand.position, Color.LIME)
        Globals.ct.heal(cand.position)


# ============================================================
# Map
# ============================================================

class Map:
    W: int
    H: int
    maxX: int
    maxY: int

    # [x][y], 1 None buffer on bot sides
    tile_info: list[list[TileInfo | None]]
    nearby_tiles: list[Position]
    nearby_ally_bots: int
    nearby_enemy_bots: int

    @staticmethod
    def init():
        Map.W = Globals.ct.get_map_width()
        Map.H = Globals.ct.get_map_height()
        Map.maxX = Map.W - 1
        Map.maxY = Map.H - 1

        Profiler.start()
        Map.tile_info = [[None] * (Map.H+1) for _ in range(Map.W+1)]
        Profiler.end('tile_info init')

    @classmethod
    def fill_tile_info(cls):
        ct = Globals.ct
        round = ct.get_current_round()
        tile_info = cls.tile_info

        cls.nearby_ally_bots = 0
        cls.nearby_enemy_bots = 0
        cls.nearby_tiles = ct.get_nearby_tiles(20)

        for pos in cls.nearby_tiles:
            tile_env: Environment = ct.get_tile_env(pos)

            ti: TileInfo | None = tile_info[pos.x][pos.y]
            if ti is None:
                ti = TileInfo()
                tile_info[pos.x][pos.y] = ti

            ti.env = tile_env
            ti.round = round

            building_id: int | None = ct.get_tile_building_id(pos)
            bot_id: int | None = ct.get_tile_builder_bot_id(pos)

            etype = None
            ti.has_building = (
                building_id is not None and 
                (etype := ct.get_entity_type(building_id)) != EntityType.MARKER
            )
            ti.entity_type = etype

            ti.has_bot = bot_id is not None and bot_id != Globals.my_id

            if ti.has_bot:
                ti.bot_hp = ct.get_hp(bot_id)
                ti.is_bot_ally = ct.get_team(bot_id) == Globals.my_team

                if ti.is_bot_ally:
                    cls.nearby_ally_bots += 1
                else:
                    cls.nearby_enemy_bots += 1

            ti.easily_passable = False

            if ti.has_building:
                ti.is_building_ally = ct.get_team(
                    building_id) == Globals.my_team
                ti.building_hp = ct.get_hp(building_id)

                if (etype in Constants.PASSABLE_SET or (
                        etype == EntityType.CORE
                        and ti.is_building_ally
                )):
                    ti.easily_passable = True


# ============================================================
# MarketMaker
# ============================================================

class MarketMaker:
    ti: int
    ax: int
    scale_ratio: float

    ti_hist: list[int] = [GameConstants.STARTING_TITANIUM] * 20
    ti_diff_hist: list[int] = [0] * 20
    est_income: int

    @classmethod
    def refresh(cls):
        cls.scale_ratio = Globals.ct.get_scale_percent() / 100.0
        cls.ti, MarketMaker.ax = Globals.ct.get_global_resources()

        idx = Globals.round % 20
        cls.ti_hist[idx] = cls.ti
        cls.ti_diff_hist[idx] = cls.ti - cls.ti_hist[
            idx-1 if idx-1 >= 0 else idx-1+20
        ]
        cls.est_income = max(cls.ti_diff_hist)

    @staticmethod
    def harvester_payback(apos: Position) -> int:
        # harvesters produce at 10/4 = 2.5 ti/round when built
        l1 = abs(apos.x - Unit.core_pos.x) + abs(apos.y - Unit.core_pos.y)

        h_cost, _ = Globals.ct.get_harvester_cost()
        c_cost, _ = Globals.ct.get_conveyor_cost()
        cost = h_cost + c_cost * l1

        return int(cost / 2.5) + l1

    @staticmethod
    def should_build_harvester(apos: Position) -> int:
        pbt = MarketMaker.harvester_payback(apos)
        if int(pbt * 1.5 + 50) < Util.get_rounds_left():
            return True
        return False


# ============================================================
# MoveManager
# ============================================================

class MoveManager:
    @staticmethod
    def can_move(direction: Direction) -> bool:
        if direction == Direction.CENTRE:
            return True
        return Globals.ct.can_move(direction)

    @staticmethod
    def can_fill_move(direction: Direction) -> bool:
        if MoveManager.can_move(direction):
            return True
        if Globals.ct.get_action_cooldown() != 0:
            return False

        pos: Position = Globals.ct.get_position().add(direction)
        if not Util.on_the_map(pos):
            return False

        if not Globals.ct.can_build_road(pos):
            return False

        ti: TileInfo = Map.tile_info[pos.x][pos.y]  # type: ignore
        if ti.has_building or ti.has_bot:
            return False

        return True


    @staticmethod
    def move(direction: Direction):
        if direction == Direction.CENTRE:
            return
        Globals.ct.move(direction)


# ============================================================
# MyGlobalBfs
# ============================================================

class MyGlobalBfs:
    dist: list[int]  # (x,y) -> (x + 1) * 52 + (y + 1)

    @classmethod
    def init(cls):
        W, H = Map.W, Map.H
        cls.dist = [1000000] * 2704

        # 1-thick border around game area: ~2*(W+H+2) ops
        for i in range(H + 2):
            cls.dist[i] = 1000001                       # x=-1 column
            cls.dist[(W + 1) * 52 + i] = 1000001  # x=W column
        for x in range(1, W + 1):
            base = x * 52
            cls.dist[base] = 1000001                     # y=-1 row
            cls.dist[base + H + 1] = 1000001             # y=H row

    @classmethod
    def update(cls):
        tile_info = Map.tile_info
        _dist = cls.dist
        for pos in Map.nearby_tiles:
            ti = tile_info[pos.x][pos.y]
            idx = (pos.x + 1) * 52 + (pos.y + 1)

            if (
                ti.env != Environment.WALL
                and not (ti.has_building and ti.entity_type not in Constants.PASSABLE_SET)
            ):
                _dist[idx] = 1000000
            else:
                _dist[idx] = 1000001

    @classmethod
    def dists_from_pos(cls, pos: Position):
        dist = cls.dist[:]

        si = (pos.x + 1) * 52 + (pos.y + 1)
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
                ni = idx + 51
                if dist[ni] == 1000000:
                    dist[ni] = d
                    _a(ni)
                ni = idx + 52
                if dist[ni] == 1000000:
                    dist[ni] = d
                    _a(ni)
                ni = idx + 53
                if dist[ni] == 1000000:
                    dist[ni] = d
                    _a(ni)
                ni = idx + 1
                if dist[ni] == 1000000:
                    dist[ni] = d
                    _a(ni)
                ni = idx + -51
                if dist[ni] == 1000000:
                    dist[ni] = d
                    _a(ni)
                ni = idx + -52
                if dist[ni] == 1000000:
                    dist[ni] = d
                    _a(ni)
                ni = idx + -53
                if dist[ni] == 1000000:
                    dist[ni] = d
                    _a(ni)
            frontier = nxt
            d += 1

        result = [[0] * (Map.H + 1) for _ in range(Map.W + 1)]
        for x in range(Map.W + 1):
            row = result[x]
            base = (x + 1) * 52 + 1
            for y in range(Map.H + 1):
                v = dist[base + y]
                row[y] = 1000000 if v >= 1000000 else v
        return result


# ============================================================
# MyGlobalBfs2
# ============================================================

class MyGlobalBfs2:
    dist: list[list[int]]  # (x,y) -> dist[x + 1][y + 1]

    @classmethod
    def init(cls):
        W, H = Map.W, Map.H
        # All passable, with 1-thick impassable border
        cls.dist = [[1000000] * 52 for _ in range(52)]

        # Border columns
        for y in range(H + 2):
            cls.dist[0][y] = 1000001
            cls.dist[W + 1][y] = 1000001
        # Border rows
        for x in range(1, W + 1):
            cls.dist[x][0] = 1000001
            cls.dist[x][H + 1] = 1000001

    @classmethod
    def update(cls):
        tile_info = Map.tile_info
        _dist = cls.dist
        for pos in Map.nearby_tiles:
            ti = tile_info[pos.x][pos.y]
            col = _dist[pos.x + 1]

            if (
                ti.env != Environment.WALL
                and not (ti.has_building and ti.entity_type not in Constants.PASSABLE_SET)
            ):
                col[pos.y + 1] = 1000000
            else:
                col[pos.y + 1] = 1000001

    @classmethod
    def dists_from_pos(cls, pos: Position):
        # Deep copy the 2D grid
        dist = [row[:] for row in cls.dist]

        sx = pos.x + 1
        sy = pos.y + 1
        dist[sx][sy] = 0

        frontier = [(sx, sy)]
        d = 1
        while frontier:
            nxt = []
            _a = nxt.append
            for cx, cy in frontier:
                nx = cx + 0
                ny = cy + -1
                if dist[nx][ny] == 1000000:
                    dist[nx][ny] = d
                    _a((nx, ny))
                nx = cx + 1
                ny = cy + -1
                if dist[nx][ny] == 1000000:
                    dist[nx][ny] = d
                    _a((nx, ny))
                nx = cx + 1
                ny = cy + 0
                if dist[nx][ny] == 1000000:
                    dist[nx][ny] = d
                    _a((nx, ny))
                nx = cx + 1
                ny = cy + 1
                if dist[nx][ny] == 1000000:
                    dist[nx][ny] = d
                    _a((nx, ny))
                nx = cx + 0
                ny = cy + 1
                if dist[nx][ny] == 1000000:
                    dist[nx][ny] = d
                    _a((nx, ny))
                nx = cx + -1
                ny = cy + 1
                if dist[nx][ny] == 1000000:
                    dist[nx][ny] = d
                    _a((nx, ny))
                nx = cx + -1
                ny = cy + 0
                if dist[nx][ny] == 1000000:
                    dist[nx][ny] = d
                    _a((nx, ny))
                nx = cx + -1
                ny = cy + -1
                if dist[nx][ny] == 1000000:
                    dist[nx][ny] = d
                    _a((nx, ny))
            frontier = nxt
            d += 1

        result = [[0] * (Map.H + 1) for _ in range(Map.W + 1)]
        for x in range(Map.W + 1):
            row = result[x]
            dcol = dist[x + 1]
            for y in range(Map.H + 1):
                v = dcol[y + 1]
                row[y] = 1000000 if v >= 1000000 else v
        return result


# ============================================================
# OreExecutive
# ============================================================

class OreExecutive:
    banned: set[tuple[int, int]] = set()

    @classmethod
    def find_ore_to_mine(cls) -> Position | None:
        # TODO: passable check
        ct = Globals.ct
        tile_info = Map.tile_info

        for pos in Map.nearby_tiles:
            ti = tile_info[pos.x][pos.y]
            env = ti.env
            if env != Environment.ORE_TITANIUM and env != Environment.ORE_AXIONITE:
                continue
            if ti.entity_type == EntityType.HARVESTER:
                continue

            return pos

        return None

    @classmethod
    def go_build_harvester(cls, pos):
        Pathfinder.move_to(pos, ban_target_pos=True)
        if BuildManager.can_dbuild_harvester(pos):
            Debug.line(pos, Color.YELLOW)
            BuildManager.dbuild_harvester(pos)

            cand: OrePositionPicker.Candidate = OrePositionPicker.pick_best_candidate(pos)
            RouteToCore.set_pos(cand.position)


# ============================================================
# OrePositionPicker
# ============================================================

class OrePositionPicker:
    class Candidate(NamedTuple):
        position: Position
        ti: TileInfo | None  # if None, it is outside map
        build_metric: int  # manhattan, but if directly on top, need to ~take a step back~

    cand: list[Candidate | None] = [None] * 4

    @classmethod
    def precompute(cls, ore_pos: Position):
        my_pos = Globals.ct.get_position()
        me_x, me_y = my_pos.x, my_pos.y

        x, y = ore_pos.x, ore_pos.y


        nx, ny = x , y -1

        build_metric = max(abs(nx - me_x), abs(ny - me_y)) 
        if build_metric == 0:
            build_metric += 2

        cls.cand[0] = cls.Candidate(
            Position(nx, ny),
            Map.tile_info[nx][ny],
            build_metric,
        )

        nx, ny = x +1, y 

        build_metric = max(abs(nx - me_x), abs(ny - me_y)) 
        if build_metric == 0:
            build_metric += 2

        cls.cand[1] = cls.Candidate(
            Position(nx, ny),
            Map.tile_info[nx][ny],
            build_metric,
        )

        nx, ny = x , y +1

        build_metric = max(abs(nx - me_x), abs(ny - me_y)) 
        if build_metric == 0:
            build_metric += 2

        cls.cand[2] = cls.Candidate(
            Position(nx, ny),
            Map.tile_info[nx][ny],
            build_metric,
        )

        nx, ny = x -1, y 

        build_metric = max(abs(nx - me_x), abs(ny - me_y)) 
        if build_metric == 0:
            build_metric += 2

        cls.cand[3] = cls.Candidate(
            Position(nx, ny),
            Map.tile_info[nx][ny],
            build_metric,
        )

    @classmethod
    def is_better_than(cls, a: Candidate, b: Candidate) -> bool:
        # prio:
        # 1. on map
        # 2. empty
        # 3. no building
        # 4. has ally building AND is road
        # 5. no builder bot
        # 6. build metric
        # 7. arbitrary

        if a.ti is None and (b.ti is not None):
            return False
        if (a.ti is not None) and b.ti is None:
            return True

        EMPTY = Environment.EMPTY

        if a.ti.env == EMPTY and b.ti.env != EMPTY:
            return True
        if a.ti.env != EMPTY and b.ti.env == EMPTY:
            return False

        if a.ti.has_building and (not b.ti.has_building):
            return False
        if (not a.ti.has_building) and b.ti.has_building:
            return True

        if a.ti.has_building and b.ti.has_building:
            ROAD = EntityType.ROAD
            a_cond = a.ti.is_building_ally and a.ti.entity_type == ROAD
            b_cond = b.ti.is_building_ally and b.ti.entity_type == ROAD

            if a_cond and (not b_cond):
                return True
            if (not a_cond) and b_cond:
                return False

        if a.ti.has_bot and (not b.ti.has_bot):
            return False
        if (not a.ti.has_bot) and b.ti.has_bot:
            return True

        if a.build_metric != b.build_metric:
            return a.build_metric < b.build_metric

        return True  # arbitrary

    @classmethod
    def pick_best_candidate(cls, ore_pos: Position) -> Candidate:
        cls.precompute(ore_pos)

        best = cls.cand[3]
        if cls.is_better_than(cls.cand[2], best):
            best = cls.cand[2]
        if cls.is_better_than(cls.cand[1], best):
            best = cls.cand[1]
        if cls.is_better_than(cls.cand[0], best):
            best = cls.cand[0]

        return best


# ============================================================
# Pathfinder
# ============================================================

class Pathfinder:
    @classmethod
    def move_to(cls, target: Position, ban_target_pos: bool = False):
        if Globals.ct.get_move_cooldown() != 0:
            return


        # Profiler.start()
        # dist = UnrolledGlobalBfs.dists_from_pos(target)
        # Profiler.end("UnrolledGlobalBfs")


        # Profiler.start()
        # dist = MyGlobalBfs.dists_from_pos(target)
        # Profiler.end("MyGlobalBfs")

        # Profiler.start()
        # dist = ClaudeGlobalBfs.dists_from_pos(target)
        # Profiler.end("ClaudeGlobalBfs")

        Profiler.start()
        dist = MyGlobalBfs.dists_from_pos(target)
        Profiler.end("MyGlobalBfs")

        Profiler.start()
        dist = MyGlobalBfs2.dists_from_pos(target)
        Profiler.end("MyGlobalBfs2222")

        Profiler.start()
        dist = BfsBureau.dists_from_pos(target)
        Profiler.end("BfsBureau")

        # Profiler.start()
        cand: DirectionPicker.Candidate = DirectionPicker.pick_best_candidate(dist, ban_target_pos)
        # Profiler.end("DirectionPicker")

        print()
        print('with ban_target_pos as', ban_target_pos)
        print(cand)

        if cand.moveable:
            assert MoveManager.can_move(cand.direction)
            MoveManager.move(cand.direction)
        elif cand.fill_moveable:
            assert MoveManager.can_fill_move(cand.direction)
            Globals.ct.build_road(cand.position)
            MoveManager.move(cand.direction)


# ============================================================
# Player
# ============================================================

class Player:
    def run(self, ct):
        try:
            Entrypoint.run(ct)
        except Exception as e:
            Debug.line(Position(0, 0), Color.RED)

            err = traceback.format_exc()
            Debug.tee(err)


# ============================================================
# Profiler
# ============================================================

class Profiler:
    _stack: list = []
    _stats: dict = {}  # desc -> [count, mean, M2, max]

    @classmethod
    def start(cls):
        cls._stack.append(time.perf_counter())

    @classmethod
    def end(cls, desc: str):
        end_time = time.perf_counter()
        if not cls._stack:
            return
        start_time = cls._stack.pop()
        elapsed = end_time - start_time
        if desc in cls._stats:
            entry = cls._stats[desc]
            entry[0] += 1
            delta = elapsed - entry[1]
            entry[1] += delta / entry[0]
            entry[2] += delta * (elapsed - entry[1])
            if elapsed > entry[3]:
                entry[3] = elapsed
        else:
            cls._stats[desc] = [1, elapsed, 0.0, elapsed]

        s = f"[P] {desc}: {cls._format_time(elapsed)}"
        print(s)

    @classmethod
    def end_now(cls, desc: str):
        end_time = time.perf_counter()
        if not cls._stack:
            return
        start_time = cls._stack.pop()
        elapsed = end_time - start_time

        s = f"[P] {desc}: {cls._format_time(elapsed)}"
        print(s)
        Debug.log(s)

    @classmethod
    def _format_time(cls, t: float) -> str:
        if t < 1e-6:
            return f"{t * 1e9:.3f}ns"
        elif t < 1e-3:
            return f"{t * 1e6:.3f}µs"
        elif t < 1:
            return f"{t * 1e3:.3f}ms"
        else:
            return f"{t:.3f}s"

    @classmethod
    def report(cls):
        if not cls._stats:
            return
        Debug.tee(" *  Profiling report:")
        for desc, (count, mean, M2, max_time) in sorted(cls._stats.items()):
            stddev = math.sqrt(M2 / count) if count > 1 else 0.0
            s = (f"[P] {desc}: "
                 f"avg={cls._format_time(mean)}, "
                 f"stddev={cls._format_time(stddev)}, "
                 f"max={cls._format_time(max_time)}, "
                 f"count={count}")
            Debug.tee(s)

    @classmethod
    def reset(cls):
        cls._stack.clear()
        cls._stats.clear()


# ============================================================
# RouteToCore
# ============================================================

class RouteToCore:
    is_active: bool = False
    from_pos: Position

    @classmethod
    def set_pos(cls, pos: Position):
        if (pos.x, pos.y) in Unit.core_pos_list:
            cls.is_active = False
            return

        cls.is_active = True
        cls.from_pos = pos

    @classmethod
    def try_build_route(cls):
        assert cls.is_active

        Profiler.start()
        bridge_dist, first_target = EgoBridgeBfs.find_bridge_route(
            cls.from_pos,
            Unit.core_pos_list
        )
        Profiler.end("EgoBridgeBfs")

        Profiler.start()
        bridge_dist, first_target = BfsBureau.find_bridge_route(
            cls.from_pos,
            Unit.core_pos_list
        )
        Profiler.end("BfsBureau.bridge")


        if first_target is None:
            Debug.tee("first_target is None")
            return

        target = Position(*first_target)
        Debug.diline(cls.from_pos, target, Color.GREEN)

        if cls.from_pos.distance_squared(target) == 1:
            if BuildManager.can_dbuild_conveyor(cls.from_pos):
                BuildManager.dbuild_conveyor(cls.from_pos, cls.from_pos.direction_to(target))
                cls.set_pos(target)
        elif BuildManager.can_dbuild_bridge(cls.from_pos):
            BuildManager.dbuild_bridge(cls.from_pos, target)
            cls.set_pos(target)

    @classmethod
    def move_to_next(cls):
        Pathfinder.move_to(cls.from_pos, ban_target_pos=True)

    @classmethod
    def should_give_up(cls):
        x, y = cls.from_pos
        ti = Map.tile_info[x][y]
        if ti is None:
            return False

        if ti.has_building:
            if not ti.is_building_ally:
                return True
            if ti.entity_type in Constants.TRANSPORTERS_SET:
                return True
            if ti.entity_type != EntityType.ROAD:  # redundant
                return True
        return False

    @classmethod
    def do_routing(cls):
        if cls.should_give_up():
            cls.is_active = False
            Debug.diamond(Color.PURPLE)
            return

        dsq = Globals.ct.get_position().distance_squared(cls.from_pos)
        if Globals.ct.get_action_cooldown() == 0 \
                and (dsq == 1 or dsq == 2):
            cls.try_build_route()
            cls.move_to_next()
        else:
            cls.move_to_next()


# ============================================================
# SuicideExecutor
# ============================================================

class SuicideExecutor:
    @staticmethod
    def execute_suicide_attempt():
        cond = MarketMaker.scale_ratio > 3
        strong_cond = MarketMaker.ti > 800 and MarketMaker.scale_ratio > 3 and Map.nearby_ally_bots > 5

        my_pos = Globals.ct.get_position()
        ti = Map.tile_info[my_pos.x][my_pos.y]

        if not (ti.has_building and not ti.is_building_ally):
            return

        if ti.entity_type in Constants.TRANSPORTERS_SET and cond:
            Globals.ct.self_destruct()

        if ti.entity_type == EntityType.ROAD and strong_cond:
            Globals.ct.self_destruct()


# ============================================================
# TileInfo
# ============================================================

class TileInfo:
    env: Environment
    round: int

    easily_passable: bool  # (allied core)/road/conveyor/bridge/splitter
    entity_type: EntityType | None

    has_building: bool  # non-marker building
    building_hp: int
    is_building_ally: bool

    has_bot: bool  # non-self builder bot
    bot_hp: int
    is_bot_ally: bool


# ============================================================
# Unit
# ============================================================

class Unit:
    core_pos: Position
    core_pos_list: list[tuple[int, int]]
    core_pos_set: set[tuple[int, int]]

    @staticmethod
    def init():
        MyGlobalBfs.init()
        MyGlobalBfs2.init()
        BfsBureau.init()

        core_id = Globals.ct.get_tile_building_id(Globals.ct.get_position())
        Unit.core_pos = Globals.ct.get_position(core_id)
        x = Unit.core_pos.x
        y = Unit.core_pos.y
        Unit.core_pos_list = [
            (x , y -1),
            (x +1, y -1),
            (x +1, y ),
            (x +1, y +1),
            (x , y +1),
            (x -1, y +1),
            (x -1, y ),
            (x -1, y -1),
            (x , y ),
        ]
        Unit.core_pos_set = set(Unit.core_pos_list)


    @classmethod
    def start_turn(cls):
        Globals.start_tick()
        MarketMaker.refresh()

        Profiler.start()
        Map.fill_tile_info()
        Profiler.end("fill_tile_info")

        Profiler.start()
        MyGlobalBfs.update()
        Profiler.end("MyGlobalBfs.update")

        MyGlobalBfs2.update()

        Profiler.start()
        BfsBureau.update()
        Profiler.end("BfsBureau.update")

    @classmethod
    def run_turn(cls):
        pass

    @classmethod
    def end_turn(cls):
        if Globals.round == 1999:
            Profiler.report()
        print(f'scale ratio {MarketMaker.scale_ratio:.2f}')


# ============================================================
# Util
# ============================================================

class Util:
    @staticmethod
    def on_the_map(pos: Position) -> bool:
        return 0 <= pos.x < Map.W and 0 <= pos.y < Map.H

    @staticmethod
    def rand_pos() -> Position:
        return Position(random.randrange(Map.W), random.randrange(Map.H))


    @staticmethod
    def is_cardinal(dir: Direction) -> bool:
        # not great, to optimise, create polyfill for Direction
        dx, dy = dir.delta()
        return (dx == 0) ^ (dy == 0)

    @staticmethod
    def is_diagonal(dir: Direction) -> bool:
        dx, dy = dir.delta()
        return dx != 0 and dy != 0

    @staticmethod
    def get_rounds_left() -> int:
        return 2000 - Globals.round


# ============================================================
# Builder
# ============================================================

class Builder(Unit):
    state: BuilderState | int
    state_map: dict

    @classmethod
    def init(cls):
        super().init()
        Explore.init()

        cls.state_map = {
            BuilderState.EXPLORE: cls.state_explore,
            BuilderState.BUILD_HARVESTER: cls.state_build_harvester,
            BuilderState.ROUTE: cls.state_route,
        }
        cls.state = BuilderState.EXPLORE


    @classmethod
    def start_turn(cls):
        super().start_turn()

    @classmethod
    def run_turn(cls):
        cls.state, pos = cls.determine_state()
        cls.state_map[cls.state](pos)

    @classmethod
    def end_turn(cls):
        super().end_turn()
        HealExecutor.execute_heal_attempt()

    @classmethod
    def state_explore(cls, pos):
        Pathfinder.move_to(pos, ban_target_pos=True)  # change to false

    @classmethod
    def state_route(cls, _):
        RouteToCore.do_routing()

    @classmethod
    def state_build_harvester(cls, pos):
        OreExecutive.go_build_harvester(pos)

    @classmethod
    def determine_state(cls):
        if RouteToCore.is_active:
            return BuilderState.ROUTE, None

        if MarketMaker.should_build_harvester(Globals.ct.get_position()):
            hpos = OreExecutive.find_ore_to_mine()
            if hpos is not None:
                return BuilderState.BUILD_HARVESTER, hpos

        return BuilderState.EXPLORE, Explore.get_target()


# ============================================================
# Core
# ============================================================

class Core(Unit):
    num_spawned: int = 0

    @classmethod
    def init(cls):
        super().init()

    @classmethod
    def start_turn(cls):
        super().start_turn()
        print(f'est income: {MarketMaker.est_income}')


    @classmethod
    def spawn(cls):
        # rework this
        pos = Globals.ct.get_position().add(random.choice(Constants.DIRECTIONS))
        if Globals.ct.can_spawn(pos):
            Globals.ct.spawn_builder(pos)
            cls.num_spawned += 1

    @classmethod
    def run_turn(cls):
        # if cls.num_spawned < 3 or MarketMaker.ti > 1000:
        if cls.num_spawned < 3:
            cls.spawn()

    @classmethod
    def end_turn(cls):
        super().end_turn()


