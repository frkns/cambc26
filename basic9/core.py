from cambc import *
from utils.constants import *
from robot import Robot


class Core(Robot):
    def __init__(
        self, ct: Controller, vision=None, movement=None, objective=None, build=None
    ):
        super().__init__(ct, vision, movement, objective, build)
        self.bots_spawned = 0
        self.spawn_dirs = [
            Direction.NORTH,
            Direction.SOUTH,
            Direction.EAST,
            Direction.WEST,
            Direction.SOUTHWEST,
            Direction.SOUTHEAST,
            Direction.NORTHEAST,
            Direction.NORTHWEST,
        ]
        self.curr_pos = []

    def try_spawn(self, pos: Position) -> bool:
        c = self.ct
        if c.can_spawn(pos):
            c.spawn_builder(pos)
            return True

        return False

    def run_macro(self):
        if self.bots_spawned < 6 or (
            self.ct.get_global_resources()[0] >= 1000
            and self.ct.get_current_round() % 20 == 0
        ) or self.ct.get_hp() < 400:
            for d in self.spawn_dirs:
                if self.try_spawn(self.ct.get_position().add(d)):
                    self.bots_spawned += 1
                    break

    def run_micro(self):
        c = self.ct
