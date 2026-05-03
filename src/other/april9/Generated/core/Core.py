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

class Core(Unit):

    @classmethod
    def init(cls):
        Unit.init()

    @classmethod
    def start_turn(cls):
        Unit.start_turn()
        CoreHistory.fill()
        SpawnManager.fill()
        print(f'est income: {MarketMaker.est_income}')

    @classmethod
    def run_turn(cls):
        # if BurnManager.should_burn_emergency():
        #     BurnManager.burn()

        # I think this is cleaner
        if SpawnManager.should_spawn_emergency():
            BurnManager.burn()
        
        if SpawnManager.should_spawn() or SpawnManager.should_spawn_emergency():
            SpawnManager.spawn()

    @classmethod
    def end_turn(cls):
        Unit.end_turn()

        if Globals.round > 666:
            Globals.ct.resign()
            raise Exception
