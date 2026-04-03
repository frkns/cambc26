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
from Awubot.nav.OmNom import OmNom


class DirectionPicker:
    class Candidate(NamedTuple):
        direction: Direction
        position: Position
        moveable: bool
        fill_moveable: bool
        rand_key: float

    cand: list[Candidate | None] = [None] * 9

    @classmethod
    def precompute(cls):
        for i in range(9):
            dir: Direction = Constants.ALL_DIRECTIONS[i]
            cls.cand[i] = cls.Candidate(
                dir,
                Globals.ct.get_position().add(dir),
                MoveManager.can_move(dir),
                MoveManager.can_fill_move(dir),
                random.random(),
            )

    @classmethod
    def is_better_than(cls, a: Candidate, b: Candidate) -> bool:
        if a.moveable and (not b.moveable):
            return True
        if (not a.moveable) and b.moveable:
            return False


        return a.rand_key < b.rand_key









