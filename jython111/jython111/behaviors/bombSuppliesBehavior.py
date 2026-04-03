from cambc import Controller, GameError

from unit import Unit
from data import CONVEYOR_TYPES
from fireManager import tryFireAtSelf
from movementManager import lockMovement
from mapUtils import sortIds
from behaviors.behavior import Behavior

class BombSuppliesBehavior(Behavior):
    @staticmethod
    def run(ct: Controller) -> bool:
        for buildingId in sortIds(ct, ct.get_position(), ct.get_nearby_buildings()):
            try:
                if ct.get_team(buildingId) == ct.get_team():
                    continue
            except GameError:
                continue

            if ct.get_entity_type(buildingId) not in CONVEYOR_TYPES:
                continue

            # if ct.get_stored_resource(buildingId) is None:
            #     continue

            buildingPosition = ct.get_position(buildingId)

            if ct.get_tile_builder_bot_id(buildingPosition) is not None:
                continue

            if ct.get_position() == buildingPosition:
                if tryFireAtSelf(ct):
                    lockMovement()
                    return True

            Unit.astar.moveTo(buildingPosition)

            if ct.get_move_cooldown() > 0:
                return True

        return False