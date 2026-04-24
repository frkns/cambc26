"""Defend bot - spawns builders that heal and don't move
"""

import random

from cambc import Controller, Direction, EntityType, Environment, Position, GameConstants

# non-centre directions
DIRECTIONS = [d for d in Direction if d != Direction.CENTRE]

class Player:
    def run(self, ct: Controller) -> None:
        etype = ct.get_entity_type()
        if etype == EntityType.CORE:
            if (ct.get_hp() < ct.get_max_hp() or len(ct.get_nearby_units()) > 1) and ct.get_scale_percent() < (200):
                for d in Direction:
                    spawn_pos = ct.get_position().add(d)
                    if ct.can_spawn(spawn_pos):
                        ct.spawn_builder(spawn_pos)
        elif etype == EntityType.BUILDER_BOT:
            if ct.can_heal(ct.get_position()):
                ct.heal(ct.get_position())
            for d in Direction:
                heal_pos = ct.get_position().add(d)
                if ct.can_heal(heal_pos):
                    ct.heal(heal_pos)
