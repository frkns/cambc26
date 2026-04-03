from cambc import Controller, EntityType, Environment, Position, GameConstants

from buildManager import tryBuildBridge
from data import WALKABLE_ENTITIES
from mapUtils import onTheMap, chevyBetween
from unit import Unit
from behaviors.behavior import Behavior

class PlaceBridgeBehavior(Behavior):
    @staticmethod
    def run(ct: Controller, target: Position, endPath: bool = False, _currentPosition: Position = None) -> None:
        Unit.indicator += "Trying to build a bridge...\n"

        moveTarget = None

        # Find where we need to move to
        if _currentPosition is not None:
            moveTarget = _currentPosition
        elif len(Unit.path) == 0:
            moveTarget = Unit.harvesterPosition
        else:
            moveTarget = Unit.path[-1]

        # If we're not close to the target, move towards it
        if ct.get_position().distance_squared(moveTarget) > 1:
            Unit.astar.moveTo(moveTarget)
            # # If we didn't move (maybe the target is blocked off) give up
            # if ct.get_move_cooldown() == 0:
            #     if endPath:
            #         Unit.indicator += "Ending path because can't move to place a bridge\n"
            #         Unit.clearPath()
            #     return
            
        if ct.get_position().distance_squared(moveTarget) <= 1:
            if _currentPosition is not None:
                currentPosition = _currentPosition
            elif len(Unit.path) == 0:
                currentPosition = ct.get_position()
            else:
                currentPosition = Unit.path[-1]
        else:
            # If we aren't close yet, don't do anything and just keep moving
            return
        
        currentBuildingId = ct.get_tile_building_id(currentPosition)

        if currentBuildingId is not None and ct.get_team(currentBuildingId) == ct.get_team() and ct.get_entity_type(currentBuildingId) == EntityType.BRIDGE:
            if endPath:
                Unit.indicator += "Ending path because we connected to another bridge\n"
                Unit.clearPath()

        # Set the initial test position
        nextPosition = currentPosition
        temp = nextPosition

        closestTarget = target.add(chevyBetween(target, nextPosition))

        # Keep trying to move closer to the target
        while True:
            temp = temp.add(temp.direction_to(closestTarget))

            if not onTheMap(ct, temp) or not ct.is_in_vision(temp):
                break

            if currentPosition.distance_squared(temp) > GameConstants.BRIDGE_TARGET_RADIUS_SQ:
                break

            ct.draw_indicator_dot(temp, 0, 255, 0)

            if temp == closestTarget:
                break

            if ct.get_tile_env(temp) not in [Environment.EMPTY, Environment.ORE_TITANIUM]:
                continue

            buildingId = ct.get_tile_building_id(temp)

            if buildingId != None and (ct.get_team(buildingId) != ct.get_team() or ct.get_entity_type(buildingId) not in WALKABLE_ENTITIES):
                continue

            nextPosition = temp
            
        # If we can't find anywhere to go, give up
        if nextPosition == currentPosition:
            if endPath:
                Unit.indicator += "Ending path because we can't find anywhere to bridge\n"
                Unit.clearPath()
            return

        # Try to build the bridge
        if tryBuildBridge(ct, currentPosition, nextPosition):
            # Track the new bridge we just built
            Unit.path.append(nextPosition)
            Unit.pathSet.add(nextPosition)
            # If we hit the target, finish
            if nextPosition == closestTarget:
                if endPath:
                    Unit.indicator += "Ending path because we hit the target\n"
                    Unit.clearPath()
                return