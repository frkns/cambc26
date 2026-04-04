from cambc import *
from bots.basic9.utils.constants import DIRECTIONS, CARDINAL_DIRECTIONS, CONVEYORS, TURRETS


class Attack:
    def __init__(self, c: Controller, vision, movement, objective):
        self.c = c
        self.vision = vision
        self.movement = movement
        self.objective = objective

    def try_build_launcher(self, pos: Position):
        if (
            self.vision.etype.get(pos, -1) == EntityType.LAUNCHER
            and self.vision.friendly[pos]
        ):
            return True

        if self.c.can_build_launcher(pos):
            self.c.build_launcher(pos)
            return True
        elif self.c.can_destroy(pos) and (
            self.vision.etype.get(pos, -1) != EntityType.SENTINEL
            or not self.vision.friendly.get(pos, False)
        ):
            self.c.destroy(pos)
            if self.c.can_build_launcher(pos):
                self.c.build_launcher(pos)
                return True

        return False

    

    def place_sentinel(self, pos: Position):
        if self.c.get_position().distance_squared(pos) > 2:
            self.movement.move_to(pos)
            if self.c.get_position().distance_squared(pos) > 2:
                return False

        if not self.vision.friendly.get(pos, False) and not self.c.is_tile_empty(pos):
            if self.c.get_position() != pos:
                self.movement.move_to(pos)

            if self.c.get_position() != pos:
                return False

            if not self.try_fire():
                return

        if self.c.get_position() == pos:
            self.movement.move_to(self.vision.randomdir(pos))

        bid = self.c.get_tile_building_id(pos)
        if bid is not None and self.c.get_entity_type(bid) == EntityType.SENTINEL:
            return True

        if (
            bid is not None
            and self.c.get_team(bid) != self.c.get_team()
            and self.c.is_tile_passable(pos)
        ):
            if self.c.get_position() != pos:
                self.movement.move_to(pos)

            if self.c.get_position() != pos:
                return False

            if self.c.can_fire(pos):
                self.c.fire(pos)
                return False

        if (
            bid is not None
            and self.c.get_team(bid) == self.c.get_team()
            and self.c.get_entity_type(bid) in CONVEYORS
        ):
            return True

        if self.c.get_position().distance_squared(pos) not in [1, 2]:
            return False

        best_dir = self.vision.best_sentinel_dir(pos)
        if best_dir is None:
            return True

        if self.c.can_build_sentinel(pos, best_dir):
            self.c.build_sentinel(pos, best_dir)
            return True
        elif self.c.can_destroy(pos) and self.c.get_sentinel_cost()[0] <= self.c.get_global_resources()[0]:
            self.c.destroy(pos)
            if self.c.can_build_sentinel(pos, best_dir):
                self.c.build_sentinel(pos, best_dir)
                return True

        return False

    def try_fire(self):
        hp = self.c.get_hp(self.c.get_tile_building_id(self.c.get_position()))
        if self.c.can_fire(self.c.get_position()):
            self.c.fire(self.c.get_position())
            if hp <= 2:
                if self.c.get_position() in self.vision.priority_attack:
                    self.vision.priority_attack.remove(self.c.get_position())
                return True

        return False

    def attack(self):
        if not self.vision.priority_attack:
            return True

        if self.c.get_position() in self.vision.priority_attack:
            return self.try_fire()

        target = min(
            self.vision.priority_attack,
            key=lambda x: x.distance_squared(self.c.get_position()),
        )
        if target.distance_squared(
            self.c.get_position()
        ) <= 2 and self.c.is_tile_passable(target):
            self.movement.move_to(target)
            return self.try_fire()

        cur = self.c.get_position()
        built_launcher = False
        for d in DIRECTIONS:
            if (
                self.vision.in_bounds(cur.add(d))
                and cur.add(d).distance_squared(target) <= 16
            ):
                if self.try_build_launcher(cur.add(d)):
                    built_launcher = True
                    break

        if not built_launcher:
            self.movement.move_to(target)

        return False
