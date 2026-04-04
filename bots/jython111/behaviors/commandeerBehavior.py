from cambc import Controller, Position, EntityType, GameConstants

from fireManager import tryFireAtSelf
from destroyManager import tryDestroy
from buildManager import tryBuildGunner, tryBuildSentinel
from data import CARDINAL_DIRECTIONS
from unit import Unit
from mapUtils import getConveyorTarget, onTheMap
from behaviors.behavior import Behavior

class CommandeerBehavior(Behavior):
    @staticmethod
    def run(ct: Controller) -> None:
        target = None
        
        for conveyorId in [ct.get_tile_building_id(ct.get_position())] + ct.get_nearby_buildings():
            if conveyorId is None:
                continue
            
            # TODO: This will make it hard for us to build our own turrets towards the core
            if ct.get_team(conveyorId) == ct.get_team():
                continue

            conveyorTarget: Position = getConveyorTarget(ct, conveyorId)

            if conveyorTarget is not None:
                target = conveyorTarget

                # If it leads straight to the core, this is the right one
                if ct.is_in_vision(conveyorTarget):
                    targetId = ct.get_tile_building_id(conveyorTarget)
                    if ct.get_team(targetId) != ct.get_team() and ct.get_entity_type(targetId) == EntityType.CORE:
                        target = ct.get_position(conveyorId)
                        
                break

        if target is not None:
            ct.draw_indicator_line(ct.get_position(), target, 0, 255, 255)

            if (ct.is_in_vision(target)):
                Unit.indicator += f"Trying to take over at {target}\n"

                corePosition = None
                for enemyId in ct.get_nearby_buildings():
                    if ct.get_team(enemyId) == ct.get_team():
                        continue

                    if ct.get_entity_type(enemyId) != EntityType.CORE:
                        continue

                    corePosition = ct.get_position(enemyId)
                    break

                if corePosition is not None:
                    corePosition = corePosition.add(corePosition.direction_to(target))

                    direction = target.direction_to(corePosition)
                
                    # Find the enemy core
                    if target.distance_squared(corePosition) <= GameConstants.SENTINEL_VISION_RADIUS_SQ:
                        targetId = ct.get_tile_building_id(target)
                        if targetId is not None:
                            if ct.get_team(targetId) == ct.get_team():
                                tryDestroy(ct, target)
                            else: 
                                Unit.astar.moveTo(target)
                                if ct.get_position() == target:
                                    tryFireAtSelf(ct)
                                elif not ct.is_in_vision(target):
                                    return

                        if target.distance_squared(corePosition) <= 13: # Gunner action range
                            tryBuildGunner(ct, target, direction)
                        else:
                            tryBuildSentinel(ct, target, direction)


            Unit.astar.moveTo(target)