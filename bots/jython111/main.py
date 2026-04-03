"""
Team Jython's bot
"""

import sys

from cambc import *
import unit
from core import Core
from builder import Builder
from breach import Breach
from sentinel import Sentinel
from gunner import Gunner
from launcher import Launcher
import data

DEBUG = data.DEBUG

class Player:
    def __init__(self):
        self.unit = None

    def initialize(self, ct: Controller) -> None:
        try:
            etype = ct.get_entity_type()
            if etype == EntityType.CORE:
                self.unit = Core(ct)
            elif etype == EntityType.BUILDER_BOT:
                self.unit = Builder(ct)
            elif etype == EntityType.BREACH:
                self.unit = Breach(ct)
            elif etype == EntityType.SENTINEL:
                self.unit = Sentinel(ct)
            elif etype == EntityType.GUNNER:
                self.unit = Gunner(ct)
            elif etype == EntityType.LAUNCHER:
                self.unit = Launcher(ct)
            else:
                self.unit = Core(ct)
        except Exception as e:
            print(f"Error during initialization (round {ct.get_current_round()}): ", e, file=sys.stderr)
            self.unit = Core(ct) # default to core if something goes wrong

    def tick(self, ct: Controller) -> None:
        if unit.ct == None:
            self.initialize(ct)

        self.unit.updateCt(ct)
        self.unit.startTurn()
        self.unit.runTurn()
        self.unit.endTurn()

    def run(self, ct: Controller) -> None:
        if DEBUG:
            self.tick(ct)
        else:
            try:
                self.tick(ct)
            except GameError as e:
                print(f"GameError during run (round {ct.get_current_round()} #{ct.get_id()}): ", e, file=sys.stderr)
            except Exception as e:
                print(f"Unexpected error during run (round {ct.get_current_round()} #{ct.get_id()}): ", e, file=sys.stderr)
