from cambc import *
from bots.basic9.utils.vision import Vision
from bots.basic9.utils.movement import Movement
from bots.basic9.utils.goal import Objective
from bots.basic9.utils.build import Build
from bots.basic9.utils.attack import Attack
from bots.basic9.utils.defense import Defense
from bots.basic9.builderbot import BuilderBot
from bots.basic9.core import Core
from bots.basic9.launcher import Launcher
from bots.basic9.sentinel import Sentinel
import random


class Player:
    def run(self, ct: Controller) -> None:
        random.seed(ct.get_current_round())

        if not hasattr(self, "robot"):
            vision = Vision(ct)
            vision.update()
            movement = Movement(ct, vision)
            objective = Objective(movement)
            build = Build(ct, vision, movement, objective)
            attack = Attack(ct, vision, movement, objective)
            defense = Defense(ct, vision, movement, objective)

            if ct.get_entity_type() == EntityType.BUILDER_BOT:
                self.robot = BuilderBot(
                    ct, vision, movement, objective, build, attack, defense
                )
            elif ct.get_entity_type() == EntityType.CORE:
                self.robot = Core(ct, vision, movement, objective, build)
            elif ct.get_entity_type() == EntityType.LAUNCHER:
                self.robot = Launcher(ct, vision, movement, objective, build)
            elif ct.get_entity_type() == EntityType.SENTINEL:
                self.robot = Sentinel(ct, vision)
        else:
            self.robot.vision.update()

        self.robot.run_macro()
        self.robot.run_micro()
