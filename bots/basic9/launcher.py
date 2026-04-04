from cambc import *
from bots.basic9.robot import Robot
from bots.basic9.utils.goal import Goal
import random


class Launcher(Robot):
    def __init__(self, ct, vision=None, movement=None, objective=None, build=None):
        super().__init__(ct, vision, movement, objective, build)

    def run_macro(self):
        for pos in self.vision.adj8(self.ct.get_position()):
            if (bbid := self.ct.get_tile_builder_bot_id(pos)) and self.ct.get_team(
                bbid
            ) == self.ct.get_team():
                if self.vision.priority_attack:
                    target = next(iter(self.vision.priority_attack))
                    if self.ct.can_launch(pos, target):
                        self.ct.launch(pos, target)
                        break

    def run_micro(self):
        pass
