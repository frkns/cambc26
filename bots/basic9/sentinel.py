from cambc import *
from bots.basic9.robot import Robot
from bots.basic9.utils.constants import CONVEYORS


class Sentinel(Robot):
    def __init__(self, ct, vision):
        super().__init__(ct, vision)
        self.nearby_tiles = self.ct.get_attackable_tiles()

    def run_macro(self):
        pass

    def run_micro(self):
        enemy_sentinels = []
        enemy_builders = []
        enemy_conveyors = []
        enemy_core = None
        other_enemies = []

        for pos in self.nearby_tiles:
            bid = self.ct.get_tile_building_id(pos)
            if bid is None:
                continue

            if self.ct.get_team(bid) == self.ct.get_team():
                continue

            if (
                self.ct.get_tile_builder_bot_id(pos) is not None
                and self.ct.get_team(self.ct.get_tile_builder_bot_id(pos))
                == self.ct.get_team()
            ):
                continue

            entity_type = self.ct.get_entity_type(bid)

            # Categorize by type
            if entity_type == EntityType.SENTINEL:
                enemy_sentinels.append(pos)
            elif entity_type == EntityType.BUILDER_BOT:
                enemy_builders.append(pos)
            elif entity_type in CONVEYORS:
                enemy_conveyors.append(pos)
            elif entity_type == EntityType.CORE:
                enemy_core = pos
            elif entity_type != EntityType.HARVESTER:
                other_enemies.append(pos)

        target = None

        if enemy_sentinels:
            target = enemy_sentinels[0]
        elif enemy_builders:
            target = enemy_builders[0]
        elif enemy_conveyors:
            target = enemy_conveyors[0]
        elif enemy_core:
            target = enemy_core
        elif other_enemies:
            target = other_enemies[0]

        if target and self.ct.can_fire(target):
            self.ct.fire(target)
