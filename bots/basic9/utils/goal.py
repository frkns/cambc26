from cambc import *
from enum import Enum


class Goal(Enum):
    EXPLORE = "explore"
    PLACE_HARVESTERS = "place_harvesters"
    BUILD = "build"
    ATTACK = "attack"
    DEFEND = "defend"
    PLACE_SENTINEL = "place_sentinel"
    CHANGE_CONVEYOR_ORIENTATION = "change_conveyor_orientation"


class Objective:
    def __init__(self, movement):
        self.movement = movement
        self.goal = Goal.EXPLORE
        self.target = movement.get_explore_target()

    def set_goal(self, goal: Goal, target: Position):
        self.goal = goal
        self.target = target
