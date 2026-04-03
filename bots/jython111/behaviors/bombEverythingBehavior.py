from cambc import Controller, EntityType

from fireManager import tryFireAtSelf
from behaviors.behavior import Behavior

class BombEverythingBehavior(Behavior):
    @staticmethod
    def run(ct: Controller) -> bool:
        buildingId = ct.get_tile_building_id(ct.get_position())
        if buildingId is not None and ct.get_team(buildingId) != ct.get_team():
            return tryFireAtSelf(ct)