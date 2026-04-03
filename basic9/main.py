from cambc import *
from utils.vision import Vision
from utils.movement import Movement
from utils.goal import Objective
from utils.build import Build
from utils.attack import Attack
from utils.defense import Defense
from builderbot import BuilderBot
from core import Core
from launcher import Launcher
from sentinel import Sentinel
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
