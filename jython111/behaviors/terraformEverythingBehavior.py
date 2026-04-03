from cambc import Controller, EntityType

from data import ALL_DIRECTIONS
from buildManager import tryBuildRoad
from mapUtils import onTheMap
from behaviors.behavior import Behavior

class TerraformEverythingBehavior(Behavior):
    @staticmethod
    def run(ct: Controller) -> None:
        for dir in ALL_DIRECTIONS:
            if onTheMap(ct, ct.get_position().add(dir)):
                buildingId = ct.get_tile_building_id(ct.get_position().add(dir))
                if buildingId is None or ct.get_entity_type(buildingId) == EntityType.MARKER:
                    if tryBuildRoad(ct, ct.get_position().add(dir), False):
                        return