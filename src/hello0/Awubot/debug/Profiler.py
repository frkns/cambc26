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
from Awubot.explore.Explore import Explore
from Awubot.nav.DirectionPicker import DirectionPicker
from Awubot.nav.OmNom import OmNom


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
        for desc, (count, mean, M2, max_time) in sorted(cls._stats.items()):
            stddev = math.sqrt(M2 / count) if count > 1 else 0.0
            s = (f"[P] {desc}: "
                 f"avg={cls._format_time(mean)}, "
                 f"stddev={cls._format_time(stddev)}, "
                 f"max={cls._format_time(max_time)}, "
                 f"count={count}")
            print(s)
            Debug.log(s)

    @classmethod
    def reset(cls):
        cls._stack.clear()
        cls._stats.clear()
