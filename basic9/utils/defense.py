from cambc import *
from utils.constants import CARDINAL_DIRECTIONS


class Defense:
    def __init__(self, c: Controller, vision, movement, objective):
        self.c = c
        self.vision = vision
        self.movement = movement
        self.objective = objective

    def get_best_defense_target(self):
        return max(self.vision.needs_defend, key=lambda x: self.vision.needs_defend[x])

    def defend(self):
        target = self.objective.target

        if target not in self.vision.needs_defend:
            return True

        if self.vision.needs_defend[target] == 0:
            return True

        if self.c.get_position().distance_squared(target) > 2:
            self.movement.move_to(target)

        if self.c.get_position().distance_squared(target) > 2:
            return

        if self.c.can_heal(target):
            self.c.heal(target)

    def change_conveyor_orientation(self):
        target = self.objective.target

        if target not in self.vision.change_orientation:
            return True

        if self.c.get_position().distance_squared(target) > 2:
            self.movement.move_to(target)

        if self.c.get_position().distance_squared(target) > 2:
            return False

        prev_dir = self.c.get_direction(self.c.get_tile_building_id(target))
        if self.c.can_destroy(target):
            self.c.destroy(target)
            if self.c.can_build_conveyor(target, prev_dir.opposite()):
                self.c.build_conveyor(target, prev_dir.opposite())
                return True

        return False
