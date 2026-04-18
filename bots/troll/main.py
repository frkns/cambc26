import sys

from cambc import *
import random

DIRECTIONS = [d for d in Direction if d != Direction.CENTRE]

class Player:
    def __init__(self):
        self.unit = None

    def run(self, ct: Controller) -> None:
        if ct.get_entity_type() == EntityType.BUILDER_BOT:
            dir = random.choice(DIRECTIONS)
            if ct.can_move(dir):
                ct.move(dir)
            if ct.can_heal(ct.get_position()):
                ct.heal(ct.get_position())
        elif ct.get_entity_type() == EntityType.CORE:
            if ct.can_spawn(ct.get_position()):
                ct.spawn_builder(ct.get_position())

                
        # for y1 in range(ct.get_map_height()):
        #     for x1 in range(ct.get_map_width()):
        #         for y2 in range(ct.get_map_height()):
        #             for x2 in range(ct.get_map_width()):

        try:
            x1, y1 = (0, 0)
            x2, y2 = (99999999999999999999999999999999999999999999999999999999999999999999, 99999999999999999999999999999999999999999999999999999999999999999999)
            ct.draw_indicator_line(Position(x1, y1), Position(x2, y2), 255, 255, 255)
        except OverflowError:
            pass






