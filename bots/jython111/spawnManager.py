from cambc import Controller, Direction, Environment, Position

from mapUtils import onTheMap

def trySpawn(ct: Controller, position: Position) -> bool:
    if ct.can_spawn(position):
        ct.spawn_builder(position)
        return True
    return False