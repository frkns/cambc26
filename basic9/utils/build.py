from cambc import *
from utils.constants import CARDINAL_DIRECTIONS


class Build:
    def __init__(self, c: Controller, vision, movement, objective):
        self.c = c
        self.vision = vision
        self.movement = movement
        self.objective = objective
        self.paths_built = 0

        self.target_ore = None
        self.core_target = None
        self.curr = None
        self.next = None
        self.just_built = []

    def start_build(self):
        self.target_ore = self.objective.target
        best_len = float("inf")

        for target in self.vision.core_targets:
            if self.target_ore.distance_squared(target) < best_len:
                best_len = self.target_ore.distance_squared(target)
                self.core_target = target

        self.curr = self.random_empty_dir(self.target_ore, self.core_target)
        if not self.curr:
            self.reset()
            return

        self.next = self.calculate_next(self.curr)
        self.just_built = []

    def random_empty_dir(self, pos: Position, target: Position):
        pos_arr = sorted(
            [pos.add(d) for d in CARDINAL_DIRECTIONS],
            key=lambda pos: pos.distance_squared(target),
        )

        for p in pos_arr:
            if (
                self.vision.in_bounds(p)
                and self.vision.mapdata.get(p, -1) == Environment.EMPTY
            ):
                if self.c.is_in_vision(p):
                    bid = self.c.get_tile_building_id(p)
                    if bid is None or self.c.get_team(bid) == self.c.get_team():
                        return p

    def reset(self):
        self.target_ore = None
        self.core_target = None
        self.curr = None
        self.next = None
        self.just_built = []

    def calculate_next(self, pos: Position):
        min_score = float("inf")
        best_pos = None

        for p in self.vision.squares_within_dist(pos, 1):
            if p == pos:
                continue

            mapdata = self.vision.mapdata.get(p, -1)

            if mapdata == Environment.WALL:
                continue

            if self.c.is_in_vision(p):
                bid = self.c.get_tile_building_id(p)
                if bid is not None and self.c.get_team(bid) != self.c.get_team():
                    continue

            if self.just_built and p == self.just_built[-1]:
                continue

            if p.distance_squared(self.core_target) > pos.distance_squared(
                self.core_target
            ):
                continue

            if mapdata in (Environment.ORE_AXIONITE, Environment.ORE_TITANIUM):
                continue

            score = p.distance_squared(self.core_target)
            if score < min_score:
                min_score = score
                best_pos = p

        if best_pos is None:
            for p in self.vision.squares_within_dist(pos, 9):
                if p == pos:
                    continue

                mapdata = self.vision.mapdata.get(p, -1)

                if (
                    self.c.is_in_vision(p)
                    and self.c.get_tile_env(p) == Environment.WALL
                ):
                    continue

                if self.c.is_in_vision(p):
                    bid = self.c.get_tile_building_id(p)
                    if bid is not None and self.c.get_team(bid) != self.c.get_team():
                        continue

                score = p.distance_squared(self.core_target)

                if mapdata in (Environment.ORE_AXIONITE, Environment.ORE_TITANIUM):
                    score += 100

                if score < min_score:
                    min_score = score
                    best_pos = p

        return best_pos

    def place_harvester(self, pos: Position):
        if self.c.get_position().distance_squared(pos) > 2:
            self.movement.move_to(pos)
            if self.c.get_position().distance_squared(pos) > 2:
                return False

        need_travel = False
        for d in CARDINAL_DIRECTIONS:
            if not self.vision.in_bounds(pos.add(d)):
                continue
            if self.c.is_in_vision(pos.add(d)) and self.c.is_tile_empty(pos.add(d)):
                need_travel = True

        if need_travel:
            if self.c.get_position() != pos:
                self.movement.move_to(pos)

            if self.c.get_position() != pos:
                return

            for d in CARDINAL_DIRECTIONS:
                if not self.vision.in_bounds(pos.add(d)):
                    continue
                if self.c.is_tile_empty(pos.add(d)) and self.c.can_build_road(
                    pos.add(d)
                ):
                    self.c.build_road(pos.add(d))
                    break

            return

        if self.c.get_position() == pos:
            self.movement.move_to(self.vision.randomdir(pos))

        if self.c.get_position().distance_squared(pos) not in [1, 2]:
            return False

        if pos not in self.vision.empty_ores:
            return True

        bid = self.c.get_tile_building_id(pos)

        if bid is not None and self.c.get_entity_type(bid) == EntityType.HARVESTER:
            return True

        if bid is not None and self.c.get_team(bid) != self.c.get_team():
            return True

        if self.c.can_build_harvester(pos):
            self.c.build_harvester(pos)
            return True
        elif self.c.can_destroy(pos):
            self.c.destroy(pos)
            if self.c.can_build_harvester(pos):
                self.c.build_harvester(pos)
                return True

        return False

    def _should_abort(self, bid, allowed_types, bid_loc):
        return (
            bid is not None
            and self.c.is_in_vision(bid_loc)
            and self.c.get_team(bid) != self.c.get_team()
        ) or (
            bid is not None
            and self.c.is_in_vision(bid_loc)
            and self.c.get_entity_type(bid) in allowed_types
            and self.c.get_team(bid) == self.c.get_team()
        )

    def _post_build(self, next_types):
        if self.vision.is_core(self.next):
            self.paths_built += 1
            self.reset()
            return True

        nid = self.c.get_tile_building_id(self.next)
        if (
            nid is not None
            and self.c.get_entity_type(nid) in next_types
            and self.c.get_team(nid) == self.c.get_team()
        ):
            self.paths_built += 1
            self.reset()
            return True

        if self.c.get_position().distance_squared(self.curr) == 1:
            self.movement.move_to(self.curr)

        self.curr = self.next
        self.next = self.calculate_next(self.curr)
        return False

    def _try_build(self, can_fn, build_fn, allowed_types, next_types):
        if can_fn():
            build_fn()
            self.just_built.append(self.curr)
            return self._post_build(next_types)

        bid = self.c.get_tile_building_id(self.curr)
        if self._should_abort(bid, allowed_types, self.curr):
            self.reset()
            return True

        if self.c.can_destroy(self.curr):
            self.c.destroy(self.curr)
            if can_fn():
                build_fn()
                self.just_built.append(self.curr)
                return self._post_build(next_types)

        return False

    def build(self):
        if (
            self.target_ore not in self.vision.unconnected_harvesters
            and not self.just_built
        ):
            self.reset()
            return

        cur = self.c.get_position()

        if cur.distance_squared(self.curr) > 2:
            self.movement.move_to(self.curr)
            self.next = self.calculate_next(self.curr)
            if cur.distance_squared(self.curr) > 2:
                return

        if cur == self.curr:
            self.movement.move_to(self.vision.randomdir(self.curr))
            self.next = self.calculate_next(self.curr)

        if self.curr.distance_squared(self.next) == 1:
            self._try_build(
                lambda: self.c.can_build_conveyor(
                    self.curr, self.curr.direction_to(self.next)
                ),
                lambda: self.c.build_conveyor(
                    self.curr, self.curr.direction_to(self.next)
                ),
                [EntityType.CONVEYOR, EntityType.BRIDGE],
                [EntityType.CONVEYOR, EntityType.BRIDGE],
            )
        else:
            self._try_build(
                lambda: self.c.can_build_bridge(self.curr, self.next),
                lambda: self.c.build_bridge(self.curr, self.next),
                [EntityType.CONVEYOR, EntityType.BRIDGE, EntityType.SPLITTER],
                [EntityType.CONVEYOR, EntityType.BRIDGE, EntityType.SPLITTER],
            )
