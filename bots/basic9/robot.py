from cambc import *


class Robot:
    def __init__(
        self,
        ct: Controller,
        vision=None,
        movement=None,
        objective=None,
        build=None,
        attack=None,
        defense=None,
    ):
        self.ct = ct
        self.vision = vision
        self.movement = movement
        self.objective = objective
        self.build = build
        self.attack = attack
        self.defense = defense

    def run_macro(self):
        pass

    def run_micro(self):
        pass
