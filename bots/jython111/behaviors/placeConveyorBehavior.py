from cambc import Controller, EntityType, Environment, Position, GameConstants

from behaviors.placeBridgeBehavior import PlaceBridgeBehavior
from fireManager import tryFireAtSelf
from destroyManager import tryDestroy
from buildManager import enoughResources, tryBuildBridge, tryBuildConveyor, tryBuildSentinel
from movementManager import tryMove
from math import sqrt
from mapUtils import findCardinalBetween, isPassableDirectionFrom, onTheMap, getConveyorTarget, cardinalBetween
from unit import Unit
from behaviors.behavior import Behavior
from data import CONVEYOR_TYPES, CARDINAL_DIRECTIONS, INF, TURRET_TYPES, DIRECTIONAL_CONVEYOR_TYPES, ENEMY_WALKABLE_ENTITIES

class PlaceConveyorBehavior(Behavior):
    @staticmethod
    def run(ct: Controller, target: Position) -> None:
        if not Unit.startedConnection and ct.get_position().distance_squared(Unit.harvesterPosition) < 2:
            Unit.startedConnection = True
        
        if len(Unit.path) > 0:
            currentPosition = Unit.path[-1]
            if (ct.get_position().distance_squared(currentPosition) > 1):
                Unit.astar.moveTo(currentPosition)
                if (ct.get_position().distance_squared(currentPosition) > 2):
                    return
        else:
            currentPosition = ct.get_position()

        currentId = ct.get_tile_building_id(currentPosition)
        if ct.get_entity_type(currentId) == EntityType.BRIDGE and ct.get_team(currentId) == ct.get_team() and currentPosition not in Unit.pathSet:
            Unit.clearPath()
            Unit.indicator += "Ending path because there's already a bridge\n"
            return
        elif currentId != None and ct.get_entity_type(currentId) in DIRECTIONAL_CONVEYOR_TYPES and ct.get_team(currentId) == ct.get_team() and Unit.startedConnection:
            currentDir = ct.get_direction(currentId)
        elif len(Unit.path) > 0 and ct.is_in_vision(Unit.path[-1]):
            currentDir = findCardinalBetween(ct, Unit.path[-1], target)
            currentPosition = currentPosition.add(currentDir.opposite())
        else:
            if not ct.is_in_vision(Unit.harvesterPosition):
                Unit.indicator += "Going towards harvester position\n"

                Unit.astar.moveTo(Unit.harvesterPosition)

                ct.draw_indicator_line(ct.get_position(), Unit.harvesterPosition, 0, 255, 0)
                return
            
            currentDir = findCardinalBetween(ct, Unit.harvesterPosition, target)
            currentPosition = Unit.harvesterPosition
            
            # If there's already an allied conveyor going somewhere, just follow it
            for d in CARDINAL_DIRECTIONS:
                checkPos = Unit.harvesterPosition.add(d)
                if not onTheMap(ct, checkPos):
                    continue

                if not ct.is_in_vision(checkPos):
                    continue

                checkId = ct.get_tile_building_id(checkPos)

                if checkId is None:
                    continue

                if ct.get_team(checkId) != ct.get_team():
                    continue

                if ct.get_entity_type(checkId) not in CONVEYOR_TYPES:
                    continue
                
                currentDir = d

            if (ct.get_position() != currentPosition.add(currentDir)):
                Unit.astar.moveTo(currentPosition.add(currentDir))

                # If we moved around wait
                if not ct.is_in_vision(currentPosition):
                    return

            currentId = ct.get_tile_building_id(currentPosition)

        if not onTheMap(ct, currentPosition.add(currentDir)):
            currentDir = findCardinalBetween(ct, currentPosition, target)
            Unit.indicator += "Current conveyor is leading off the map - overriding with direction towards spawn\n"

        nextPosition = currentPosition.add(currentDir)

        closestTargetPosition = target.add(target.direction_to(currentPosition))

        # # If we're close, bridge over to save
        # if ct.is_in_vision(closestTargetPosition) and nextPosition.distance_squared(closestTargetPosition) <= GameConstants.BRIDGE_TARGET_RADIUS_SQ:
        #     if tryBuildBridge(ct, nextPosition, closestTargetPosition):
        #         Unit.clearPath()
        #         Unit.indicator += "Ending path because we just made a bridge\n"
        #         return

        if not ct.is_in_vision(nextPosition):
            nextId = None
            Unit.astar.moveTo(nextPosition)
            return
        elif len(Unit.path) > 0:
            # End early if we're linking to an already-built pathway
            nextId = ct.get_tile_building_id(nextPosition)
            if nextId != None and ct.get_entity_type(nextId) in CONVEYOR_TYPES and ct.get_team(nextId) == ct.get_team() and nextPosition not in Unit.pathSet:
                tryMove(ct, currentDir)
                if (not Unit.inspecting):
                    Unit.clearPath()
                    Unit.indicator += "Ending path because we're linking to another path\n"
                return
            
        if ct.get_position().distance_squared(nextPosition) >= 2:
            Unit.pathfind.goTowards(nextPosition)

        # Check if there's already an allied conveyor
        nextCurrentDir = None
        nextCurrentId = ct.get_tile_building_id(nextPosition)
        if nextCurrentId is not None and ct.get_team(nextCurrentId) == ct.get_team() and ct.get_entity_type(nextCurrentId) in DIRECTIONAL_CONVEYOR_TYPES:
            nextCurrentDir = ct.get_direction(nextCurrentId)
            # If there's already a conveyor before we've started, we're just inspecting it
            if len(Unit.path) == 0:
                Unit.inspecting = True

        currentDirBlocked = False

        nextDir = None
        closestDistance = INF
        for dir in CARDINAL_DIRECTIONS:
            candidatePos = nextPosition.add(dir)

            if not onTheMap(ct, candidatePos):
                continue

            if not isPassableDirectionFrom(ct, dir, nextPosition):
                # Don't go around enemy builder bots when we're inspecting
                if ct.is_in_vision(candidatePos) and (ct.get_tile_builder_bot_id(candidatePos) is None or not Unit.inspecting):
                    if dir == currentDir:
                        currentDirBlocked = True
                    continue

            distance = sqrt(candidatePos.distance_squared(target))

            # Give a large penalty for doubling back
            if dir == currentDir.opposite():
                distance += 500

            # Give a large penalty if we've already visited the location in our path
            if candidatePos in Unit.pathSet:
                ct.draw_indicator_dot(nextPosition, 255, 0, 255)
                distance += 10

            if ct.is_in_vision(candidatePos):
                buildingId = ct.get_tile_building_id(candidatePos)
                if ct.get_team(buildingId) == ct.get_team():
                    buildingType = ct.get_entity_type(buildingId)
                    # Handling allied conveyors
                    if buildingType in (EntityType.CONVEYOR, EntityType.ARMOURED_CONVEYOR):
                        # Give lots and lots of penalty if we'd run straight against another conveyor
                        if ct.get_direction(buildingId) == dir.opposite():
                            distance += 500
                        # Also give penalty if we're going against a conveyor that's probably jammed
                        if ct.get_stored_resource(buildingId) is not None and not Unit.inspecting:
                            nextTargetPosition = getConveyorTarget(ct, buildingId)
                            ct.draw_indicator_dot(nextTargetPosition, 255, 0, 31)
                            if nextTargetPosition is not None and ct.is_in_vision(nextTargetPosition):
                                nextTargetId = ct.get_tile_building_id(nextTargetPosition)
                                if nextTargetId is not None and ct.get_entity_type(nextTargetId) in (EntityType.CONVEYOR, EntityType.ARMOURED_CONVEYOR):
                                    distance += 250
                    elif buildingType == EntityType.SPLITTER:
                        # Also give penalty for going against a splitter
                        if ct.get_direction(buildingId) != dir:
                            distance += 500
                    # Give penalty for going over a turret
                    elif buildingType in TURRET_TYPES:
                        distance += 250
                elif buildingId is not None:
                    if len(Unit.path) == 0:
                        # Give penalty if there's an enemy building and we're just starting
                        distance += 5

            # Give a bonus for moving in the same direction
            if dir == currentDir and nextPosition.distance_squared(target) > 8:
                distance -= 1

            # Give a bonus for keeping the same direction that already exists
            if dir == nextCurrentDir and Unit.inspecting:
                distance -= 1

            if distance < closestDistance:
                nextDir = dir
                closestDistance = distance

            ct.draw_indicator_line(nextPosition, nextPosition.add(dir), 0, 0, 255)

        if nextDir is not None:
            ct.draw_indicator_line(nextPosition, nextPosition.add(nextDir), 0, 255, 0)

        if nextDir is None:                
            PlaceBridgeBehavior.run(ct, target, _currentPosition = nextPosition)
            return

        if currentDirBlocked:
            adjacent = nextPosition.add(nextDir).add(currentDir)
            if (nextDir == cardinalBetween(nextPosition, target).opposite()) or (onTheMap(ct, adjacent) and ct.is_in_vision(adjacent) and ct.get_tile_env(adjacent) != Environment.EMPTY):
                PlaceBridgeBehavior.run(ct, target, _currentPosition = nextPosition)
                if not enoughResources(ct.get_global_resources(), ct.get_bridge_cost()):
                    return
        
        Unit.indicator += "Trying to build a conveyor...\n"

        if tryBuildConveyor(ct, nextPosition, nextDir):
            Unit.path.append(nextPosition)
            Unit.pathSet.add(nextPosition)

        # If we see another allied builder bot and we're just inspecting, assume they've got it covered
        if Unit.inspecting:
            nextUnitId = ct.get_tile_builder_bot_id(nextPosition)

            if nextUnitId != ct.get_id() and nextUnitId is not None and ct.get_team(nextUnitId) == ct.get_team():
                Unit.clearPath()
                Unit.indicator += "Ending path because another ally is inspecting\n"
                return

        nextId = ct.get_tile_building_id(nextPosition)

        if nextId != None and ct.get_entity_type(nextId) != EntityType.MARKER:
            # Check if the building is an ally
            if ct.get_team(nextId) == ct.get_team():
                # Check if we successfully conveyored
                if ct.get_entity_type(nextId) in CONVEYOR_TYPES:
                    tryMove(ct, currentDir)
                # If we just used a sentinel to blast obstacles away
                elif ct.get_entity_type(nextId) == EntityType.SENTINEL:
                    # Make sure the sentinel is inactive (the current tile is loaded)
                    if (ct.get_entity_type(currentId) in CONVEYOR_TYPES and ct.get_stored_resource(currentId) is not None) or ct.get_entity_type(currentId) in (EntityType.ROAD, EntityType.MARKER):
                        # Make sure the path is clear
                        if ct.get_team(ct.get_tile_building_id(nextPosition.add(nextDir))) == ct.get_team():
                            Unit.indicator += "Sentinel is no longer needed"
                            tryDestroy(ct, nextPosition)
                        # If it's not clear
                        else:
                            # Try to bridge out
                            PlaceBridgeBehavior.run(ct, target, endPath=True)
            else: #if len(Unit.path) > 0
                # If the obstacle is something we can go on, try to destroy it
                if ct.get_entity_type(nextId) in ENEMY_WALKABLE_ENTITIES:
                    Unit.indicator += "Trying to fire at the obstacle in the way\n"
                    Unit.astar.moveTo(nextPosition)
                    if ct.get_position() == nextPosition:
                        tryFireAtSelf(ct)
                else:
                    # If there's an obstacle in the way, try to bridge through
                    PlaceBridgeBehavior.run(ct, target)
                                
                    # Drill through obstacles by spamming Sentinels
                    # If it's an enemy in the way, blast them away with a sentinel (funded by the conveyor behind us)
                    if ct.get_action_cooldown() == 0 and enoughResources(ct.get_global_resources(), ct.get_sentinel_cost()):
                        if ct.get_position().distance_squared(currentPosition) <= 8:
                            Unit.indicator += "Trying to blast the obstacle away"

                            # Try building just in case
                            tryBuildSentinel(ct, currentPosition, currentDir)

                            # Move back
                            for dir in CARDINAL_DIRECTIONS:
                                movePos = ct.get_position().add(dir)
                                if not onTheMap(ct, movePos):
                                    continue
                                if ct.get_entity_type(ct.get_tile_building_id(movePos)) in (EntityType.CONVEYOR, EntityType.ARMOURED_CONVEYOR):
                                    Unit.pathfind.goTowards(movePos)
                                    break
                            else:
                                # If we can't find anywhere to move and we're right next to the harvester, try to flank to a better position
                                if len(Unit.path) < 1:
                                    Unit.pathfind.goTowards(Unit.harvesterPosition)
                                    # If we still don't move, just give up
                                    if ct.get_move_cooldown() == 0:
                                        Unit.indicator += "Ending path because we can't start"
                                        Unit.clearPath()
                                        return

                            # Build where we just were
                            if tryDestroy(ct, currentPosition) and len(Unit.path) > 0:
                                Unit.pathSet.discard(Unit.path[-1])
                                Unit.path.pop(-1)
                            tryBuildSentinel(ct, currentPosition, currentDir)