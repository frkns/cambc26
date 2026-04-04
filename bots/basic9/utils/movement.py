from cambc import *
from bots.basic9.utils.bugpath import BugPath
from bots.basic9.utils.astar import Astar
import random


class Movement:
    def __init__(self, c: Controller, vision):
        self.c = c
        self.vision = vision

        self.bug = BugPath(c, vision)
        self.astar = Astar(c, vision)
        self.edges = list(
            set(Position(0, i) for i in range(self.vision.mapheight))
            | set(Position(i, 0) for i in range(self.vision.mapwidth))
            | set(
                Position(self.vision.mapwidth - 1, i)
                for i in range(self.vision.mapheight)
            )
            | set(
                Position(i, self.vision.mapheight - 1)
                for i in range(self.vision.mapwidth)
            )
        )

    def move_to(self, target: Position):
        if self.c.get_move_cooldown() != 0:
            return

        # if not self.astar.move_to(target):
        self.bug.move_to(target)

    def get_explore_target(self) -> Position:
        return random.choice(self.edges)
