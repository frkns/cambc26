from bots.basic9.robot import Robot
from bots.basic9.utils.goal import Goal
import random


class BuilderBot(Robot):
    def __init__(
        self,
        ct,
        vision=None,
        movement=None,
        objective=None,
        build=None,
        attack=None,
        defense=None,
    ):
        super().__init__(ct, vision, movement, objective, build, attack, defense)
        self.spawn_time = ct.get_current_round()

        self.objective.set_goal(Goal.EXPLORE, self.vision.get_random_nearby_tile(self.vision.core_loc))

    def building_macro(self):
        if self.objective.goal == Goal.EXPLORE and self.vision.unconnected_harvesters:
            self.objective.set_goal(
                Goal.BUILD,
                min(
                    self.vision.unconnected_harvesters,
                    key=lambda pos: self.ct.get_position().distance_squared(pos),
                ),
            )
            self.build.start_build()
            if not self.build.curr:
                self.vision.unconnected_harvesters.remove(self.objective.target)
                self.objective.set_goal(
                    Goal.EXPLORE, self.movement.get_explore_target()
                )

        if self.objective.goal == Goal.EXPLORE and self.vision.empty_ores:
            target = min(
                self.vision.empty_ores,
                key=lambda pos: self.vision.core_loc.distance_squared(pos),
            )
            if self.ct.get_harvester_cost()[0] < self.ct.get_global_resources()[0]:
                self.objective.set_goal(Goal.PLACE_HARVESTERS, target)
            else:
                self.objective.set_goal(Goal.EXPLORE, target)

        if self.objective.goal == Goal.PLACE_HARVESTERS:
            if (
                not self.vision.empty_ores
            ):
                self.objective.set_goal(
                    Goal.EXPLORE, self.movement.get_explore_target()
                )
            else:
                self.objective.target = min(
                    self.vision.empty_ores,
                    key=lambda pos: self.ct.get_position().distance_squared(pos),
                )
                
        return self.objective.goal != Goal.EXPLORE

    def run_macro(self):
        # exit conditions
        if self.objective.goal == Goal.BUILD and not self.build.curr:
            self.objective.set_goal(Goal.EXPLORE, self.movement.get_explore_target())

        if self.spawn_time % 2 == 0:
            print("im a builder_defender lol")
            # Check if we can afford a harvester plus 100 titanium
            self.building_macro()
            if self.vision.sentinel_defense_placements:
                self.objective.set_goal(
                    Goal.PLACE_SENTINEL,
                    min(
                        list(self.vision.sentinel_defense_placements),
                        key=lambda x: x.distance_squared(self.ct.get_position()),
                    ),
                )
            elif self.vision.change_orientation:
                self.objective.set_goal(
                    Goal.CHANGE_CONVEYOR_ORIENTATION,
                    next(iter(self.vision.change_orientation)),
                )
            elif self.vision.needs_defend:
                self.objective.set_goal(
                    Goal.DEFEND, self.defense.get_best_defense_target()
                )
            if self.objective.goal == Goal.EXPLORE:
                if self.vision.friendly_harvesters:
                    patrol_target = self.vision.patrol_harvester or self.vision.core_loc
                    current_pos = self.ct.get_position()
                    if current_pos == self.vision.core_loc:
                        if random.random() < 0.3:
                            self.objective.set_goal(
                                Goal.EXPLORE,
                                self.vision.get_random_nearby_tile(self.vision.core_loc),
                            )
                        else:
                            self.objective.set_goal(Goal.EXPLORE, patrol_target)
                    elif current_pos.distance_squared(self.objective.target) <= 2:
                        self.objective.set_goal(Goal.EXPLORE, self.vision.core_loc)
                else:
                    if self.ct.get_position().distance_squared(self.objective.target) <= 2:
                        self.objective.set_goal(
                            Goal.EXPLORE,
                            self.vision.get_random_nearby_tile(self.vision.core_loc),
                        )
                    elif self.objective.goal != Goal.EXPLORE:
                        self.objective.set_goal(
                            Goal.EXPLORE,
                            self.vision.get_random_nearby_tile(self.vision.core_loc),
                        )

        else:
            if (
                self.objective.goal == Goal.EXPLORE
                and self.objective.target is not None
                and self.ct.get_position().distance_squared(self.objective.target) <= 4
            ):
                self.objective.set_goal(
                    Goal.EXPLORE, self.movement.get_explore_target()
                )
            print("im an attacker lol")
            if self.vision.sentinel_placements:
                self.objective.set_goal(
                    Goal.PLACE_SENTINEL,
                    min(
                        list(self.vision.sentinel_placements),
                        key=lambda x: x.distance_squared(self.ct.get_position()),
                    ),
                )
            elif self.vision.priority_attack:
                self.objective.set_goal(Goal.ATTACK, None)
            elif self.vision.enemy_core_loc is None:
                if self.objective.goal != Goal.EXPLORE or (
                    self.objective.goal == Goal.EXPLORE
                    and self.objective.target not in self.vision.potential_enemy_core
                ):
                    self.objective.set_goal(
                        Goal.EXPLORE, random.choice(self.vision.potential_enemy_core)
                    )
            elif self.objective.goal == Goal.EXPLORE and (
                self.objective.target.distance_squared(self.vision.enemy_core_loc) > 100
                or self.ct.get_position().distance_squared(self.objective.target) <= 5
            ):
                self.objective.set_goal(
                    Goal.EXPLORE,
                    self.vision.get_random_nearby_tile(self.vision.enemy_core_loc),
                )

    def run_micro(self):
        print(f"GOAL: {self.objective.goal}")
        print(f"GOAL_LOC: {self.objective.target}")
        print(f"SYMMETRY: {self.vision.symmetry}")
        print(f"ENEMY_CORE_LOC: {self.vision.enemy_core_loc}")
        match self.objective.goal:
            case Goal.EXPLORE:
                self.movement.move_to(self.objective.target)
            case Goal.BUILD:
                self.build.build()
            case Goal.PLACE_HARVESTERS:
                if self.build.place_harvester(self.objective.target):
                    self.objective.set_goal(
                        Goal.EXPLORE, self.movement.get_explore_target()
                    )
            case Goal.ATTACK:
                if self.attack.attack():
                    self.objective.set_goal(
                        Goal.EXPLORE, self.movement.get_explore_target()
                    )
            case Goal.DEFEND:
                if self.defense.defend():
                    self.objective.set_goal(
                        Goal.EXPLORE, self.movement.get_explore_target()
                    )
            case Goal.PLACE_SENTINEL:
                if self.attack.place_sentinel(self.objective.target):
                    self.objective.set_goal(
                        Goal.EXPLORE, self.movement.get_explore_target()
                    )
            case Goal.CHANGE_CONVEYOR_ORIENTATION:
                if self.defense.change_conveyor_orientation():
                    self.objective.set_goal(
                        Goal.EXPLORE, self.movement.get_explore_target()
                    )

        if self.ct.can_heal(self.ct.get_position()):
            self.ct.heal(self.ct.get_position())

        if self.objective.target is not None:
            self.ct.draw_indicator_line(
                self.ct.get_position(), self.objective.target, 255, 255, 255
            )

        for i in self.vision.sentinel_defense_placements:
            self.ct.draw_indicator_dot(i, 255, 0, 0)