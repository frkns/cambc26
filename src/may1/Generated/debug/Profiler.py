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
from Awubot import *
from Generated import *

class Profiler:
    _stack: list = []  # Now stores (start_time, round, desc)
    _stats: dict = {}  # desc -> [count, mean, M2, max]


     

    @classmethod
    def start(cls, desc: str = ""):
        cls._stack.append((Globals.ct.get_cpu_time_elapsed(), Globals.round, desc))

    @classmethod
    def end(cls, desc: str):

        end_time = Globals.ct.get_cpu_time_elapsed()
        end_round = Globals.round
        if not cls._stack:
            return
        start_time, start_round, start_desc = cls._stack.pop()
        
        # Check for round overflow
        if start_round != end_round:
            team = Globals.my_team.__str__()[-1]
            label = desc or start_desc or "<unknown>"
            warning = f"[{Globals.my_team.__str__()[-1]}][{Globals.my_type.value}] WARNING: Round overflow in '{label}': started in round {start_round}, ended in round {end_round}"
            print(warning)
            Debug.log(warning)
            return  # Don't record stats for overflowed measurements
        
        elapsed = (end_time - start_time) / 1_000_000
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

        team = Globals.my_team.__str__()[-1]
        s = f"[{Globals.my_team.__str__()[-1]}][{Globals.my_type.value}] {desc}: {cls._format_time(elapsed)}"

    @classmethod
    def end_now(cls, desc: str):
        end_time = Globals.ct.get_cpu_time_elapsed()
        end_round = Globals.round
        if not cls._stack:
            return
        start_time, start_round, start_desc = cls._stack.pop()
        
        # Check for round overflow
        if start_round != end_round:
            team = Globals.my_team.__str__()[-1]
            label = desc or start_desc or "<unknown>"
            warning = f"[{Globals.my_team.__str__()[-1]}][{Globals.my_type.value}] WARNING: Round overflow in '{label}': started in round {start_round}, ended in round {end_round}"
            print(warning)
            Debug.log(warning)
            return
        
        elapsed = (end_time - start_time) / 1_000_000

        team = Globals.my_team.__str__()[-1]
        s = f"[{Globals.my_team.__str__()[-1]}][{Globals.my_type.value}] {desc}: {cls._format_time(elapsed)}"
        print(s)
        Debug.log(s)

    @classmethod
    def start_turn_check(cls):
        if cls._stack:
            team = Globals.my_team.__str__()[-1]
            stale_descs = [entry[2] or "<unknown>" for entry in cls._stack]
            warning = f"[{Globals.my_team.__str__()[-1]}][{Globals.my_type.value}] WARNING: Profiler stack not empty at turn start (round {Globals.round}). Stale entries: {stale_descs}"
            print(warning)
            Debug.log(warning)
            cls._stack.clear()

    @classmethod
    def compare(cls, f, g):
        if Globals.round & 1:
            Profiler.start('1')
            ret = f()
            Profiler.end('1')
        else:
            Profiler.start('2')
            ret = g()
            Profiler.end('2')
        return ret

    @classmethod
    def _format_time(cls, t: float) -> str:
        if t < 1e-6:
            return f"{t * 1e9:.1f}ns"
        elif t < 1e-3:
            return f"{t * 1e6:.1f}µs"
        elif t < 1:
            return f"{t * 1e3:.2f}ms"
        else:
            return f"{t:.2f}s"

    @classmethod
    def report(cls):
        if not cls._stats:
            return
        team = Globals.my_team.__str__()[-1]
        Debug.tee(f" *  Profiling report {team}:")
        for desc, (count, mean, M2, max_time) in sorted(cls._stats.items()):
            stddev = math.sqrt(M2 / count) if count > 1 else 0.0
            s = (f"[{Globals.my_team.__str__()[-1]}][{Globals.my_type.value}] {desc}: "
                 f"avg={cls._format_time(mean)}, "
                 f"stddev={cls._format_time(stddev)}, "
                 f"max={cls._format_time(max_time)}, "
                 f"count={count}")
            Debug.tee(s)

    @classmethod
    def reset(cls):
        cls._stack.clear()
        cls._stats.clear()