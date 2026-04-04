from cambc import Controller, EntityType, Environment

from behaviors.behavior import Behavior
from mapUtils import sortPositions
from unit import Unit

def _oreScore(ct: Controller, pos):
    """Lower score = higher priority. Prefer the resource type we have less of."""
    dist = ct.get_position().distance_squared(pos)
    return dist

class GoTowardsOreBehavior(Behavior):
    @staticmethod
    def run(ct: Controller) -> None:
        # Collect visible open ores and sort by score (distance + resource priority)
        nearbyOres = []
        for tile in ct.get_nearby_tiles():
            buildingId = ct.get_tile_building_id(tile)
            if (buildingId == None or (ct.get_team(buildingId) == ct.get_team() and ct.get_entity_type(buildingId) == EntityType.BARRIER)) and ct.get_tile_env(tile) == Environment.ORE_TITANIUM:
                if ct.get_position().distance_squared(tile) > 1:
                    nearbyOres.append(tile)

        if nearbyOres:
            bestOre = min(nearbyOres, key=lambda t: _oreScore(ct, t))
            Unit.astar.moveTo(bestOre)
            return

        for ore in sortPositions(ct.get_position(), Unit.symmetry.getOpenTitaniumOrePositions(ct)):
            if ct.get_position().distance_squared(ore) > 1:
                Unit.astar.moveTo(ore)
                return