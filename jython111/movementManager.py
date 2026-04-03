from cambc import Controller, Direction, EntityType
import traceback
import sys

from destroyManager import tryDestroy
from buildManager import tryBuildRoad, onTheMap
from data import DEBUG

import mapUtils

_locked = False

def unlockMovement():
    global _locked
    _locked = False

def lockMovement():
    global _locked
    _locked = True

def movementIsLocked():
    global _locked
    return _locked

def tryMove(ct: Controller, direction: Direction, buildRoads: bool = True) -> bool:
    global _locked
    if _locked:
        return False
    
    if direction == Direction.CENTRE:
        if DEBUG:
            print("WARNING: tried to move to the center direction!!!")
            traceback.print_stack(file=sys.stdout)
        return False
    if ct.can_move(direction):
        ct.move(direction)
        return True
    elif buildRoads:
        nextPos = ct.get_position().add(direction)
        if onTheMap(ct, nextPos):
            if ct.get_entity_type(ct.get_tile_building_id(nextPos)) == EntityType.BARRIER and mapUtils._breakBarriers:
                tryDestroy(ct, nextPos)
            ct.draw_indicator_dot(nextPos, 255, 255, 200)
            if tryBuildRoad(ct, nextPos):
                if ct.can_move(direction):
                    ct.move(direction)
                    return True
    return False