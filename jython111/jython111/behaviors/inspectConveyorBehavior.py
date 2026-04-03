from cambc import Controller, Environment, EntityType

from behaviors.behavior import Behavior
from unit import Unit

class InspectConveyorBehavior(Behavior):
    @staticmethod
    def run(ct: Controller) -> None:
        if Unit.connecting:
            return
        
        for tile in ct.get_nearby_tiles():
            if not ct.is_in_vision(tile):
                continue
            if ct.get_tile_env(tile) in (Environment.ORE_TITANIUM, Environment.ORE_AXIONITE):
                buildingId = ct.get_tile_building_id(tile)
                if buildingId != None and ct.get_team(buildingId) == ct.get_team() and ct.get_entity_type(buildingId) == EntityType.HARVESTER:
                    Unit.astar.moveTo(tile)
                    if ct.get_position().distance_squared(tile) == 1:
                        Unit.startPath(tile, inspecting=True)
                        return

        if Unit.symmetry.alliedHarvesters:        
            Unit.startPath(list(Unit.symmetry.alliedHarvesters)[((ct.get_current_round() // 100) + ct.get_id()) % len(Unit.symmetry.alliedHarvesters)], inspecting=True)