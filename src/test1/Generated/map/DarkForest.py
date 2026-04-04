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
# ===--- IMPORT



class TreeNode:
    __slots__ = ('up',)
    up: int | None  # can be detached. if None then is root


# total flow/harvester is set to 12 (LCM of 1,2,3,4)
# bottleneck of a route is 4 harvesters = 4 * 12 = 48 pressure




class DarkForest:
    nodes: list[TreeNode | None] = [None] * 3136
    kind: list[int] = [0] * 3136   # per-position sink class
    flow: list[int]        # flow in subtree (bottom-up)
    pressure: list[int]    # pressure at node (top-down, reset at sink boundaries)
    node_kind: list[int]   # propagated kind per node (top-down)
    sink_set: set[int]


    @classmethod
    def init(cls):
        if Globals.my_type == EntityType.BUILDER_BOT:
            for p in Unit.core_pos_set:
                cls.register_sink(p, 1)
            return

        if Globals.my_type in (EntityType.SENTINEL, EntityType.GUNNER):
            cls.register_sink((((Globals.my_pos.x) + 3) * 56 + ((Globals.my_pos.y) + 3)),
                              3)

    @classmethod
    def register_enemy_core(cls):
        for p in Symmetry.enemy_core_pos_set:  # from sym
            cls.register_sink(p, 2)

    @classmethod
    def remove_node(cls, u: int):
        # Destroy node u. Any node with up=u will be severed automagically in compute func.
        if cls.kind[u] == 1 or cls.kind[u] == 2:
            return 

        cls.nodes[u] = None
        cls.kind[u] = 0

    @classmethod
    def register_sink(cls, u: int, k: int):
        """Mark position u as a sink of class k and ensure a root node exists there."""
        cls.kind[u] = k
        ns = cls.nodes
        if ns[u] is None:
            n = TreeNode()
            n.up = None
            ns[u] = n
        else:
            ns[u].up = None  # sinks are roots


    @classmethod
    def add_edge(cls, u: int, v: int):
        # register (u,v) edge: u.up = v
        ns = cls.nodes
        if ns[u] is None:
            ns[u] = TreeNode()
        ns[u].up = v




# ---===
    @classmethod
    def debug_pressure(cls):
        """Draw dots: green=low, yellow=med, orange=high, red=saturated."""
        ns = cls.nodes
        pressure = cls.pressure
        ct = Globals.ct
        for x in range(50):
            for y in range(50):
                i = (((x) + 3) * 56 + ((y) + 3))
                if ns[i] is not None and pressure[i] > 0:
                    p = pressure[i]
                    if p <= 12:
                        ct.draw_indicator_dot(Position(x, y), 0, 255, 0)
                    elif p <= 24:
                        ct.draw_indicator_dot(Position(x, y), 255, 255, 0)
                    elif p <= 36:
                        ct.draw_indicator_dot(Position(x, y), 255, 128, 0)
                    else:
                        ct.draw_indicator_dot(Position(x, y), 255, 0, 0)
# ===---
# ---===
    @classmethod
    def debug_sink_set(cls):
        for i in cls.sink_set:
            Globals.ct.draw_indicator_dot(Position(((i) // 56 - 3), ((i) % 56 - 3)), 0, 255, 255)
# ===---
# ---===
    @classmethod
    def debug_enemy_core_connected(cls):
        """Draw magenta dots on nodes whose propagated kind is Kind.ENEMY_CORE."""
        ns = cls.nodes
        nk = cls.node_kind
        ct = Globals.ct
        for x in range(50):
            for y in range(50):
                i = (((x) + 3) * 56 + ((y) + 3))
                if ns[i] is not None and nk[i] == 2:
                    ct.draw_indicator_dot(Position(x, y), 255, 0, 255)
# ===---
# ---===
    @classmethod
    def debug_kind(cls):
        """Draw dots colored by propagated node_kind. Extends to any number of kinds."""
        ns = cls.nodes
        nk = cls.node_kind
        ct = Globals.ct
        _palette = (
            (128, 128, 128),  # 0: Kind.NONE (grey, never drawn)
            (0,   255, 0  ),  # 1: Kind.ALLY_CORE (green)
            (255, 0,   0  ),  # 2: Kind.ENEMY_CORE (red)
            (0,   128, 255),  # 3: (blue)
            (255, 255, 0  ),  # 4: (yellow)
            (255, 0,   255),  # 5: (magenta)
            (0,   255, 255),  # 6: (cyan)
            (255, 128, 0  ),  # 7: (orange)
            (128, 0,   255),  # 8: (purple)
            (128, 255, 0  ),  # 9: (lime)
        )
        _plen = len(_palette)
        for x in range(50):
            for y in range(50):
                i = (((x) + 3) * 56 + ((y) + 3))
                if ns[i] is not None:
                    k = nk[i]
                    if k:
                        if k < _plen:
                            r, g, b = _palette[k]
                        else:
                            hue = (k * 137) % 360
                            h6 = hue // 60
                            f = (hue % 60) * 255 // 60
                            if   h6 == 0: r, g, b = 255, f, 0
                            elif h6 == 1: r, g, b = 255 - f, 255, 0
                            elif h6 == 2: r, g, b = 0, 255, f
                            elif h6 == 3: r, g, b = 0, 255 - f, 255
                            elif h6 == 4: r, g, b = f, 0, 255
                            else:         r, g, b = 255, 0, 255 - f
                        ct.draw_indicator_dot(Position(x, y), r, g, b)
# ===---


# ---===
    @classmethod
    def fcompute(cls):

        ns = cls.nodes
        kind = cls.kind
        core_pos_set = Unit.core_pos_set
        harvesters = Map.harvester_set

        flow = [0] * 3136
        cc   = [0] * 3136

        # ── harvest → flow directly ──
        _sh = (0, 12, 6,
               4, 3)
        for h in harvesters:
            _n0 = h -1
            _e0 = ns[_n0] is not None
            _n1 = h +1
            _e1 = ns[_n1] is not None
            _n2 = h -56
            _e2 = ns[_n2] is not None
            _n3 = h +56
            _e3 = ns[_n3] is not None
            cnt = _e0 + _e1 + _e2 + _e3
            if cnt:
                s = _sh[cnt]
                if _e0: flow[_n0] += s
                if _e1: flow[_n1] += s
                if _e2: flow[_n2] += s
                if _e3: flow[_n3] += s

        # ── fix dead parents, indegree, collect active ──
        active = []
        aa = active.append
        if (t := ns[171]) is not None:
            aa(171)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[172]) is not None:
            aa(172)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[173]) is not None:
            aa(173)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[174]) is not None:
            aa(174)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[175]) is not None:
            aa(175)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[176]) is not None:
            aa(176)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[177]) is not None:
            aa(177)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[178]) is not None:
            aa(178)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[179]) is not None:
            aa(179)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[180]) is not None:
            aa(180)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[181]) is not None:
            aa(181)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[182]) is not None:
            aa(182)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[183]) is not None:
            aa(183)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[184]) is not None:
            aa(184)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[185]) is not None:
            aa(185)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[186]) is not None:
            aa(186)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[187]) is not None:
            aa(187)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[188]) is not None:
            aa(188)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[189]) is not None:
            aa(189)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[190]) is not None:
            aa(190)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[191]) is not None:
            aa(191)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[192]) is not None:
            aa(192)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[193]) is not None:
            aa(193)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[194]) is not None:
            aa(194)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[195]) is not None:
            aa(195)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[196]) is not None:
            aa(196)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[197]) is not None:
            aa(197)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[198]) is not None:
            aa(198)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[199]) is not None:
            aa(199)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[200]) is not None:
            aa(200)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[201]) is not None:
            aa(201)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[202]) is not None:
            aa(202)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[203]) is not None:
            aa(203)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[204]) is not None:
            aa(204)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[205]) is not None:
            aa(205)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[206]) is not None:
            aa(206)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[207]) is not None:
            aa(207)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[208]) is not None:
            aa(208)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[209]) is not None:
            aa(209)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[210]) is not None:
            aa(210)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[211]) is not None:
            aa(211)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[212]) is not None:
            aa(212)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[213]) is not None:
            aa(213)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[214]) is not None:
            aa(214)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[215]) is not None:
            aa(215)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[216]) is not None:
            aa(216)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[217]) is not None:
            aa(217)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[218]) is not None:
            aa(218)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[219]) is not None:
            aa(219)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[220]) is not None:
            aa(220)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[227]) is not None:
            aa(227)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[228]) is not None:
            aa(228)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[229]) is not None:
            aa(229)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[230]) is not None:
            aa(230)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[231]) is not None:
            aa(231)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[232]) is not None:
            aa(232)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[233]) is not None:
            aa(233)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[234]) is not None:
            aa(234)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[235]) is not None:
            aa(235)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[236]) is not None:
            aa(236)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[237]) is not None:
            aa(237)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[238]) is not None:
            aa(238)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[239]) is not None:
            aa(239)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[240]) is not None:
            aa(240)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[241]) is not None:
            aa(241)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[242]) is not None:
            aa(242)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[243]) is not None:
            aa(243)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[244]) is not None:
            aa(244)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[245]) is not None:
            aa(245)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[246]) is not None:
            aa(246)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[247]) is not None:
            aa(247)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[248]) is not None:
            aa(248)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[249]) is not None:
            aa(249)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[250]) is not None:
            aa(250)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[251]) is not None:
            aa(251)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[252]) is not None:
            aa(252)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[253]) is not None:
            aa(253)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[254]) is not None:
            aa(254)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[255]) is not None:
            aa(255)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[256]) is not None:
            aa(256)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[257]) is not None:
            aa(257)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[258]) is not None:
            aa(258)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[259]) is not None:
            aa(259)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[260]) is not None:
            aa(260)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[261]) is not None:
            aa(261)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[262]) is not None:
            aa(262)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[263]) is not None:
            aa(263)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[264]) is not None:
            aa(264)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[265]) is not None:
            aa(265)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[266]) is not None:
            aa(266)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[267]) is not None:
            aa(267)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[268]) is not None:
            aa(268)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[269]) is not None:
            aa(269)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[270]) is not None:
            aa(270)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[271]) is not None:
            aa(271)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[272]) is not None:
            aa(272)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[273]) is not None:
            aa(273)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[274]) is not None:
            aa(274)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[275]) is not None:
            aa(275)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[276]) is not None:
            aa(276)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[283]) is not None:
            aa(283)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[284]) is not None:
            aa(284)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[285]) is not None:
            aa(285)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[286]) is not None:
            aa(286)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[287]) is not None:
            aa(287)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[288]) is not None:
            aa(288)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[289]) is not None:
            aa(289)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[290]) is not None:
            aa(290)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[291]) is not None:
            aa(291)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[292]) is not None:
            aa(292)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[293]) is not None:
            aa(293)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[294]) is not None:
            aa(294)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[295]) is not None:
            aa(295)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[296]) is not None:
            aa(296)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[297]) is not None:
            aa(297)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[298]) is not None:
            aa(298)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[299]) is not None:
            aa(299)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[300]) is not None:
            aa(300)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[301]) is not None:
            aa(301)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[302]) is not None:
            aa(302)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[303]) is not None:
            aa(303)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[304]) is not None:
            aa(304)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[305]) is not None:
            aa(305)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[306]) is not None:
            aa(306)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[307]) is not None:
            aa(307)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[308]) is not None:
            aa(308)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[309]) is not None:
            aa(309)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[310]) is not None:
            aa(310)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[311]) is not None:
            aa(311)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[312]) is not None:
            aa(312)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[313]) is not None:
            aa(313)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[314]) is not None:
            aa(314)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[315]) is not None:
            aa(315)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[316]) is not None:
            aa(316)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[317]) is not None:
            aa(317)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[318]) is not None:
            aa(318)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[319]) is not None:
            aa(319)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[320]) is not None:
            aa(320)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[321]) is not None:
            aa(321)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[322]) is not None:
            aa(322)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[323]) is not None:
            aa(323)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[324]) is not None:
            aa(324)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[325]) is not None:
            aa(325)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[326]) is not None:
            aa(326)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[327]) is not None:
            aa(327)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[328]) is not None:
            aa(328)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[329]) is not None:
            aa(329)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[330]) is not None:
            aa(330)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[331]) is not None:
            aa(331)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[332]) is not None:
            aa(332)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[339]) is not None:
            aa(339)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[340]) is not None:
            aa(340)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[341]) is not None:
            aa(341)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[342]) is not None:
            aa(342)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[343]) is not None:
            aa(343)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[344]) is not None:
            aa(344)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[345]) is not None:
            aa(345)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[346]) is not None:
            aa(346)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[347]) is not None:
            aa(347)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[348]) is not None:
            aa(348)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[349]) is not None:
            aa(349)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[350]) is not None:
            aa(350)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[351]) is not None:
            aa(351)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[352]) is not None:
            aa(352)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[353]) is not None:
            aa(353)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[354]) is not None:
            aa(354)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[355]) is not None:
            aa(355)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[356]) is not None:
            aa(356)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[357]) is not None:
            aa(357)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[358]) is not None:
            aa(358)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[359]) is not None:
            aa(359)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[360]) is not None:
            aa(360)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[361]) is not None:
            aa(361)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[362]) is not None:
            aa(362)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[363]) is not None:
            aa(363)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[364]) is not None:
            aa(364)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[365]) is not None:
            aa(365)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[366]) is not None:
            aa(366)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[367]) is not None:
            aa(367)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[368]) is not None:
            aa(368)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[369]) is not None:
            aa(369)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[370]) is not None:
            aa(370)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[371]) is not None:
            aa(371)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[372]) is not None:
            aa(372)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[373]) is not None:
            aa(373)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[374]) is not None:
            aa(374)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[375]) is not None:
            aa(375)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[376]) is not None:
            aa(376)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[377]) is not None:
            aa(377)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[378]) is not None:
            aa(378)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[379]) is not None:
            aa(379)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[380]) is not None:
            aa(380)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[381]) is not None:
            aa(381)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[382]) is not None:
            aa(382)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[383]) is not None:
            aa(383)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[384]) is not None:
            aa(384)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[385]) is not None:
            aa(385)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[386]) is not None:
            aa(386)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[387]) is not None:
            aa(387)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[388]) is not None:
            aa(388)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[395]) is not None:
            aa(395)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[396]) is not None:
            aa(396)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[397]) is not None:
            aa(397)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[398]) is not None:
            aa(398)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[399]) is not None:
            aa(399)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[400]) is not None:
            aa(400)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[401]) is not None:
            aa(401)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[402]) is not None:
            aa(402)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[403]) is not None:
            aa(403)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[404]) is not None:
            aa(404)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[405]) is not None:
            aa(405)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[406]) is not None:
            aa(406)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[407]) is not None:
            aa(407)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[408]) is not None:
            aa(408)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[409]) is not None:
            aa(409)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[410]) is not None:
            aa(410)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[411]) is not None:
            aa(411)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[412]) is not None:
            aa(412)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[413]) is not None:
            aa(413)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[414]) is not None:
            aa(414)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[415]) is not None:
            aa(415)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[416]) is not None:
            aa(416)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[417]) is not None:
            aa(417)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[418]) is not None:
            aa(418)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[419]) is not None:
            aa(419)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[420]) is not None:
            aa(420)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[421]) is not None:
            aa(421)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[422]) is not None:
            aa(422)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[423]) is not None:
            aa(423)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[424]) is not None:
            aa(424)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[425]) is not None:
            aa(425)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[426]) is not None:
            aa(426)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[427]) is not None:
            aa(427)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[428]) is not None:
            aa(428)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[429]) is not None:
            aa(429)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[430]) is not None:
            aa(430)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[431]) is not None:
            aa(431)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[432]) is not None:
            aa(432)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[433]) is not None:
            aa(433)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[434]) is not None:
            aa(434)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[435]) is not None:
            aa(435)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[436]) is not None:
            aa(436)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[437]) is not None:
            aa(437)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[438]) is not None:
            aa(438)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[439]) is not None:
            aa(439)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[440]) is not None:
            aa(440)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[441]) is not None:
            aa(441)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[442]) is not None:
            aa(442)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[443]) is not None:
            aa(443)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[444]) is not None:
            aa(444)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[451]) is not None:
            aa(451)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[452]) is not None:
            aa(452)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[453]) is not None:
            aa(453)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[454]) is not None:
            aa(454)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[455]) is not None:
            aa(455)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[456]) is not None:
            aa(456)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[457]) is not None:
            aa(457)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[458]) is not None:
            aa(458)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[459]) is not None:
            aa(459)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[460]) is not None:
            aa(460)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[461]) is not None:
            aa(461)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[462]) is not None:
            aa(462)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[463]) is not None:
            aa(463)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[464]) is not None:
            aa(464)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[465]) is not None:
            aa(465)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[466]) is not None:
            aa(466)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[467]) is not None:
            aa(467)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[468]) is not None:
            aa(468)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[469]) is not None:
            aa(469)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[470]) is not None:
            aa(470)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[471]) is not None:
            aa(471)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[472]) is not None:
            aa(472)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[473]) is not None:
            aa(473)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[474]) is not None:
            aa(474)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[475]) is not None:
            aa(475)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[476]) is not None:
            aa(476)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[477]) is not None:
            aa(477)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[478]) is not None:
            aa(478)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[479]) is not None:
            aa(479)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[480]) is not None:
            aa(480)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[481]) is not None:
            aa(481)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[482]) is not None:
            aa(482)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[483]) is not None:
            aa(483)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[484]) is not None:
            aa(484)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[485]) is not None:
            aa(485)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[486]) is not None:
            aa(486)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[487]) is not None:
            aa(487)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[488]) is not None:
            aa(488)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[489]) is not None:
            aa(489)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[490]) is not None:
            aa(490)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[491]) is not None:
            aa(491)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[492]) is not None:
            aa(492)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[493]) is not None:
            aa(493)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[494]) is not None:
            aa(494)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[495]) is not None:
            aa(495)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[496]) is not None:
            aa(496)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[497]) is not None:
            aa(497)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[498]) is not None:
            aa(498)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[499]) is not None:
            aa(499)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[500]) is not None:
            aa(500)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[507]) is not None:
            aa(507)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[508]) is not None:
            aa(508)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[509]) is not None:
            aa(509)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[510]) is not None:
            aa(510)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[511]) is not None:
            aa(511)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[512]) is not None:
            aa(512)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[513]) is not None:
            aa(513)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[514]) is not None:
            aa(514)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[515]) is not None:
            aa(515)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[516]) is not None:
            aa(516)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[517]) is not None:
            aa(517)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[518]) is not None:
            aa(518)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[519]) is not None:
            aa(519)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[520]) is not None:
            aa(520)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[521]) is not None:
            aa(521)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[522]) is not None:
            aa(522)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[523]) is not None:
            aa(523)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[524]) is not None:
            aa(524)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[525]) is not None:
            aa(525)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[526]) is not None:
            aa(526)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[527]) is not None:
            aa(527)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[528]) is not None:
            aa(528)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[529]) is not None:
            aa(529)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[530]) is not None:
            aa(530)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[531]) is not None:
            aa(531)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[532]) is not None:
            aa(532)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[533]) is not None:
            aa(533)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[534]) is not None:
            aa(534)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[535]) is not None:
            aa(535)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[536]) is not None:
            aa(536)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[537]) is not None:
            aa(537)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[538]) is not None:
            aa(538)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[539]) is not None:
            aa(539)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[540]) is not None:
            aa(540)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[541]) is not None:
            aa(541)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[542]) is not None:
            aa(542)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[543]) is not None:
            aa(543)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[544]) is not None:
            aa(544)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[545]) is not None:
            aa(545)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[546]) is not None:
            aa(546)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[547]) is not None:
            aa(547)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[548]) is not None:
            aa(548)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[549]) is not None:
            aa(549)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[550]) is not None:
            aa(550)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[551]) is not None:
            aa(551)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[552]) is not None:
            aa(552)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[553]) is not None:
            aa(553)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[554]) is not None:
            aa(554)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[555]) is not None:
            aa(555)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[556]) is not None:
            aa(556)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[563]) is not None:
            aa(563)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[564]) is not None:
            aa(564)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[565]) is not None:
            aa(565)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[566]) is not None:
            aa(566)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[567]) is not None:
            aa(567)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[568]) is not None:
            aa(568)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[569]) is not None:
            aa(569)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[570]) is not None:
            aa(570)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[571]) is not None:
            aa(571)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[572]) is not None:
            aa(572)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[573]) is not None:
            aa(573)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[574]) is not None:
            aa(574)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[575]) is not None:
            aa(575)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[576]) is not None:
            aa(576)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[577]) is not None:
            aa(577)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[578]) is not None:
            aa(578)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[579]) is not None:
            aa(579)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[580]) is not None:
            aa(580)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[581]) is not None:
            aa(581)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[582]) is not None:
            aa(582)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[583]) is not None:
            aa(583)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[584]) is not None:
            aa(584)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[585]) is not None:
            aa(585)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[586]) is not None:
            aa(586)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[587]) is not None:
            aa(587)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[588]) is not None:
            aa(588)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[589]) is not None:
            aa(589)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[590]) is not None:
            aa(590)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[591]) is not None:
            aa(591)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[592]) is not None:
            aa(592)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[593]) is not None:
            aa(593)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[594]) is not None:
            aa(594)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[595]) is not None:
            aa(595)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[596]) is not None:
            aa(596)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[597]) is not None:
            aa(597)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[598]) is not None:
            aa(598)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[599]) is not None:
            aa(599)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[600]) is not None:
            aa(600)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[601]) is not None:
            aa(601)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[602]) is not None:
            aa(602)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[603]) is not None:
            aa(603)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[604]) is not None:
            aa(604)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[605]) is not None:
            aa(605)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[606]) is not None:
            aa(606)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[607]) is not None:
            aa(607)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[608]) is not None:
            aa(608)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[609]) is not None:
            aa(609)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[610]) is not None:
            aa(610)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[611]) is not None:
            aa(611)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[612]) is not None:
            aa(612)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[619]) is not None:
            aa(619)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[620]) is not None:
            aa(620)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[621]) is not None:
            aa(621)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[622]) is not None:
            aa(622)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[623]) is not None:
            aa(623)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[624]) is not None:
            aa(624)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[625]) is not None:
            aa(625)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[626]) is not None:
            aa(626)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[627]) is not None:
            aa(627)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[628]) is not None:
            aa(628)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[629]) is not None:
            aa(629)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[630]) is not None:
            aa(630)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[631]) is not None:
            aa(631)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[632]) is not None:
            aa(632)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[633]) is not None:
            aa(633)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[634]) is not None:
            aa(634)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[635]) is not None:
            aa(635)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[636]) is not None:
            aa(636)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[637]) is not None:
            aa(637)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[638]) is not None:
            aa(638)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[639]) is not None:
            aa(639)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[640]) is not None:
            aa(640)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[641]) is not None:
            aa(641)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[642]) is not None:
            aa(642)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[643]) is not None:
            aa(643)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[644]) is not None:
            aa(644)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[645]) is not None:
            aa(645)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[646]) is not None:
            aa(646)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[647]) is not None:
            aa(647)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[648]) is not None:
            aa(648)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[649]) is not None:
            aa(649)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[650]) is not None:
            aa(650)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[651]) is not None:
            aa(651)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[652]) is not None:
            aa(652)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[653]) is not None:
            aa(653)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[654]) is not None:
            aa(654)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[655]) is not None:
            aa(655)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[656]) is not None:
            aa(656)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[657]) is not None:
            aa(657)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[658]) is not None:
            aa(658)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[659]) is not None:
            aa(659)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[660]) is not None:
            aa(660)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[661]) is not None:
            aa(661)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[662]) is not None:
            aa(662)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[663]) is not None:
            aa(663)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[664]) is not None:
            aa(664)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[665]) is not None:
            aa(665)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[666]) is not None:
            aa(666)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[667]) is not None:
            aa(667)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[668]) is not None:
            aa(668)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[675]) is not None:
            aa(675)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[676]) is not None:
            aa(676)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[677]) is not None:
            aa(677)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[678]) is not None:
            aa(678)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[679]) is not None:
            aa(679)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[680]) is not None:
            aa(680)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[681]) is not None:
            aa(681)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[682]) is not None:
            aa(682)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[683]) is not None:
            aa(683)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[684]) is not None:
            aa(684)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[685]) is not None:
            aa(685)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[686]) is not None:
            aa(686)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[687]) is not None:
            aa(687)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[688]) is not None:
            aa(688)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[689]) is not None:
            aa(689)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[690]) is not None:
            aa(690)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[691]) is not None:
            aa(691)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[692]) is not None:
            aa(692)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[693]) is not None:
            aa(693)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[694]) is not None:
            aa(694)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[695]) is not None:
            aa(695)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[696]) is not None:
            aa(696)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[697]) is not None:
            aa(697)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[698]) is not None:
            aa(698)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[699]) is not None:
            aa(699)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[700]) is not None:
            aa(700)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[701]) is not None:
            aa(701)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[702]) is not None:
            aa(702)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[703]) is not None:
            aa(703)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[704]) is not None:
            aa(704)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[705]) is not None:
            aa(705)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[706]) is not None:
            aa(706)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[707]) is not None:
            aa(707)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[708]) is not None:
            aa(708)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[709]) is not None:
            aa(709)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[710]) is not None:
            aa(710)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[711]) is not None:
            aa(711)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[712]) is not None:
            aa(712)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[713]) is not None:
            aa(713)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[714]) is not None:
            aa(714)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[715]) is not None:
            aa(715)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[716]) is not None:
            aa(716)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[717]) is not None:
            aa(717)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[718]) is not None:
            aa(718)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[719]) is not None:
            aa(719)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[720]) is not None:
            aa(720)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[721]) is not None:
            aa(721)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[722]) is not None:
            aa(722)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[723]) is not None:
            aa(723)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[724]) is not None:
            aa(724)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[731]) is not None:
            aa(731)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[732]) is not None:
            aa(732)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[733]) is not None:
            aa(733)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[734]) is not None:
            aa(734)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[735]) is not None:
            aa(735)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[736]) is not None:
            aa(736)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[737]) is not None:
            aa(737)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[738]) is not None:
            aa(738)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[739]) is not None:
            aa(739)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[740]) is not None:
            aa(740)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[741]) is not None:
            aa(741)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[742]) is not None:
            aa(742)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[743]) is not None:
            aa(743)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[744]) is not None:
            aa(744)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[745]) is not None:
            aa(745)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[746]) is not None:
            aa(746)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[747]) is not None:
            aa(747)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[748]) is not None:
            aa(748)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[749]) is not None:
            aa(749)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[750]) is not None:
            aa(750)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[751]) is not None:
            aa(751)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[752]) is not None:
            aa(752)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[753]) is not None:
            aa(753)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[754]) is not None:
            aa(754)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[755]) is not None:
            aa(755)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[756]) is not None:
            aa(756)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[757]) is not None:
            aa(757)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[758]) is not None:
            aa(758)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[759]) is not None:
            aa(759)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[760]) is not None:
            aa(760)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[761]) is not None:
            aa(761)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[762]) is not None:
            aa(762)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[763]) is not None:
            aa(763)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[764]) is not None:
            aa(764)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[765]) is not None:
            aa(765)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[766]) is not None:
            aa(766)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[767]) is not None:
            aa(767)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[768]) is not None:
            aa(768)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[769]) is not None:
            aa(769)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[770]) is not None:
            aa(770)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[771]) is not None:
            aa(771)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[772]) is not None:
            aa(772)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[773]) is not None:
            aa(773)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[774]) is not None:
            aa(774)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[775]) is not None:
            aa(775)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[776]) is not None:
            aa(776)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[777]) is not None:
            aa(777)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[778]) is not None:
            aa(778)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[779]) is not None:
            aa(779)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[780]) is not None:
            aa(780)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[787]) is not None:
            aa(787)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[788]) is not None:
            aa(788)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[789]) is not None:
            aa(789)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[790]) is not None:
            aa(790)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[791]) is not None:
            aa(791)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[792]) is not None:
            aa(792)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[793]) is not None:
            aa(793)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[794]) is not None:
            aa(794)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[795]) is not None:
            aa(795)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[796]) is not None:
            aa(796)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[797]) is not None:
            aa(797)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[798]) is not None:
            aa(798)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[799]) is not None:
            aa(799)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[800]) is not None:
            aa(800)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[801]) is not None:
            aa(801)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[802]) is not None:
            aa(802)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[803]) is not None:
            aa(803)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[804]) is not None:
            aa(804)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[805]) is not None:
            aa(805)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[806]) is not None:
            aa(806)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[807]) is not None:
            aa(807)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[808]) is not None:
            aa(808)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[809]) is not None:
            aa(809)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[810]) is not None:
            aa(810)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[811]) is not None:
            aa(811)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[812]) is not None:
            aa(812)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[813]) is not None:
            aa(813)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[814]) is not None:
            aa(814)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[815]) is not None:
            aa(815)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[816]) is not None:
            aa(816)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[817]) is not None:
            aa(817)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[818]) is not None:
            aa(818)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[819]) is not None:
            aa(819)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[820]) is not None:
            aa(820)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[821]) is not None:
            aa(821)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[822]) is not None:
            aa(822)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[823]) is not None:
            aa(823)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[824]) is not None:
            aa(824)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[825]) is not None:
            aa(825)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[826]) is not None:
            aa(826)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[827]) is not None:
            aa(827)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[828]) is not None:
            aa(828)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[829]) is not None:
            aa(829)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[830]) is not None:
            aa(830)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[831]) is not None:
            aa(831)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[832]) is not None:
            aa(832)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[833]) is not None:
            aa(833)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[834]) is not None:
            aa(834)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[835]) is not None:
            aa(835)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[836]) is not None:
            aa(836)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[843]) is not None:
            aa(843)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[844]) is not None:
            aa(844)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[845]) is not None:
            aa(845)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[846]) is not None:
            aa(846)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[847]) is not None:
            aa(847)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[848]) is not None:
            aa(848)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[849]) is not None:
            aa(849)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[850]) is not None:
            aa(850)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[851]) is not None:
            aa(851)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[852]) is not None:
            aa(852)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[853]) is not None:
            aa(853)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[854]) is not None:
            aa(854)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[855]) is not None:
            aa(855)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[856]) is not None:
            aa(856)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[857]) is not None:
            aa(857)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[858]) is not None:
            aa(858)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[859]) is not None:
            aa(859)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[860]) is not None:
            aa(860)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[861]) is not None:
            aa(861)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[862]) is not None:
            aa(862)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[863]) is not None:
            aa(863)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[864]) is not None:
            aa(864)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[865]) is not None:
            aa(865)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[866]) is not None:
            aa(866)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[867]) is not None:
            aa(867)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[868]) is not None:
            aa(868)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[869]) is not None:
            aa(869)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[870]) is not None:
            aa(870)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[871]) is not None:
            aa(871)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[872]) is not None:
            aa(872)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[873]) is not None:
            aa(873)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[874]) is not None:
            aa(874)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[875]) is not None:
            aa(875)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[876]) is not None:
            aa(876)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[877]) is not None:
            aa(877)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[878]) is not None:
            aa(878)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[879]) is not None:
            aa(879)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[880]) is not None:
            aa(880)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[881]) is not None:
            aa(881)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[882]) is not None:
            aa(882)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[883]) is not None:
            aa(883)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[884]) is not None:
            aa(884)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[885]) is not None:
            aa(885)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[886]) is not None:
            aa(886)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[887]) is not None:
            aa(887)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[888]) is not None:
            aa(888)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[889]) is not None:
            aa(889)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[890]) is not None:
            aa(890)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[891]) is not None:
            aa(891)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[892]) is not None:
            aa(892)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[899]) is not None:
            aa(899)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[900]) is not None:
            aa(900)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[901]) is not None:
            aa(901)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[902]) is not None:
            aa(902)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[903]) is not None:
            aa(903)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[904]) is not None:
            aa(904)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[905]) is not None:
            aa(905)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[906]) is not None:
            aa(906)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[907]) is not None:
            aa(907)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[908]) is not None:
            aa(908)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[909]) is not None:
            aa(909)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[910]) is not None:
            aa(910)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[911]) is not None:
            aa(911)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[912]) is not None:
            aa(912)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[913]) is not None:
            aa(913)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[914]) is not None:
            aa(914)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[915]) is not None:
            aa(915)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[916]) is not None:
            aa(916)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[917]) is not None:
            aa(917)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[918]) is not None:
            aa(918)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[919]) is not None:
            aa(919)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[920]) is not None:
            aa(920)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[921]) is not None:
            aa(921)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[922]) is not None:
            aa(922)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[923]) is not None:
            aa(923)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[924]) is not None:
            aa(924)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[925]) is not None:
            aa(925)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[926]) is not None:
            aa(926)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[927]) is not None:
            aa(927)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[928]) is not None:
            aa(928)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[929]) is not None:
            aa(929)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[930]) is not None:
            aa(930)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[931]) is not None:
            aa(931)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[932]) is not None:
            aa(932)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[933]) is not None:
            aa(933)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[934]) is not None:
            aa(934)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[935]) is not None:
            aa(935)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[936]) is not None:
            aa(936)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[937]) is not None:
            aa(937)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[938]) is not None:
            aa(938)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[939]) is not None:
            aa(939)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[940]) is not None:
            aa(940)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[941]) is not None:
            aa(941)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[942]) is not None:
            aa(942)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[943]) is not None:
            aa(943)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[944]) is not None:
            aa(944)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[945]) is not None:
            aa(945)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[946]) is not None:
            aa(946)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[947]) is not None:
            aa(947)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[948]) is not None:
            aa(948)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[955]) is not None:
            aa(955)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[956]) is not None:
            aa(956)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[957]) is not None:
            aa(957)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[958]) is not None:
            aa(958)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[959]) is not None:
            aa(959)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[960]) is not None:
            aa(960)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[961]) is not None:
            aa(961)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[962]) is not None:
            aa(962)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[963]) is not None:
            aa(963)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[964]) is not None:
            aa(964)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[965]) is not None:
            aa(965)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[966]) is not None:
            aa(966)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[967]) is not None:
            aa(967)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[968]) is not None:
            aa(968)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[969]) is not None:
            aa(969)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[970]) is not None:
            aa(970)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[971]) is not None:
            aa(971)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[972]) is not None:
            aa(972)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[973]) is not None:
            aa(973)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[974]) is not None:
            aa(974)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[975]) is not None:
            aa(975)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[976]) is not None:
            aa(976)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[977]) is not None:
            aa(977)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[978]) is not None:
            aa(978)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[979]) is not None:
            aa(979)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[980]) is not None:
            aa(980)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[981]) is not None:
            aa(981)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[982]) is not None:
            aa(982)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[983]) is not None:
            aa(983)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[984]) is not None:
            aa(984)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[985]) is not None:
            aa(985)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[986]) is not None:
            aa(986)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[987]) is not None:
            aa(987)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[988]) is not None:
            aa(988)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[989]) is not None:
            aa(989)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[990]) is not None:
            aa(990)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[991]) is not None:
            aa(991)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[992]) is not None:
            aa(992)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[993]) is not None:
            aa(993)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[994]) is not None:
            aa(994)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[995]) is not None:
            aa(995)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[996]) is not None:
            aa(996)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[997]) is not None:
            aa(997)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[998]) is not None:
            aa(998)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[999]) is not None:
            aa(999)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1000]) is not None:
            aa(1000)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1001]) is not None:
            aa(1001)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1002]) is not None:
            aa(1002)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1003]) is not None:
            aa(1003)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1004]) is not None:
            aa(1004)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1011]) is not None:
            aa(1011)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1012]) is not None:
            aa(1012)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1013]) is not None:
            aa(1013)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1014]) is not None:
            aa(1014)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1015]) is not None:
            aa(1015)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1016]) is not None:
            aa(1016)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1017]) is not None:
            aa(1017)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1018]) is not None:
            aa(1018)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1019]) is not None:
            aa(1019)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1020]) is not None:
            aa(1020)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1021]) is not None:
            aa(1021)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1022]) is not None:
            aa(1022)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1023]) is not None:
            aa(1023)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1024]) is not None:
            aa(1024)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1025]) is not None:
            aa(1025)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1026]) is not None:
            aa(1026)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1027]) is not None:
            aa(1027)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1028]) is not None:
            aa(1028)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1029]) is not None:
            aa(1029)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1030]) is not None:
            aa(1030)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1031]) is not None:
            aa(1031)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1032]) is not None:
            aa(1032)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1033]) is not None:
            aa(1033)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1034]) is not None:
            aa(1034)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1035]) is not None:
            aa(1035)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1036]) is not None:
            aa(1036)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1037]) is not None:
            aa(1037)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1038]) is not None:
            aa(1038)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1039]) is not None:
            aa(1039)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1040]) is not None:
            aa(1040)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1041]) is not None:
            aa(1041)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1042]) is not None:
            aa(1042)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1043]) is not None:
            aa(1043)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1044]) is not None:
            aa(1044)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1045]) is not None:
            aa(1045)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1046]) is not None:
            aa(1046)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1047]) is not None:
            aa(1047)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1048]) is not None:
            aa(1048)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1049]) is not None:
            aa(1049)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1050]) is not None:
            aa(1050)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1051]) is not None:
            aa(1051)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1052]) is not None:
            aa(1052)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1053]) is not None:
            aa(1053)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1054]) is not None:
            aa(1054)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1055]) is not None:
            aa(1055)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1056]) is not None:
            aa(1056)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1057]) is not None:
            aa(1057)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1058]) is not None:
            aa(1058)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1059]) is not None:
            aa(1059)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1060]) is not None:
            aa(1060)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1067]) is not None:
            aa(1067)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1068]) is not None:
            aa(1068)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1069]) is not None:
            aa(1069)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1070]) is not None:
            aa(1070)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1071]) is not None:
            aa(1071)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1072]) is not None:
            aa(1072)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1073]) is not None:
            aa(1073)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1074]) is not None:
            aa(1074)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1075]) is not None:
            aa(1075)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1076]) is not None:
            aa(1076)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1077]) is not None:
            aa(1077)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1078]) is not None:
            aa(1078)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1079]) is not None:
            aa(1079)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1080]) is not None:
            aa(1080)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1081]) is not None:
            aa(1081)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1082]) is not None:
            aa(1082)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1083]) is not None:
            aa(1083)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1084]) is not None:
            aa(1084)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1085]) is not None:
            aa(1085)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1086]) is not None:
            aa(1086)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1087]) is not None:
            aa(1087)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1088]) is not None:
            aa(1088)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1089]) is not None:
            aa(1089)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1090]) is not None:
            aa(1090)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1091]) is not None:
            aa(1091)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1092]) is not None:
            aa(1092)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1093]) is not None:
            aa(1093)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1094]) is not None:
            aa(1094)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1095]) is not None:
            aa(1095)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1096]) is not None:
            aa(1096)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1097]) is not None:
            aa(1097)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1098]) is not None:
            aa(1098)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1099]) is not None:
            aa(1099)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1100]) is not None:
            aa(1100)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1101]) is not None:
            aa(1101)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1102]) is not None:
            aa(1102)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1103]) is not None:
            aa(1103)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1104]) is not None:
            aa(1104)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1105]) is not None:
            aa(1105)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1106]) is not None:
            aa(1106)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1107]) is not None:
            aa(1107)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1108]) is not None:
            aa(1108)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1109]) is not None:
            aa(1109)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1110]) is not None:
            aa(1110)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1111]) is not None:
            aa(1111)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1112]) is not None:
            aa(1112)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1113]) is not None:
            aa(1113)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1114]) is not None:
            aa(1114)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1115]) is not None:
            aa(1115)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1116]) is not None:
            aa(1116)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1123]) is not None:
            aa(1123)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1124]) is not None:
            aa(1124)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1125]) is not None:
            aa(1125)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1126]) is not None:
            aa(1126)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1127]) is not None:
            aa(1127)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1128]) is not None:
            aa(1128)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1129]) is not None:
            aa(1129)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1130]) is not None:
            aa(1130)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1131]) is not None:
            aa(1131)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1132]) is not None:
            aa(1132)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1133]) is not None:
            aa(1133)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1134]) is not None:
            aa(1134)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1135]) is not None:
            aa(1135)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1136]) is not None:
            aa(1136)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1137]) is not None:
            aa(1137)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1138]) is not None:
            aa(1138)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1139]) is not None:
            aa(1139)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1140]) is not None:
            aa(1140)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1141]) is not None:
            aa(1141)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1142]) is not None:
            aa(1142)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1143]) is not None:
            aa(1143)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1144]) is not None:
            aa(1144)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1145]) is not None:
            aa(1145)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1146]) is not None:
            aa(1146)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1147]) is not None:
            aa(1147)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1148]) is not None:
            aa(1148)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1149]) is not None:
            aa(1149)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1150]) is not None:
            aa(1150)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1151]) is not None:
            aa(1151)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1152]) is not None:
            aa(1152)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1153]) is not None:
            aa(1153)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1154]) is not None:
            aa(1154)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1155]) is not None:
            aa(1155)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1156]) is not None:
            aa(1156)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1157]) is not None:
            aa(1157)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1158]) is not None:
            aa(1158)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1159]) is not None:
            aa(1159)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1160]) is not None:
            aa(1160)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1161]) is not None:
            aa(1161)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1162]) is not None:
            aa(1162)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1163]) is not None:
            aa(1163)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1164]) is not None:
            aa(1164)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1165]) is not None:
            aa(1165)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1166]) is not None:
            aa(1166)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1167]) is not None:
            aa(1167)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1168]) is not None:
            aa(1168)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1169]) is not None:
            aa(1169)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1170]) is not None:
            aa(1170)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1171]) is not None:
            aa(1171)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1172]) is not None:
            aa(1172)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1179]) is not None:
            aa(1179)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1180]) is not None:
            aa(1180)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1181]) is not None:
            aa(1181)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1182]) is not None:
            aa(1182)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1183]) is not None:
            aa(1183)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1184]) is not None:
            aa(1184)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1185]) is not None:
            aa(1185)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1186]) is not None:
            aa(1186)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1187]) is not None:
            aa(1187)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1188]) is not None:
            aa(1188)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1189]) is not None:
            aa(1189)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1190]) is not None:
            aa(1190)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1191]) is not None:
            aa(1191)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1192]) is not None:
            aa(1192)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1193]) is not None:
            aa(1193)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1194]) is not None:
            aa(1194)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1195]) is not None:
            aa(1195)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1196]) is not None:
            aa(1196)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1197]) is not None:
            aa(1197)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1198]) is not None:
            aa(1198)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1199]) is not None:
            aa(1199)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1200]) is not None:
            aa(1200)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1201]) is not None:
            aa(1201)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1202]) is not None:
            aa(1202)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1203]) is not None:
            aa(1203)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1204]) is not None:
            aa(1204)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1205]) is not None:
            aa(1205)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1206]) is not None:
            aa(1206)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1207]) is not None:
            aa(1207)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1208]) is not None:
            aa(1208)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1209]) is not None:
            aa(1209)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1210]) is not None:
            aa(1210)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1211]) is not None:
            aa(1211)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1212]) is not None:
            aa(1212)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1213]) is not None:
            aa(1213)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1214]) is not None:
            aa(1214)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1215]) is not None:
            aa(1215)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1216]) is not None:
            aa(1216)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1217]) is not None:
            aa(1217)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1218]) is not None:
            aa(1218)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1219]) is not None:
            aa(1219)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1220]) is not None:
            aa(1220)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1221]) is not None:
            aa(1221)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1222]) is not None:
            aa(1222)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1223]) is not None:
            aa(1223)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1224]) is not None:
            aa(1224)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1225]) is not None:
            aa(1225)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1226]) is not None:
            aa(1226)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1227]) is not None:
            aa(1227)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1228]) is not None:
            aa(1228)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1235]) is not None:
            aa(1235)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1236]) is not None:
            aa(1236)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1237]) is not None:
            aa(1237)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1238]) is not None:
            aa(1238)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1239]) is not None:
            aa(1239)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1240]) is not None:
            aa(1240)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1241]) is not None:
            aa(1241)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1242]) is not None:
            aa(1242)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1243]) is not None:
            aa(1243)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1244]) is not None:
            aa(1244)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1245]) is not None:
            aa(1245)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1246]) is not None:
            aa(1246)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1247]) is not None:
            aa(1247)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1248]) is not None:
            aa(1248)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1249]) is not None:
            aa(1249)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1250]) is not None:
            aa(1250)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1251]) is not None:
            aa(1251)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1252]) is not None:
            aa(1252)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1253]) is not None:
            aa(1253)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1254]) is not None:
            aa(1254)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1255]) is not None:
            aa(1255)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1256]) is not None:
            aa(1256)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1257]) is not None:
            aa(1257)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1258]) is not None:
            aa(1258)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1259]) is not None:
            aa(1259)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1260]) is not None:
            aa(1260)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1261]) is not None:
            aa(1261)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1262]) is not None:
            aa(1262)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1263]) is not None:
            aa(1263)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1264]) is not None:
            aa(1264)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1265]) is not None:
            aa(1265)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1266]) is not None:
            aa(1266)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1267]) is not None:
            aa(1267)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1268]) is not None:
            aa(1268)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1269]) is not None:
            aa(1269)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1270]) is not None:
            aa(1270)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1271]) is not None:
            aa(1271)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1272]) is not None:
            aa(1272)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1273]) is not None:
            aa(1273)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1274]) is not None:
            aa(1274)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1275]) is not None:
            aa(1275)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1276]) is not None:
            aa(1276)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1277]) is not None:
            aa(1277)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1278]) is not None:
            aa(1278)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1279]) is not None:
            aa(1279)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1280]) is not None:
            aa(1280)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1281]) is not None:
            aa(1281)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1282]) is not None:
            aa(1282)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1283]) is not None:
            aa(1283)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1284]) is not None:
            aa(1284)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1291]) is not None:
            aa(1291)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1292]) is not None:
            aa(1292)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1293]) is not None:
            aa(1293)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1294]) is not None:
            aa(1294)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1295]) is not None:
            aa(1295)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1296]) is not None:
            aa(1296)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1297]) is not None:
            aa(1297)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1298]) is not None:
            aa(1298)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1299]) is not None:
            aa(1299)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1300]) is not None:
            aa(1300)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1301]) is not None:
            aa(1301)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1302]) is not None:
            aa(1302)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1303]) is not None:
            aa(1303)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1304]) is not None:
            aa(1304)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1305]) is not None:
            aa(1305)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1306]) is not None:
            aa(1306)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1307]) is not None:
            aa(1307)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1308]) is not None:
            aa(1308)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1309]) is not None:
            aa(1309)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1310]) is not None:
            aa(1310)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1311]) is not None:
            aa(1311)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1312]) is not None:
            aa(1312)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1313]) is not None:
            aa(1313)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1314]) is not None:
            aa(1314)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1315]) is not None:
            aa(1315)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1316]) is not None:
            aa(1316)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1317]) is not None:
            aa(1317)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1318]) is not None:
            aa(1318)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1319]) is not None:
            aa(1319)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1320]) is not None:
            aa(1320)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1321]) is not None:
            aa(1321)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1322]) is not None:
            aa(1322)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1323]) is not None:
            aa(1323)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1324]) is not None:
            aa(1324)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1325]) is not None:
            aa(1325)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1326]) is not None:
            aa(1326)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1327]) is not None:
            aa(1327)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1328]) is not None:
            aa(1328)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1329]) is not None:
            aa(1329)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1330]) is not None:
            aa(1330)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1331]) is not None:
            aa(1331)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1332]) is not None:
            aa(1332)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1333]) is not None:
            aa(1333)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1334]) is not None:
            aa(1334)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1335]) is not None:
            aa(1335)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1336]) is not None:
            aa(1336)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1337]) is not None:
            aa(1337)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1338]) is not None:
            aa(1338)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1339]) is not None:
            aa(1339)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1340]) is not None:
            aa(1340)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1347]) is not None:
            aa(1347)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1348]) is not None:
            aa(1348)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1349]) is not None:
            aa(1349)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1350]) is not None:
            aa(1350)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1351]) is not None:
            aa(1351)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1352]) is not None:
            aa(1352)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1353]) is not None:
            aa(1353)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1354]) is not None:
            aa(1354)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1355]) is not None:
            aa(1355)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1356]) is not None:
            aa(1356)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1357]) is not None:
            aa(1357)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1358]) is not None:
            aa(1358)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1359]) is not None:
            aa(1359)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1360]) is not None:
            aa(1360)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1361]) is not None:
            aa(1361)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1362]) is not None:
            aa(1362)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1363]) is not None:
            aa(1363)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1364]) is not None:
            aa(1364)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1365]) is not None:
            aa(1365)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1366]) is not None:
            aa(1366)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1367]) is not None:
            aa(1367)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1368]) is not None:
            aa(1368)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1369]) is not None:
            aa(1369)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1370]) is not None:
            aa(1370)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1371]) is not None:
            aa(1371)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1372]) is not None:
            aa(1372)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1373]) is not None:
            aa(1373)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1374]) is not None:
            aa(1374)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1375]) is not None:
            aa(1375)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1376]) is not None:
            aa(1376)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1377]) is not None:
            aa(1377)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1378]) is not None:
            aa(1378)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1379]) is not None:
            aa(1379)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1380]) is not None:
            aa(1380)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1381]) is not None:
            aa(1381)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1382]) is not None:
            aa(1382)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1383]) is not None:
            aa(1383)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1384]) is not None:
            aa(1384)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1385]) is not None:
            aa(1385)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1386]) is not None:
            aa(1386)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1387]) is not None:
            aa(1387)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1388]) is not None:
            aa(1388)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1389]) is not None:
            aa(1389)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1390]) is not None:
            aa(1390)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1391]) is not None:
            aa(1391)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1392]) is not None:
            aa(1392)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1393]) is not None:
            aa(1393)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1394]) is not None:
            aa(1394)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1395]) is not None:
            aa(1395)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1396]) is not None:
            aa(1396)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1403]) is not None:
            aa(1403)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1404]) is not None:
            aa(1404)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1405]) is not None:
            aa(1405)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1406]) is not None:
            aa(1406)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1407]) is not None:
            aa(1407)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1408]) is not None:
            aa(1408)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1409]) is not None:
            aa(1409)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1410]) is not None:
            aa(1410)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1411]) is not None:
            aa(1411)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1412]) is not None:
            aa(1412)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1413]) is not None:
            aa(1413)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1414]) is not None:
            aa(1414)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1415]) is not None:
            aa(1415)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1416]) is not None:
            aa(1416)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1417]) is not None:
            aa(1417)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1418]) is not None:
            aa(1418)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1419]) is not None:
            aa(1419)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1420]) is not None:
            aa(1420)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1421]) is not None:
            aa(1421)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1422]) is not None:
            aa(1422)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1423]) is not None:
            aa(1423)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1424]) is not None:
            aa(1424)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1425]) is not None:
            aa(1425)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1426]) is not None:
            aa(1426)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1427]) is not None:
            aa(1427)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1428]) is not None:
            aa(1428)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1429]) is not None:
            aa(1429)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1430]) is not None:
            aa(1430)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1431]) is not None:
            aa(1431)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1432]) is not None:
            aa(1432)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1433]) is not None:
            aa(1433)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1434]) is not None:
            aa(1434)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1435]) is not None:
            aa(1435)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1436]) is not None:
            aa(1436)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1437]) is not None:
            aa(1437)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1438]) is not None:
            aa(1438)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1439]) is not None:
            aa(1439)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1440]) is not None:
            aa(1440)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1441]) is not None:
            aa(1441)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1442]) is not None:
            aa(1442)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1443]) is not None:
            aa(1443)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1444]) is not None:
            aa(1444)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1445]) is not None:
            aa(1445)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1446]) is not None:
            aa(1446)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1447]) is not None:
            aa(1447)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1448]) is not None:
            aa(1448)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1449]) is not None:
            aa(1449)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1450]) is not None:
            aa(1450)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1451]) is not None:
            aa(1451)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1452]) is not None:
            aa(1452)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1459]) is not None:
            aa(1459)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1460]) is not None:
            aa(1460)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1461]) is not None:
            aa(1461)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1462]) is not None:
            aa(1462)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1463]) is not None:
            aa(1463)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1464]) is not None:
            aa(1464)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1465]) is not None:
            aa(1465)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1466]) is not None:
            aa(1466)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1467]) is not None:
            aa(1467)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1468]) is not None:
            aa(1468)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1469]) is not None:
            aa(1469)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1470]) is not None:
            aa(1470)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1471]) is not None:
            aa(1471)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1472]) is not None:
            aa(1472)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1473]) is not None:
            aa(1473)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1474]) is not None:
            aa(1474)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1475]) is not None:
            aa(1475)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1476]) is not None:
            aa(1476)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1477]) is not None:
            aa(1477)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1478]) is not None:
            aa(1478)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1479]) is not None:
            aa(1479)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1480]) is not None:
            aa(1480)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1481]) is not None:
            aa(1481)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1482]) is not None:
            aa(1482)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1483]) is not None:
            aa(1483)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1484]) is not None:
            aa(1484)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1485]) is not None:
            aa(1485)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1486]) is not None:
            aa(1486)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1487]) is not None:
            aa(1487)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1488]) is not None:
            aa(1488)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1489]) is not None:
            aa(1489)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1490]) is not None:
            aa(1490)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1491]) is not None:
            aa(1491)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1492]) is not None:
            aa(1492)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1493]) is not None:
            aa(1493)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1494]) is not None:
            aa(1494)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1495]) is not None:
            aa(1495)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1496]) is not None:
            aa(1496)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1497]) is not None:
            aa(1497)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1498]) is not None:
            aa(1498)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1499]) is not None:
            aa(1499)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1500]) is not None:
            aa(1500)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1501]) is not None:
            aa(1501)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1502]) is not None:
            aa(1502)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1503]) is not None:
            aa(1503)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1504]) is not None:
            aa(1504)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1505]) is not None:
            aa(1505)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1506]) is not None:
            aa(1506)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1507]) is not None:
            aa(1507)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1508]) is not None:
            aa(1508)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1515]) is not None:
            aa(1515)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1516]) is not None:
            aa(1516)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1517]) is not None:
            aa(1517)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1518]) is not None:
            aa(1518)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1519]) is not None:
            aa(1519)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1520]) is not None:
            aa(1520)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1521]) is not None:
            aa(1521)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1522]) is not None:
            aa(1522)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1523]) is not None:
            aa(1523)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1524]) is not None:
            aa(1524)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1525]) is not None:
            aa(1525)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1526]) is not None:
            aa(1526)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1527]) is not None:
            aa(1527)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1528]) is not None:
            aa(1528)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1529]) is not None:
            aa(1529)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1530]) is not None:
            aa(1530)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1531]) is not None:
            aa(1531)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1532]) is not None:
            aa(1532)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1533]) is not None:
            aa(1533)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1534]) is not None:
            aa(1534)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1535]) is not None:
            aa(1535)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1536]) is not None:
            aa(1536)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1537]) is not None:
            aa(1537)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1538]) is not None:
            aa(1538)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1539]) is not None:
            aa(1539)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1540]) is not None:
            aa(1540)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1541]) is not None:
            aa(1541)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1542]) is not None:
            aa(1542)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1543]) is not None:
            aa(1543)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1544]) is not None:
            aa(1544)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1545]) is not None:
            aa(1545)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1546]) is not None:
            aa(1546)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1547]) is not None:
            aa(1547)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1548]) is not None:
            aa(1548)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1549]) is not None:
            aa(1549)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1550]) is not None:
            aa(1550)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1551]) is not None:
            aa(1551)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1552]) is not None:
            aa(1552)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1553]) is not None:
            aa(1553)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1554]) is not None:
            aa(1554)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1555]) is not None:
            aa(1555)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1556]) is not None:
            aa(1556)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1557]) is not None:
            aa(1557)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1558]) is not None:
            aa(1558)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1559]) is not None:
            aa(1559)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1560]) is not None:
            aa(1560)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1561]) is not None:
            aa(1561)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1562]) is not None:
            aa(1562)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1563]) is not None:
            aa(1563)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1564]) is not None:
            aa(1564)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1571]) is not None:
            aa(1571)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1572]) is not None:
            aa(1572)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1573]) is not None:
            aa(1573)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1574]) is not None:
            aa(1574)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1575]) is not None:
            aa(1575)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1576]) is not None:
            aa(1576)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1577]) is not None:
            aa(1577)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1578]) is not None:
            aa(1578)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1579]) is not None:
            aa(1579)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1580]) is not None:
            aa(1580)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1581]) is not None:
            aa(1581)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1582]) is not None:
            aa(1582)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1583]) is not None:
            aa(1583)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1584]) is not None:
            aa(1584)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1585]) is not None:
            aa(1585)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1586]) is not None:
            aa(1586)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1587]) is not None:
            aa(1587)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1588]) is not None:
            aa(1588)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1589]) is not None:
            aa(1589)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1590]) is not None:
            aa(1590)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1591]) is not None:
            aa(1591)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1592]) is not None:
            aa(1592)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1593]) is not None:
            aa(1593)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1594]) is not None:
            aa(1594)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1595]) is not None:
            aa(1595)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1596]) is not None:
            aa(1596)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1597]) is not None:
            aa(1597)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1598]) is not None:
            aa(1598)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1599]) is not None:
            aa(1599)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1600]) is not None:
            aa(1600)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1601]) is not None:
            aa(1601)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1602]) is not None:
            aa(1602)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1603]) is not None:
            aa(1603)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1604]) is not None:
            aa(1604)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1605]) is not None:
            aa(1605)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1606]) is not None:
            aa(1606)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1607]) is not None:
            aa(1607)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1608]) is not None:
            aa(1608)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1609]) is not None:
            aa(1609)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1610]) is not None:
            aa(1610)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1611]) is not None:
            aa(1611)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1612]) is not None:
            aa(1612)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1613]) is not None:
            aa(1613)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1614]) is not None:
            aa(1614)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1615]) is not None:
            aa(1615)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1616]) is not None:
            aa(1616)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1617]) is not None:
            aa(1617)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1618]) is not None:
            aa(1618)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1619]) is not None:
            aa(1619)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1620]) is not None:
            aa(1620)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1627]) is not None:
            aa(1627)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1628]) is not None:
            aa(1628)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1629]) is not None:
            aa(1629)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1630]) is not None:
            aa(1630)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1631]) is not None:
            aa(1631)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1632]) is not None:
            aa(1632)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1633]) is not None:
            aa(1633)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1634]) is not None:
            aa(1634)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1635]) is not None:
            aa(1635)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1636]) is not None:
            aa(1636)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1637]) is not None:
            aa(1637)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1638]) is not None:
            aa(1638)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1639]) is not None:
            aa(1639)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1640]) is not None:
            aa(1640)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1641]) is not None:
            aa(1641)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1642]) is not None:
            aa(1642)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1643]) is not None:
            aa(1643)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1644]) is not None:
            aa(1644)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1645]) is not None:
            aa(1645)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1646]) is not None:
            aa(1646)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1647]) is not None:
            aa(1647)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1648]) is not None:
            aa(1648)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1649]) is not None:
            aa(1649)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1650]) is not None:
            aa(1650)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1651]) is not None:
            aa(1651)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1652]) is not None:
            aa(1652)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1653]) is not None:
            aa(1653)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1654]) is not None:
            aa(1654)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1655]) is not None:
            aa(1655)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1656]) is not None:
            aa(1656)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1657]) is not None:
            aa(1657)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1658]) is not None:
            aa(1658)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1659]) is not None:
            aa(1659)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1660]) is not None:
            aa(1660)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1661]) is not None:
            aa(1661)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1662]) is not None:
            aa(1662)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1663]) is not None:
            aa(1663)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1664]) is not None:
            aa(1664)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1665]) is not None:
            aa(1665)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1666]) is not None:
            aa(1666)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1667]) is not None:
            aa(1667)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1668]) is not None:
            aa(1668)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1669]) is not None:
            aa(1669)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1670]) is not None:
            aa(1670)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1671]) is not None:
            aa(1671)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1672]) is not None:
            aa(1672)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1673]) is not None:
            aa(1673)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1674]) is not None:
            aa(1674)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1675]) is not None:
            aa(1675)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1676]) is not None:
            aa(1676)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1683]) is not None:
            aa(1683)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1684]) is not None:
            aa(1684)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1685]) is not None:
            aa(1685)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1686]) is not None:
            aa(1686)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1687]) is not None:
            aa(1687)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1688]) is not None:
            aa(1688)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1689]) is not None:
            aa(1689)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1690]) is not None:
            aa(1690)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1691]) is not None:
            aa(1691)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1692]) is not None:
            aa(1692)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1693]) is not None:
            aa(1693)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1694]) is not None:
            aa(1694)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1695]) is not None:
            aa(1695)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1696]) is not None:
            aa(1696)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1697]) is not None:
            aa(1697)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1698]) is not None:
            aa(1698)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1699]) is not None:
            aa(1699)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1700]) is not None:
            aa(1700)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1701]) is not None:
            aa(1701)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1702]) is not None:
            aa(1702)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1703]) is not None:
            aa(1703)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1704]) is not None:
            aa(1704)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1705]) is not None:
            aa(1705)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1706]) is not None:
            aa(1706)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1707]) is not None:
            aa(1707)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1708]) is not None:
            aa(1708)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1709]) is not None:
            aa(1709)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1710]) is not None:
            aa(1710)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1711]) is not None:
            aa(1711)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1712]) is not None:
            aa(1712)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1713]) is not None:
            aa(1713)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1714]) is not None:
            aa(1714)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1715]) is not None:
            aa(1715)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1716]) is not None:
            aa(1716)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1717]) is not None:
            aa(1717)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1718]) is not None:
            aa(1718)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1719]) is not None:
            aa(1719)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1720]) is not None:
            aa(1720)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1721]) is not None:
            aa(1721)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1722]) is not None:
            aa(1722)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1723]) is not None:
            aa(1723)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1724]) is not None:
            aa(1724)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1725]) is not None:
            aa(1725)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1726]) is not None:
            aa(1726)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1727]) is not None:
            aa(1727)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1728]) is not None:
            aa(1728)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1729]) is not None:
            aa(1729)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1730]) is not None:
            aa(1730)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1731]) is not None:
            aa(1731)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1732]) is not None:
            aa(1732)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1739]) is not None:
            aa(1739)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1740]) is not None:
            aa(1740)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1741]) is not None:
            aa(1741)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1742]) is not None:
            aa(1742)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1743]) is not None:
            aa(1743)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1744]) is not None:
            aa(1744)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1745]) is not None:
            aa(1745)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1746]) is not None:
            aa(1746)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1747]) is not None:
            aa(1747)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1748]) is not None:
            aa(1748)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1749]) is not None:
            aa(1749)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1750]) is not None:
            aa(1750)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1751]) is not None:
            aa(1751)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1752]) is not None:
            aa(1752)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1753]) is not None:
            aa(1753)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1754]) is not None:
            aa(1754)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1755]) is not None:
            aa(1755)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1756]) is not None:
            aa(1756)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1757]) is not None:
            aa(1757)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1758]) is not None:
            aa(1758)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1759]) is not None:
            aa(1759)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1760]) is not None:
            aa(1760)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1761]) is not None:
            aa(1761)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1762]) is not None:
            aa(1762)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1763]) is not None:
            aa(1763)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1764]) is not None:
            aa(1764)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1765]) is not None:
            aa(1765)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1766]) is not None:
            aa(1766)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1767]) is not None:
            aa(1767)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1768]) is not None:
            aa(1768)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1769]) is not None:
            aa(1769)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1770]) is not None:
            aa(1770)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1771]) is not None:
            aa(1771)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1772]) is not None:
            aa(1772)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1773]) is not None:
            aa(1773)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1774]) is not None:
            aa(1774)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1775]) is not None:
            aa(1775)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1776]) is not None:
            aa(1776)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1777]) is not None:
            aa(1777)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1778]) is not None:
            aa(1778)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1779]) is not None:
            aa(1779)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1780]) is not None:
            aa(1780)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1781]) is not None:
            aa(1781)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1782]) is not None:
            aa(1782)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1783]) is not None:
            aa(1783)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1784]) is not None:
            aa(1784)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1785]) is not None:
            aa(1785)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1786]) is not None:
            aa(1786)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1787]) is not None:
            aa(1787)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1788]) is not None:
            aa(1788)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1795]) is not None:
            aa(1795)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1796]) is not None:
            aa(1796)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1797]) is not None:
            aa(1797)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1798]) is not None:
            aa(1798)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1799]) is not None:
            aa(1799)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1800]) is not None:
            aa(1800)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1801]) is not None:
            aa(1801)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1802]) is not None:
            aa(1802)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1803]) is not None:
            aa(1803)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1804]) is not None:
            aa(1804)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1805]) is not None:
            aa(1805)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1806]) is not None:
            aa(1806)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1807]) is not None:
            aa(1807)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1808]) is not None:
            aa(1808)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1809]) is not None:
            aa(1809)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1810]) is not None:
            aa(1810)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1811]) is not None:
            aa(1811)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1812]) is not None:
            aa(1812)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1813]) is not None:
            aa(1813)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1814]) is not None:
            aa(1814)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1815]) is not None:
            aa(1815)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1816]) is not None:
            aa(1816)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1817]) is not None:
            aa(1817)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1818]) is not None:
            aa(1818)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1819]) is not None:
            aa(1819)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1820]) is not None:
            aa(1820)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1821]) is not None:
            aa(1821)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1822]) is not None:
            aa(1822)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1823]) is not None:
            aa(1823)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1824]) is not None:
            aa(1824)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1825]) is not None:
            aa(1825)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1826]) is not None:
            aa(1826)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1827]) is not None:
            aa(1827)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1828]) is not None:
            aa(1828)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1829]) is not None:
            aa(1829)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1830]) is not None:
            aa(1830)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1831]) is not None:
            aa(1831)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1832]) is not None:
            aa(1832)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1833]) is not None:
            aa(1833)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1834]) is not None:
            aa(1834)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1835]) is not None:
            aa(1835)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1836]) is not None:
            aa(1836)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1837]) is not None:
            aa(1837)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1838]) is not None:
            aa(1838)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1839]) is not None:
            aa(1839)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1840]) is not None:
            aa(1840)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1841]) is not None:
            aa(1841)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1842]) is not None:
            aa(1842)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1843]) is not None:
            aa(1843)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1844]) is not None:
            aa(1844)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1851]) is not None:
            aa(1851)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1852]) is not None:
            aa(1852)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1853]) is not None:
            aa(1853)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1854]) is not None:
            aa(1854)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1855]) is not None:
            aa(1855)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1856]) is not None:
            aa(1856)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1857]) is not None:
            aa(1857)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1858]) is not None:
            aa(1858)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1859]) is not None:
            aa(1859)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1860]) is not None:
            aa(1860)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1861]) is not None:
            aa(1861)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1862]) is not None:
            aa(1862)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1863]) is not None:
            aa(1863)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1864]) is not None:
            aa(1864)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1865]) is not None:
            aa(1865)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1866]) is not None:
            aa(1866)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1867]) is not None:
            aa(1867)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1868]) is not None:
            aa(1868)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1869]) is not None:
            aa(1869)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1870]) is not None:
            aa(1870)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1871]) is not None:
            aa(1871)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1872]) is not None:
            aa(1872)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1873]) is not None:
            aa(1873)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1874]) is not None:
            aa(1874)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1875]) is not None:
            aa(1875)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1876]) is not None:
            aa(1876)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1877]) is not None:
            aa(1877)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1878]) is not None:
            aa(1878)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1879]) is not None:
            aa(1879)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1880]) is not None:
            aa(1880)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1881]) is not None:
            aa(1881)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1882]) is not None:
            aa(1882)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1883]) is not None:
            aa(1883)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1884]) is not None:
            aa(1884)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1885]) is not None:
            aa(1885)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1886]) is not None:
            aa(1886)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1887]) is not None:
            aa(1887)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1888]) is not None:
            aa(1888)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1889]) is not None:
            aa(1889)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1890]) is not None:
            aa(1890)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1891]) is not None:
            aa(1891)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1892]) is not None:
            aa(1892)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1893]) is not None:
            aa(1893)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1894]) is not None:
            aa(1894)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1895]) is not None:
            aa(1895)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1896]) is not None:
            aa(1896)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1897]) is not None:
            aa(1897)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1898]) is not None:
            aa(1898)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1899]) is not None:
            aa(1899)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1900]) is not None:
            aa(1900)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1907]) is not None:
            aa(1907)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1908]) is not None:
            aa(1908)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1909]) is not None:
            aa(1909)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1910]) is not None:
            aa(1910)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1911]) is not None:
            aa(1911)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1912]) is not None:
            aa(1912)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1913]) is not None:
            aa(1913)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1914]) is not None:
            aa(1914)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1915]) is not None:
            aa(1915)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1916]) is not None:
            aa(1916)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1917]) is not None:
            aa(1917)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1918]) is not None:
            aa(1918)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1919]) is not None:
            aa(1919)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1920]) is not None:
            aa(1920)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1921]) is not None:
            aa(1921)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1922]) is not None:
            aa(1922)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1923]) is not None:
            aa(1923)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1924]) is not None:
            aa(1924)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1925]) is not None:
            aa(1925)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1926]) is not None:
            aa(1926)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1927]) is not None:
            aa(1927)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1928]) is not None:
            aa(1928)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1929]) is not None:
            aa(1929)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1930]) is not None:
            aa(1930)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1931]) is not None:
            aa(1931)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1932]) is not None:
            aa(1932)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1933]) is not None:
            aa(1933)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1934]) is not None:
            aa(1934)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1935]) is not None:
            aa(1935)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1936]) is not None:
            aa(1936)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1937]) is not None:
            aa(1937)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1938]) is not None:
            aa(1938)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1939]) is not None:
            aa(1939)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1940]) is not None:
            aa(1940)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1941]) is not None:
            aa(1941)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1942]) is not None:
            aa(1942)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1943]) is not None:
            aa(1943)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1944]) is not None:
            aa(1944)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1945]) is not None:
            aa(1945)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1946]) is not None:
            aa(1946)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1947]) is not None:
            aa(1947)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1948]) is not None:
            aa(1948)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1949]) is not None:
            aa(1949)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1950]) is not None:
            aa(1950)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1951]) is not None:
            aa(1951)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1952]) is not None:
            aa(1952)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1953]) is not None:
            aa(1953)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1954]) is not None:
            aa(1954)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1955]) is not None:
            aa(1955)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1956]) is not None:
            aa(1956)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1963]) is not None:
            aa(1963)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1964]) is not None:
            aa(1964)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1965]) is not None:
            aa(1965)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1966]) is not None:
            aa(1966)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1967]) is not None:
            aa(1967)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1968]) is not None:
            aa(1968)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1969]) is not None:
            aa(1969)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1970]) is not None:
            aa(1970)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1971]) is not None:
            aa(1971)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1972]) is not None:
            aa(1972)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1973]) is not None:
            aa(1973)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1974]) is not None:
            aa(1974)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1975]) is not None:
            aa(1975)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1976]) is not None:
            aa(1976)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1977]) is not None:
            aa(1977)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1978]) is not None:
            aa(1978)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1979]) is not None:
            aa(1979)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1980]) is not None:
            aa(1980)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1981]) is not None:
            aa(1981)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1982]) is not None:
            aa(1982)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1983]) is not None:
            aa(1983)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1984]) is not None:
            aa(1984)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1985]) is not None:
            aa(1985)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1986]) is not None:
            aa(1986)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1987]) is not None:
            aa(1987)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1988]) is not None:
            aa(1988)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1989]) is not None:
            aa(1989)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1990]) is not None:
            aa(1990)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1991]) is not None:
            aa(1991)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1992]) is not None:
            aa(1992)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1993]) is not None:
            aa(1993)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1994]) is not None:
            aa(1994)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1995]) is not None:
            aa(1995)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1996]) is not None:
            aa(1996)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1997]) is not None:
            aa(1997)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1998]) is not None:
            aa(1998)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[1999]) is not None:
            aa(1999)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2000]) is not None:
            aa(2000)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2001]) is not None:
            aa(2001)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2002]) is not None:
            aa(2002)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2003]) is not None:
            aa(2003)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2004]) is not None:
            aa(2004)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2005]) is not None:
            aa(2005)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2006]) is not None:
            aa(2006)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2007]) is not None:
            aa(2007)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2008]) is not None:
            aa(2008)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2009]) is not None:
            aa(2009)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2010]) is not None:
            aa(2010)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2011]) is not None:
            aa(2011)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2012]) is not None:
            aa(2012)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2019]) is not None:
            aa(2019)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2020]) is not None:
            aa(2020)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2021]) is not None:
            aa(2021)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2022]) is not None:
            aa(2022)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2023]) is not None:
            aa(2023)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2024]) is not None:
            aa(2024)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2025]) is not None:
            aa(2025)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2026]) is not None:
            aa(2026)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2027]) is not None:
            aa(2027)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2028]) is not None:
            aa(2028)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2029]) is not None:
            aa(2029)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2030]) is not None:
            aa(2030)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2031]) is not None:
            aa(2031)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2032]) is not None:
            aa(2032)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2033]) is not None:
            aa(2033)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2034]) is not None:
            aa(2034)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2035]) is not None:
            aa(2035)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2036]) is not None:
            aa(2036)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2037]) is not None:
            aa(2037)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2038]) is not None:
            aa(2038)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2039]) is not None:
            aa(2039)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2040]) is not None:
            aa(2040)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2041]) is not None:
            aa(2041)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2042]) is not None:
            aa(2042)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2043]) is not None:
            aa(2043)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2044]) is not None:
            aa(2044)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2045]) is not None:
            aa(2045)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2046]) is not None:
            aa(2046)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2047]) is not None:
            aa(2047)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2048]) is not None:
            aa(2048)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2049]) is not None:
            aa(2049)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2050]) is not None:
            aa(2050)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2051]) is not None:
            aa(2051)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2052]) is not None:
            aa(2052)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2053]) is not None:
            aa(2053)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2054]) is not None:
            aa(2054)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2055]) is not None:
            aa(2055)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2056]) is not None:
            aa(2056)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2057]) is not None:
            aa(2057)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2058]) is not None:
            aa(2058)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2059]) is not None:
            aa(2059)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2060]) is not None:
            aa(2060)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2061]) is not None:
            aa(2061)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2062]) is not None:
            aa(2062)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2063]) is not None:
            aa(2063)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2064]) is not None:
            aa(2064)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2065]) is not None:
            aa(2065)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2066]) is not None:
            aa(2066)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2067]) is not None:
            aa(2067)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2068]) is not None:
            aa(2068)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2075]) is not None:
            aa(2075)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2076]) is not None:
            aa(2076)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2077]) is not None:
            aa(2077)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2078]) is not None:
            aa(2078)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2079]) is not None:
            aa(2079)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2080]) is not None:
            aa(2080)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2081]) is not None:
            aa(2081)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2082]) is not None:
            aa(2082)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2083]) is not None:
            aa(2083)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2084]) is not None:
            aa(2084)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2085]) is not None:
            aa(2085)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2086]) is not None:
            aa(2086)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2087]) is not None:
            aa(2087)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2088]) is not None:
            aa(2088)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2089]) is not None:
            aa(2089)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2090]) is not None:
            aa(2090)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2091]) is not None:
            aa(2091)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2092]) is not None:
            aa(2092)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2093]) is not None:
            aa(2093)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2094]) is not None:
            aa(2094)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2095]) is not None:
            aa(2095)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2096]) is not None:
            aa(2096)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2097]) is not None:
            aa(2097)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2098]) is not None:
            aa(2098)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2099]) is not None:
            aa(2099)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2100]) is not None:
            aa(2100)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2101]) is not None:
            aa(2101)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2102]) is not None:
            aa(2102)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2103]) is not None:
            aa(2103)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2104]) is not None:
            aa(2104)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2105]) is not None:
            aa(2105)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2106]) is not None:
            aa(2106)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2107]) is not None:
            aa(2107)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2108]) is not None:
            aa(2108)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2109]) is not None:
            aa(2109)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2110]) is not None:
            aa(2110)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2111]) is not None:
            aa(2111)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2112]) is not None:
            aa(2112)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2113]) is not None:
            aa(2113)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2114]) is not None:
            aa(2114)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2115]) is not None:
            aa(2115)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2116]) is not None:
            aa(2116)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2117]) is not None:
            aa(2117)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2118]) is not None:
            aa(2118)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2119]) is not None:
            aa(2119)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2120]) is not None:
            aa(2120)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2121]) is not None:
            aa(2121)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2122]) is not None:
            aa(2122)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2123]) is not None:
            aa(2123)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2124]) is not None:
            aa(2124)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2131]) is not None:
            aa(2131)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2132]) is not None:
            aa(2132)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2133]) is not None:
            aa(2133)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2134]) is not None:
            aa(2134)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2135]) is not None:
            aa(2135)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2136]) is not None:
            aa(2136)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2137]) is not None:
            aa(2137)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2138]) is not None:
            aa(2138)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2139]) is not None:
            aa(2139)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2140]) is not None:
            aa(2140)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2141]) is not None:
            aa(2141)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2142]) is not None:
            aa(2142)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2143]) is not None:
            aa(2143)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2144]) is not None:
            aa(2144)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2145]) is not None:
            aa(2145)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2146]) is not None:
            aa(2146)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2147]) is not None:
            aa(2147)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2148]) is not None:
            aa(2148)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2149]) is not None:
            aa(2149)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2150]) is not None:
            aa(2150)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2151]) is not None:
            aa(2151)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2152]) is not None:
            aa(2152)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2153]) is not None:
            aa(2153)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2154]) is not None:
            aa(2154)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2155]) is not None:
            aa(2155)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2156]) is not None:
            aa(2156)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2157]) is not None:
            aa(2157)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2158]) is not None:
            aa(2158)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2159]) is not None:
            aa(2159)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2160]) is not None:
            aa(2160)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2161]) is not None:
            aa(2161)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2162]) is not None:
            aa(2162)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2163]) is not None:
            aa(2163)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2164]) is not None:
            aa(2164)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2165]) is not None:
            aa(2165)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2166]) is not None:
            aa(2166)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2167]) is not None:
            aa(2167)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2168]) is not None:
            aa(2168)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2169]) is not None:
            aa(2169)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2170]) is not None:
            aa(2170)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2171]) is not None:
            aa(2171)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2172]) is not None:
            aa(2172)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2173]) is not None:
            aa(2173)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2174]) is not None:
            aa(2174)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2175]) is not None:
            aa(2175)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2176]) is not None:
            aa(2176)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2177]) is not None:
            aa(2177)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2178]) is not None:
            aa(2178)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2179]) is not None:
            aa(2179)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2180]) is not None:
            aa(2180)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2187]) is not None:
            aa(2187)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2188]) is not None:
            aa(2188)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2189]) is not None:
            aa(2189)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2190]) is not None:
            aa(2190)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2191]) is not None:
            aa(2191)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2192]) is not None:
            aa(2192)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2193]) is not None:
            aa(2193)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2194]) is not None:
            aa(2194)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2195]) is not None:
            aa(2195)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2196]) is not None:
            aa(2196)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2197]) is not None:
            aa(2197)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2198]) is not None:
            aa(2198)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2199]) is not None:
            aa(2199)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2200]) is not None:
            aa(2200)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2201]) is not None:
            aa(2201)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2202]) is not None:
            aa(2202)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2203]) is not None:
            aa(2203)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2204]) is not None:
            aa(2204)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2205]) is not None:
            aa(2205)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2206]) is not None:
            aa(2206)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2207]) is not None:
            aa(2207)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2208]) is not None:
            aa(2208)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2209]) is not None:
            aa(2209)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2210]) is not None:
            aa(2210)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2211]) is not None:
            aa(2211)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2212]) is not None:
            aa(2212)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2213]) is not None:
            aa(2213)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2214]) is not None:
            aa(2214)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2215]) is not None:
            aa(2215)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2216]) is not None:
            aa(2216)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2217]) is not None:
            aa(2217)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2218]) is not None:
            aa(2218)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2219]) is not None:
            aa(2219)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2220]) is not None:
            aa(2220)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2221]) is not None:
            aa(2221)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2222]) is not None:
            aa(2222)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2223]) is not None:
            aa(2223)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2224]) is not None:
            aa(2224)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2225]) is not None:
            aa(2225)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2226]) is not None:
            aa(2226)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2227]) is not None:
            aa(2227)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2228]) is not None:
            aa(2228)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2229]) is not None:
            aa(2229)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2230]) is not None:
            aa(2230)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2231]) is not None:
            aa(2231)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2232]) is not None:
            aa(2232)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2233]) is not None:
            aa(2233)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2234]) is not None:
            aa(2234)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2235]) is not None:
            aa(2235)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2236]) is not None:
            aa(2236)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2243]) is not None:
            aa(2243)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2244]) is not None:
            aa(2244)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2245]) is not None:
            aa(2245)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2246]) is not None:
            aa(2246)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2247]) is not None:
            aa(2247)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2248]) is not None:
            aa(2248)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2249]) is not None:
            aa(2249)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2250]) is not None:
            aa(2250)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2251]) is not None:
            aa(2251)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2252]) is not None:
            aa(2252)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2253]) is not None:
            aa(2253)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2254]) is not None:
            aa(2254)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2255]) is not None:
            aa(2255)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2256]) is not None:
            aa(2256)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2257]) is not None:
            aa(2257)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2258]) is not None:
            aa(2258)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2259]) is not None:
            aa(2259)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2260]) is not None:
            aa(2260)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2261]) is not None:
            aa(2261)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2262]) is not None:
            aa(2262)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2263]) is not None:
            aa(2263)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2264]) is not None:
            aa(2264)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2265]) is not None:
            aa(2265)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2266]) is not None:
            aa(2266)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2267]) is not None:
            aa(2267)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2268]) is not None:
            aa(2268)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2269]) is not None:
            aa(2269)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2270]) is not None:
            aa(2270)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2271]) is not None:
            aa(2271)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2272]) is not None:
            aa(2272)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2273]) is not None:
            aa(2273)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2274]) is not None:
            aa(2274)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2275]) is not None:
            aa(2275)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2276]) is not None:
            aa(2276)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2277]) is not None:
            aa(2277)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2278]) is not None:
            aa(2278)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2279]) is not None:
            aa(2279)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2280]) is not None:
            aa(2280)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2281]) is not None:
            aa(2281)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2282]) is not None:
            aa(2282)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2283]) is not None:
            aa(2283)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2284]) is not None:
            aa(2284)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2285]) is not None:
            aa(2285)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2286]) is not None:
            aa(2286)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2287]) is not None:
            aa(2287)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2288]) is not None:
            aa(2288)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2289]) is not None:
            aa(2289)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2290]) is not None:
            aa(2290)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2291]) is not None:
            aa(2291)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2292]) is not None:
            aa(2292)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2299]) is not None:
            aa(2299)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2300]) is not None:
            aa(2300)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2301]) is not None:
            aa(2301)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2302]) is not None:
            aa(2302)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2303]) is not None:
            aa(2303)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2304]) is not None:
            aa(2304)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2305]) is not None:
            aa(2305)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2306]) is not None:
            aa(2306)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2307]) is not None:
            aa(2307)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2308]) is not None:
            aa(2308)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2309]) is not None:
            aa(2309)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2310]) is not None:
            aa(2310)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2311]) is not None:
            aa(2311)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2312]) is not None:
            aa(2312)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2313]) is not None:
            aa(2313)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2314]) is not None:
            aa(2314)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2315]) is not None:
            aa(2315)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2316]) is not None:
            aa(2316)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2317]) is not None:
            aa(2317)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2318]) is not None:
            aa(2318)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2319]) is not None:
            aa(2319)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2320]) is not None:
            aa(2320)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2321]) is not None:
            aa(2321)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2322]) is not None:
            aa(2322)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2323]) is not None:
            aa(2323)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2324]) is not None:
            aa(2324)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2325]) is not None:
            aa(2325)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2326]) is not None:
            aa(2326)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2327]) is not None:
            aa(2327)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2328]) is not None:
            aa(2328)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2329]) is not None:
            aa(2329)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2330]) is not None:
            aa(2330)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2331]) is not None:
            aa(2331)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2332]) is not None:
            aa(2332)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2333]) is not None:
            aa(2333)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2334]) is not None:
            aa(2334)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2335]) is not None:
            aa(2335)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2336]) is not None:
            aa(2336)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2337]) is not None:
            aa(2337)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2338]) is not None:
            aa(2338)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2339]) is not None:
            aa(2339)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2340]) is not None:
            aa(2340)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2341]) is not None:
            aa(2341)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2342]) is not None:
            aa(2342)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2343]) is not None:
            aa(2343)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2344]) is not None:
            aa(2344)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2345]) is not None:
            aa(2345)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2346]) is not None:
            aa(2346)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2347]) is not None:
            aa(2347)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2348]) is not None:
            aa(2348)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2355]) is not None:
            aa(2355)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2356]) is not None:
            aa(2356)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2357]) is not None:
            aa(2357)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2358]) is not None:
            aa(2358)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2359]) is not None:
            aa(2359)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2360]) is not None:
            aa(2360)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2361]) is not None:
            aa(2361)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2362]) is not None:
            aa(2362)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2363]) is not None:
            aa(2363)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2364]) is not None:
            aa(2364)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2365]) is not None:
            aa(2365)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2366]) is not None:
            aa(2366)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2367]) is not None:
            aa(2367)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2368]) is not None:
            aa(2368)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2369]) is not None:
            aa(2369)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2370]) is not None:
            aa(2370)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2371]) is not None:
            aa(2371)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2372]) is not None:
            aa(2372)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2373]) is not None:
            aa(2373)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2374]) is not None:
            aa(2374)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2375]) is not None:
            aa(2375)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2376]) is not None:
            aa(2376)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2377]) is not None:
            aa(2377)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2378]) is not None:
            aa(2378)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2379]) is not None:
            aa(2379)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2380]) is not None:
            aa(2380)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2381]) is not None:
            aa(2381)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2382]) is not None:
            aa(2382)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2383]) is not None:
            aa(2383)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2384]) is not None:
            aa(2384)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2385]) is not None:
            aa(2385)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2386]) is not None:
            aa(2386)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2387]) is not None:
            aa(2387)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2388]) is not None:
            aa(2388)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2389]) is not None:
            aa(2389)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2390]) is not None:
            aa(2390)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2391]) is not None:
            aa(2391)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2392]) is not None:
            aa(2392)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2393]) is not None:
            aa(2393)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2394]) is not None:
            aa(2394)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2395]) is not None:
            aa(2395)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2396]) is not None:
            aa(2396)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2397]) is not None:
            aa(2397)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2398]) is not None:
            aa(2398)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2399]) is not None:
            aa(2399)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2400]) is not None:
            aa(2400)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2401]) is not None:
            aa(2401)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2402]) is not None:
            aa(2402)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2403]) is not None:
            aa(2403)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2404]) is not None:
            aa(2404)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2411]) is not None:
            aa(2411)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2412]) is not None:
            aa(2412)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2413]) is not None:
            aa(2413)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2414]) is not None:
            aa(2414)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2415]) is not None:
            aa(2415)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2416]) is not None:
            aa(2416)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2417]) is not None:
            aa(2417)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2418]) is not None:
            aa(2418)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2419]) is not None:
            aa(2419)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2420]) is not None:
            aa(2420)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2421]) is not None:
            aa(2421)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2422]) is not None:
            aa(2422)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2423]) is not None:
            aa(2423)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2424]) is not None:
            aa(2424)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2425]) is not None:
            aa(2425)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2426]) is not None:
            aa(2426)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2427]) is not None:
            aa(2427)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2428]) is not None:
            aa(2428)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2429]) is not None:
            aa(2429)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2430]) is not None:
            aa(2430)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2431]) is not None:
            aa(2431)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2432]) is not None:
            aa(2432)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2433]) is not None:
            aa(2433)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2434]) is not None:
            aa(2434)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2435]) is not None:
            aa(2435)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2436]) is not None:
            aa(2436)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2437]) is not None:
            aa(2437)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2438]) is not None:
            aa(2438)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2439]) is not None:
            aa(2439)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2440]) is not None:
            aa(2440)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2441]) is not None:
            aa(2441)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2442]) is not None:
            aa(2442)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2443]) is not None:
            aa(2443)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2444]) is not None:
            aa(2444)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2445]) is not None:
            aa(2445)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2446]) is not None:
            aa(2446)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2447]) is not None:
            aa(2447)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2448]) is not None:
            aa(2448)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2449]) is not None:
            aa(2449)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2450]) is not None:
            aa(2450)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2451]) is not None:
            aa(2451)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2452]) is not None:
            aa(2452)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2453]) is not None:
            aa(2453)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2454]) is not None:
            aa(2454)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2455]) is not None:
            aa(2455)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2456]) is not None:
            aa(2456)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2457]) is not None:
            aa(2457)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2458]) is not None:
            aa(2458)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2459]) is not None:
            aa(2459)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2460]) is not None:
            aa(2460)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2467]) is not None:
            aa(2467)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2468]) is not None:
            aa(2468)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2469]) is not None:
            aa(2469)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2470]) is not None:
            aa(2470)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2471]) is not None:
            aa(2471)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2472]) is not None:
            aa(2472)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2473]) is not None:
            aa(2473)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2474]) is not None:
            aa(2474)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2475]) is not None:
            aa(2475)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2476]) is not None:
            aa(2476)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2477]) is not None:
            aa(2477)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2478]) is not None:
            aa(2478)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2479]) is not None:
            aa(2479)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2480]) is not None:
            aa(2480)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2481]) is not None:
            aa(2481)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2482]) is not None:
            aa(2482)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2483]) is not None:
            aa(2483)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2484]) is not None:
            aa(2484)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2485]) is not None:
            aa(2485)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2486]) is not None:
            aa(2486)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2487]) is not None:
            aa(2487)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2488]) is not None:
            aa(2488)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2489]) is not None:
            aa(2489)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2490]) is not None:
            aa(2490)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2491]) is not None:
            aa(2491)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2492]) is not None:
            aa(2492)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2493]) is not None:
            aa(2493)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2494]) is not None:
            aa(2494)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2495]) is not None:
            aa(2495)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2496]) is not None:
            aa(2496)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2497]) is not None:
            aa(2497)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2498]) is not None:
            aa(2498)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2499]) is not None:
            aa(2499)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2500]) is not None:
            aa(2500)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2501]) is not None:
            aa(2501)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2502]) is not None:
            aa(2502)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2503]) is not None:
            aa(2503)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2504]) is not None:
            aa(2504)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2505]) is not None:
            aa(2505)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2506]) is not None:
            aa(2506)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2507]) is not None:
            aa(2507)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2508]) is not None:
            aa(2508)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2509]) is not None:
            aa(2509)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2510]) is not None:
            aa(2510)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2511]) is not None:
            aa(2511)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2512]) is not None:
            aa(2512)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2513]) is not None:
            aa(2513)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2514]) is not None:
            aa(2514)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2515]) is not None:
            aa(2515)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2516]) is not None:
            aa(2516)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2523]) is not None:
            aa(2523)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2524]) is not None:
            aa(2524)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2525]) is not None:
            aa(2525)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2526]) is not None:
            aa(2526)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2527]) is not None:
            aa(2527)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2528]) is not None:
            aa(2528)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2529]) is not None:
            aa(2529)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2530]) is not None:
            aa(2530)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2531]) is not None:
            aa(2531)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2532]) is not None:
            aa(2532)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2533]) is not None:
            aa(2533)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2534]) is not None:
            aa(2534)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2535]) is not None:
            aa(2535)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2536]) is not None:
            aa(2536)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2537]) is not None:
            aa(2537)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2538]) is not None:
            aa(2538)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2539]) is not None:
            aa(2539)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2540]) is not None:
            aa(2540)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2541]) is not None:
            aa(2541)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2542]) is not None:
            aa(2542)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2543]) is not None:
            aa(2543)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2544]) is not None:
            aa(2544)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2545]) is not None:
            aa(2545)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2546]) is not None:
            aa(2546)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2547]) is not None:
            aa(2547)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2548]) is not None:
            aa(2548)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2549]) is not None:
            aa(2549)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2550]) is not None:
            aa(2550)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2551]) is not None:
            aa(2551)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2552]) is not None:
            aa(2552)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2553]) is not None:
            aa(2553)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2554]) is not None:
            aa(2554)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2555]) is not None:
            aa(2555)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2556]) is not None:
            aa(2556)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2557]) is not None:
            aa(2557)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2558]) is not None:
            aa(2558)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2559]) is not None:
            aa(2559)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2560]) is not None:
            aa(2560)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2561]) is not None:
            aa(2561)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2562]) is not None:
            aa(2562)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2563]) is not None:
            aa(2563)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2564]) is not None:
            aa(2564)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2565]) is not None:
            aa(2565)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2566]) is not None:
            aa(2566)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2567]) is not None:
            aa(2567)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2568]) is not None:
            aa(2568)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2569]) is not None:
            aa(2569)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2570]) is not None:
            aa(2570)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2571]) is not None:
            aa(2571)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2572]) is not None:
            aa(2572)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2579]) is not None:
            aa(2579)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2580]) is not None:
            aa(2580)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2581]) is not None:
            aa(2581)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2582]) is not None:
            aa(2582)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2583]) is not None:
            aa(2583)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2584]) is not None:
            aa(2584)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2585]) is not None:
            aa(2585)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2586]) is not None:
            aa(2586)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2587]) is not None:
            aa(2587)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2588]) is not None:
            aa(2588)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2589]) is not None:
            aa(2589)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2590]) is not None:
            aa(2590)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2591]) is not None:
            aa(2591)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2592]) is not None:
            aa(2592)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2593]) is not None:
            aa(2593)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2594]) is not None:
            aa(2594)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2595]) is not None:
            aa(2595)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2596]) is not None:
            aa(2596)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2597]) is not None:
            aa(2597)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2598]) is not None:
            aa(2598)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2599]) is not None:
            aa(2599)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2600]) is not None:
            aa(2600)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2601]) is not None:
            aa(2601)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2602]) is not None:
            aa(2602)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2603]) is not None:
            aa(2603)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2604]) is not None:
            aa(2604)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2605]) is not None:
            aa(2605)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2606]) is not None:
            aa(2606)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2607]) is not None:
            aa(2607)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2608]) is not None:
            aa(2608)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2609]) is not None:
            aa(2609)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2610]) is not None:
            aa(2610)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2611]) is not None:
            aa(2611)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2612]) is not None:
            aa(2612)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2613]) is not None:
            aa(2613)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2614]) is not None:
            aa(2614)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2615]) is not None:
            aa(2615)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2616]) is not None:
            aa(2616)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2617]) is not None:
            aa(2617)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2618]) is not None:
            aa(2618)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2619]) is not None:
            aa(2619)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2620]) is not None:
            aa(2620)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2621]) is not None:
            aa(2621)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2622]) is not None:
            aa(2622)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2623]) is not None:
            aa(2623)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2624]) is not None:
            aa(2624)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2625]) is not None:
            aa(2625)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2626]) is not None:
            aa(2626)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2627]) is not None:
            aa(2627)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2628]) is not None:
            aa(2628)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2635]) is not None:
            aa(2635)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2636]) is not None:
            aa(2636)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2637]) is not None:
            aa(2637)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2638]) is not None:
            aa(2638)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2639]) is not None:
            aa(2639)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2640]) is not None:
            aa(2640)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2641]) is not None:
            aa(2641)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2642]) is not None:
            aa(2642)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2643]) is not None:
            aa(2643)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2644]) is not None:
            aa(2644)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2645]) is not None:
            aa(2645)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2646]) is not None:
            aa(2646)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2647]) is not None:
            aa(2647)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2648]) is not None:
            aa(2648)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2649]) is not None:
            aa(2649)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2650]) is not None:
            aa(2650)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2651]) is not None:
            aa(2651)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2652]) is not None:
            aa(2652)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2653]) is not None:
            aa(2653)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2654]) is not None:
            aa(2654)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2655]) is not None:
            aa(2655)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2656]) is not None:
            aa(2656)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2657]) is not None:
            aa(2657)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2658]) is not None:
            aa(2658)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2659]) is not None:
            aa(2659)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2660]) is not None:
            aa(2660)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2661]) is not None:
            aa(2661)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2662]) is not None:
            aa(2662)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2663]) is not None:
            aa(2663)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2664]) is not None:
            aa(2664)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2665]) is not None:
            aa(2665)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2666]) is not None:
            aa(2666)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2667]) is not None:
            aa(2667)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2668]) is not None:
            aa(2668)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2669]) is not None:
            aa(2669)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2670]) is not None:
            aa(2670)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2671]) is not None:
            aa(2671)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2672]) is not None:
            aa(2672)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2673]) is not None:
            aa(2673)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2674]) is not None:
            aa(2674)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2675]) is not None:
            aa(2675)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2676]) is not None:
            aa(2676)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2677]) is not None:
            aa(2677)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2678]) is not None:
            aa(2678)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2679]) is not None:
            aa(2679)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2680]) is not None:
            aa(2680)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2681]) is not None:
            aa(2681)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2682]) is not None:
            aa(2682)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2683]) is not None:
            aa(2683)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2684]) is not None:
            aa(2684)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2691]) is not None:
            aa(2691)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2692]) is not None:
            aa(2692)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2693]) is not None:
            aa(2693)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2694]) is not None:
            aa(2694)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2695]) is not None:
            aa(2695)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2696]) is not None:
            aa(2696)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2697]) is not None:
            aa(2697)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2698]) is not None:
            aa(2698)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2699]) is not None:
            aa(2699)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2700]) is not None:
            aa(2700)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2701]) is not None:
            aa(2701)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2702]) is not None:
            aa(2702)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2703]) is not None:
            aa(2703)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2704]) is not None:
            aa(2704)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2705]) is not None:
            aa(2705)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2706]) is not None:
            aa(2706)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2707]) is not None:
            aa(2707)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2708]) is not None:
            aa(2708)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2709]) is not None:
            aa(2709)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2710]) is not None:
            aa(2710)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2711]) is not None:
            aa(2711)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2712]) is not None:
            aa(2712)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2713]) is not None:
            aa(2713)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2714]) is not None:
            aa(2714)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2715]) is not None:
            aa(2715)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2716]) is not None:
            aa(2716)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2717]) is not None:
            aa(2717)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2718]) is not None:
            aa(2718)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2719]) is not None:
            aa(2719)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2720]) is not None:
            aa(2720)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2721]) is not None:
            aa(2721)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2722]) is not None:
            aa(2722)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2723]) is not None:
            aa(2723)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2724]) is not None:
            aa(2724)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2725]) is not None:
            aa(2725)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2726]) is not None:
            aa(2726)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2727]) is not None:
            aa(2727)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2728]) is not None:
            aa(2728)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2729]) is not None:
            aa(2729)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2730]) is not None:
            aa(2730)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2731]) is not None:
            aa(2731)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2732]) is not None:
            aa(2732)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2733]) is not None:
            aa(2733)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2734]) is not None:
            aa(2734)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2735]) is not None:
            aa(2735)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2736]) is not None:
            aa(2736)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2737]) is not None:
            aa(2737)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2738]) is not None:
            aa(2738)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2739]) is not None:
            aa(2739)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2740]) is not None:
            aa(2740)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2747]) is not None:
            aa(2747)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2748]) is not None:
            aa(2748)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2749]) is not None:
            aa(2749)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2750]) is not None:
            aa(2750)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2751]) is not None:
            aa(2751)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2752]) is not None:
            aa(2752)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2753]) is not None:
            aa(2753)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2754]) is not None:
            aa(2754)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2755]) is not None:
            aa(2755)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2756]) is not None:
            aa(2756)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2757]) is not None:
            aa(2757)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2758]) is not None:
            aa(2758)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2759]) is not None:
            aa(2759)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2760]) is not None:
            aa(2760)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2761]) is not None:
            aa(2761)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2762]) is not None:
            aa(2762)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2763]) is not None:
            aa(2763)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2764]) is not None:
            aa(2764)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2765]) is not None:
            aa(2765)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2766]) is not None:
            aa(2766)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2767]) is not None:
            aa(2767)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2768]) is not None:
            aa(2768)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2769]) is not None:
            aa(2769)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2770]) is not None:
            aa(2770)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2771]) is not None:
            aa(2771)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2772]) is not None:
            aa(2772)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2773]) is not None:
            aa(2773)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2774]) is not None:
            aa(2774)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2775]) is not None:
            aa(2775)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2776]) is not None:
            aa(2776)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2777]) is not None:
            aa(2777)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2778]) is not None:
            aa(2778)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2779]) is not None:
            aa(2779)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2780]) is not None:
            aa(2780)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2781]) is not None:
            aa(2781)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2782]) is not None:
            aa(2782)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2783]) is not None:
            aa(2783)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2784]) is not None:
            aa(2784)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2785]) is not None:
            aa(2785)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2786]) is not None:
            aa(2786)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2787]) is not None:
            aa(2787)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2788]) is not None:
            aa(2788)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2789]) is not None:
            aa(2789)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2790]) is not None:
            aa(2790)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2791]) is not None:
            aa(2791)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2792]) is not None:
            aa(2792)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2793]) is not None:
            aa(2793)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2794]) is not None:
            aa(2794)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2795]) is not None:
            aa(2795)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2796]) is not None:
            aa(2796)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2803]) is not None:
            aa(2803)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2804]) is not None:
            aa(2804)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2805]) is not None:
            aa(2805)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2806]) is not None:
            aa(2806)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2807]) is not None:
            aa(2807)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2808]) is not None:
            aa(2808)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2809]) is not None:
            aa(2809)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2810]) is not None:
            aa(2810)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2811]) is not None:
            aa(2811)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2812]) is not None:
            aa(2812)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2813]) is not None:
            aa(2813)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2814]) is not None:
            aa(2814)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2815]) is not None:
            aa(2815)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2816]) is not None:
            aa(2816)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2817]) is not None:
            aa(2817)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2818]) is not None:
            aa(2818)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2819]) is not None:
            aa(2819)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2820]) is not None:
            aa(2820)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2821]) is not None:
            aa(2821)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2822]) is not None:
            aa(2822)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2823]) is not None:
            aa(2823)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2824]) is not None:
            aa(2824)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2825]) is not None:
            aa(2825)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2826]) is not None:
            aa(2826)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2827]) is not None:
            aa(2827)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2828]) is not None:
            aa(2828)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2829]) is not None:
            aa(2829)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2830]) is not None:
            aa(2830)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2831]) is not None:
            aa(2831)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2832]) is not None:
            aa(2832)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2833]) is not None:
            aa(2833)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2834]) is not None:
            aa(2834)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2835]) is not None:
            aa(2835)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2836]) is not None:
            aa(2836)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2837]) is not None:
            aa(2837)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2838]) is not None:
            aa(2838)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2839]) is not None:
            aa(2839)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2840]) is not None:
            aa(2840)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2841]) is not None:
            aa(2841)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2842]) is not None:
            aa(2842)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2843]) is not None:
            aa(2843)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2844]) is not None:
            aa(2844)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2845]) is not None:
            aa(2845)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2846]) is not None:
            aa(2846)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2847]) is not None:
            aa(2847)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2848]) is not None:
            aa(2848)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2849]) is not None:
            aa(2849)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2850]) is not None:
            aa(2850)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2851]) is not None:
            aa(2851)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2852]) is not None:
            aa(2852)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2859]) is not None:
            aa(2859)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2860]) is not None:
            aa(2860)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2861]) is not None:
            aa(2861)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2862]) is not None:
            aa(2862)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2863]) is not None:
            aa(2863)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2864]) is not None:
            aa(2864)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2865]) is not None:
            aa(2865)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2866]) is not None:
            aa(2866)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2867]) is not None:
            aa(2867)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2868]) is not None:
            aa(2868)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2869]) is not None:
            aa(2869)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2870]) is not None:
            aa(2870)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2871]) is not None:
            aa(2871)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2872]) is not None:
            aa(2872)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2873]) is not None:
            aa(2873)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2874]) is not None:
            aa(2874)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2875]) is not None:
            aa(2875)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2876]) is not None:
            aa(2876)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2877]) is not None:
            aa(2877)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2878]) is not None:
            aa(2878)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2879]) is not None:
            aa(2879)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2880]) is not None:
            aa(2880)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2881]) is not None:
            aa(2881)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2882]) is not None:
            aa(2882)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2883]) is not None:
            aa(2883)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2884]) is not None:
            aa(2884)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2885]) is not None:
            aa(2885)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2886]) is not None:
            aa(2886)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2887]) is not None:
            aa(2887)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2888]) is not None:
            aa(2888)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2889]) is not None:
            aa(2889)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2890]) is not None:
            aa(2890)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2891]) is not None:
            aa(2891)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2892]) is not None:
            aa(2892)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2893]) is not None:
            aa(2893)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2894]) is not None:
            aa(2894)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2895]) is not None:
            aa(2895)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2896]) is not None:
            aa(2896)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2897]) is not None:
            aa(2897)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2898]) is not None:
            aa(2898)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2899]) is not None:
            aa(2899)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2900]) is not None:
            aa(2900)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2901]) is not None:
            aa(2901)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2902]) is not None:
            aa(2902)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2903]) is not None:
            aa(2903)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2904]) is not None:
            aa(2904)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2905]) is not None:
            aa(2905)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2906]) is not None:
            aa(2906)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2907]) is not None:
            aa(2907)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2908]) is not None:
            aa(2908)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2915]) is not None:
            aa(2915)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2916]) is not None:
            aa(2916)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2917]) is not None:
            aa(2917)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2918]) is not None:
            aa(2918)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2919]) is not None:
            aa(2919)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2920]) is not None:
            aa(2920)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2921]) is not None:
            aa(2921)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2922]) is not None:
            aa(2922)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2923]) is not None:
            aa(2923)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2924]) is not None:
            aa(2924)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2925]) is not None:
            aa(2925)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2926]) is not None:
            aa(2926)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2927]) is not None:
            aa(2927)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2928]) is not None:
            aa(2928)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2929]) is not None:
            aa(2929)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2930]) is not None:
            aa(2930)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2931]) is not None:
            aa(2931)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2932]) is not None:
            aa(2932)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2933]) is not None:
            aa(2933)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2934]) is not None:
            aa(2934)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2935]) is not None:
            aa(2935)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2936]) is not None:
            aa(2936)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2937]) is not None:
            aa(2937)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2938]) is not None:
            aa(2938)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2939]) is not None:
            aa(2939)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2940]) is not None:
            aa(2940)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2941]) is not None:
            aa(2941)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2942]) is not None:
            aa(2942)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2943]) is not None:
            aa(2943)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2944]) is not None:
            aa(2944)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2945]) is not None:
            aa(2945)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2946]) is not None:
            aa(2946)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2947]) is not None:
            aa(2947)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2948]) is not None:
            aa(2948)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2949]) is not None:
            aa(2949)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2950]) is not None:
            aa(2950)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2951]) is not None:
            aa(2951)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2952]) is not None:
            aa(2952)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2953]) is not None:
            aa(2953)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2954]) is not None:
            aa(2954)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2955]) is not None:
            aa(2955)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2956]) is not None:
            aa(2956)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2957]) is not None:
            aa(2957)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2958]) is not None:
            aa(2958)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2959]) is not None:
            aa(2959)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2960]) is not None:
            aa(2960)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2961]) is not None:
            aa(2961)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2962]) is not None:
            aa(2962)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2963]) is not None:
            aa(2963)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None
        if (t := ns[2964]) is not None:
            aa(2964)
            if (p := t.up) is not None:
                if ns[p] is not None:
                    cc[p] += 1
                else:
                    t.up = None

        # ── find leaves ──
        q = []
        qa = q.append
        for i in active:
            if not cc[i]:
                qa(i)

        # ── bottom-up BFS ──
        qi = 0
        while qi < len(q):
            u = q[qi]; qi += 1
            p = ns[u].up
            if p is not None:
                flow[p] += flow[u]
                cc[p] -= 1
                if not cc[p]:
                    qa(p)

        # ── top-down ──
        pressure = [0] * 3136
        nk = [0] * 3136
        sink_set = core_pos_set.copy()
        sink_add = sink_set.add
        THR = 24

        for u in reversed(q):
            p = ns[u].up
            if p is None:
                # root — use own kind
                pressure[u] = flow[u]
                k = kind[u]
            elif kind[p]:
                # direct child of a sink — per-branch pressure reset
                pressure[u] = flow[u]
                k = kind[p]
            else:
                # interior — inherit from parent
                pressure[u] = pressure[p]
                k = nk[p]
            nk[u] = k
            if k == 1 and pressure[u] <= THR:
                sink_add(u)

        cls.flow = flow
        cls.pressure = pressure
        cls.node_kind = nk
        cls.sink_set = sink_set
# ===---