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
            case EntityType.SENTINEL:
                Sentinel.init()
                cls.me = Sentinel

    @classmethod
    def run(cls, ct: Controller):
        Globals.ct = ct  # in case not fixed...
        if cls.needs_init:
            cls.init(ct)
            cls.needs_init = False

        cls.me.start_turn()
        cls.me.run_turn()
        cls.me.end_turn()


class Player:
    def run(self, ct):
        try:
            Entrypoint.run(ct)
        except Exception as e:
            Debug.line(Position(0, 0), Color.RED)

            err = traceback.format_exc()
            Debug.tee(err)

            ct.resign()
