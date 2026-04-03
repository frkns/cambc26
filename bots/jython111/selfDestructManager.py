from cambc import Controller, EntityType

from unit import Unit

def trySelfDestruct(ct: Controller) -> bool:
    # Make sure we don't blow up our own core
    if ct.get_team(ct.get_tile_building_id(ct.get_position())) == ct.get_team() and ct.get_entity_type(ct.get_tile_building_id(ct.get_position())) == EntityType.CORE:
        return False
    
    ct.self_destruct()
    Unit.alive = False
    return True