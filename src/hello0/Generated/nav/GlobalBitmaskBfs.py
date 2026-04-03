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
from Awubot.debug.Debug import Color, Debug
from Awubot.debug.Profiler import Profiler
from Awubot.explore.Explore import Explore
from Awubot.nav.DirectionPicker import DirectionPicker
from Awubot.nav.OmNom import OmNom


class GlobalBitmaskBfs:
    @classmethod
    def dists_from_pos(cls, pos: Position):
        S = MapMask.STRIDE
        FULL = MapMask.FULL
        passable = FULL & ~MapMask.wall
        W, H = Map.W, Map.H

        dist_flat = [1000000] * (S * H)
        start_idx = pos.y * S + pos.x
        dist_flat[start_idx] = 0

        # Early exit target: our position
        my_pos = Globals.ct.get_position()
        target_bit = 1 << (my_pos.y * S + my_pos.x)

        reached_from = 1 << start_idx
        reached_to = 0

        step = 1
        while reached_from != reached_to:
            # Expand 8-directionally (padding column in STRIDE prevents wrap)
            wide = reached_from | (reached_from << 1) | (reached_from >> 1)
            reached_to = (wide | (wide << S) | (wide >> S)) & passable

            # New cells = symmetric difference
            changed = reached_from ^ reached_to

            # Assign distances to new cells
            while changed:
                lsb = changed & -changed
                changed ^= lsb
                dist_flat[lsb.bit_length() - 1] = step

            # Early exit when we've reached our unit
            if reached_to & target_bit:
                break

            step += 1
            reached_from, reached_to = reached_to, reached_from

        return [[dist_flat[y * S + x] for y in range(H)] for x in range(W)]