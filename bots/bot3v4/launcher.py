# launcher.py
from cambc import *
from utils.constants import Constants
from utils.building import Building

class Launcher:
    @staticmethod
    def tick(ct: Controller):
        print("Hi!")

        my_team = ct.get_team()
        my_pos = ct.get_position()
        tiles = ct.get_nearby_tiles()

        # Cache buildings by position — no need to pre-walk neighbours
        building_cache = {}
        for tile in tiles:
            building_id = ct.get_tile_building_id(tile)
            if building_id is not None:
                building_cache[tile] = Building(ct, building_id, tile)

        # Find the first nearby enemy builder bot
        nearby_bot = None
        for unit in ct.get_nearby_units(2):
            if ct.get_entity_type(unit) != EntityType.BUILDER_BOT:
                continue
            if ct.get_team(unit) != my_team:
                nearby_bot = ct.get_position(unit)
                break

        print("Oh no! Nearby Enemy Bot:", nearby_bot)

        if nearby_bot is None:
            return

        best_pos = None
        best_score = -999999

        for tile in tiles:
            if not ct.is_tile_passable(tile):
                continue

            score = my_pos.distance_squared(tile)

            building = building_cache.get(tile)
            if building is not None:
                if building.team == my_team and building.entityType in Constants.ROUTING:
                    continue

            for d in Constants.DIRECTIONS:
                new_loc = tile.add(d)
                if not Launcher.on_map(ct, new_loc) or not ct.is_in_vision(new_loc):
                    continue
                adj_building = building_cache.get(new_loc)
                if adj_building is None:
                    continue
                if adj_building.team != my_team and adj_building.entityType == EntityType.LAUNCHER:
                    score -= 50
                elif adj_building.team == my_team and adj_building.entityType in Constants.TRANSPORT_ROUTING:
                    score -= 50

            if score > best_score:
                best_pos = tile
                best_score = score

        print("Plausible place to throw:", best_pos)

        if best_pos is not None and ct.can_launch(nearby_bot, best_pos):
            ct.launch(nearby_bot, best_pos)

    @staticmethod
    def on_map(ct, pos):
        return 0 <= pos.x < ct.get_map_width() and 0 <= pos.y < ct.get_map_height()