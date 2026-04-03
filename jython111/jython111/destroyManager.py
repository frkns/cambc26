from cambc import Controller, Position, EntityType
from data import DEBUG
if DEBUG:
    import traceback
    import sys

def tryDestroy(ct: Controller, position: Position) -> bool:
    buildingId = ct.get_tile_building_id(position)

    # Make sure we don't destroy our own core (or markers)
    if buildingId is not None and ct.get_team(buildingId) == ct.get_team() and ct.get_entity_type(buildingId) in (EntityType.CORE, EntityType.MARKER):
        return False

    if ct.can_destroy(position):
        ct.destroy(position)
        if DEBUG:
            traceback.print_stack(file=sys.stdout)
        return True
    return False