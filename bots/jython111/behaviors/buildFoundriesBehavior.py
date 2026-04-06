from cambc import Controller, EntityType, Environment, GameConstants

from data import CARDINAL_DIRECTIONS, CONVEYOR_TYPES, DIRECTIONAL_CONVEYOR_TYPES
from unit import Unit
from mapUtils import getConveyorTarget, onTheMap
from buildManager import tryBuildBridge, tryBuildConveyor, tryBuildSplitter, tryBuildFoundry
from behaviors.behavior import Behavior

class BuildFoundriesBehavior(Behavior):
    @staticmethod
    def run(ct: Controller) -> bool:
        for splitterId in ct.get_nearby_buildings():
            if not ct.is_in_vision(ct.get_position(splitterId)):
                continue

            if ct.get_team(splitterId) != ct.get_team():
                continue

            if ct.get_entity_type(splitterId) not in DIRECTIONAL_CONVEYOR_TYPES:
                continue
            
            splitterPosition = ct.get_position(splitterId)

            inputs = 0
            inputDirection = None

            for d in CARDINAL_DIRECTIONS:
                inputLocation = splitterPosition.add(d)

                if not onTheMap(ct, inputLocation) or not ct.is_in_vision(inputLocation):
                    continue
                
                # Count ores as inputs
                if ct.get_tile_env(inputLocation) in (Environment.ORE_TITANIUM, Environment.ORE_AXIONITE):
                    inputs += 1
                    inputDirection = d.opposite()
                    continue
                
                inputId = ct.get_tile_building_id(inputLocation)

                if inputId is None or ct.get_team(inputId) != ct.get_team():
                    continue

                if ct.get_entity_type(inputId) not in DIRECTIONAL_CONVEYOR_TYPES:
                    continue

                if ct.get_direction(inputId) != d.opposite():
                    continue

                inputs += 1
                inputDirection = d.opposite()

            if inputs != 1:
                continue

            conveyorResource = ct.get_stored_resource(splitterId)
            if conveyorResource is not None:
                targetPosition = getConveyorTarget(ct, splitterId)

                if not onTheMap(ct, targetPosition) or not ct.is_in_vision(targetPosition):
                    continue

                targetId = ct.get_tile_building_id(targetPosition)
                if targetId is not None:
                    # Try to turn the target into a splitter
                    if ct.get_entity_type(targetId) in DIRECTIONAL_CONVEYOR_TYPES:
                        targetResource = ct.get_stored_resource(targetId)
                        # If there are two different types of resources, try to build a foundry
                        if targetResource is not None and targetResource != conveyorResource:
                            # If there's already a splitter
                            if ct.get_entity_type(splitterId) == EntityType.SPLITTER:
                                # Check if there's a conveyor pointing towards the next target so we can build a foundry
                                for d in CARDINAL_DIRECTIONS:
                                    outputPosition = targetPosition.add(d)

                                    # Make sure it's not the same splitter (since it won't be able to go back)
                                    if outputPosition == splitterPosition:
                                        continue
                                    
                                    if not onTheMap(ct, outputPosition) or not ct.is_in_vision(outputPosition):
                                        continue

                                    outputId = ct.get_tile_building_id(outputPosition)
                                    outputTeam = ct.get_team(outputId)
                                    outputType = ct.get_entity_type(outputId)

                                    if outputId is None or (outputTeam == ct.get_team() and outputType in (EntityType.ROAD, EntityType.MARKER)):
                                        closestCorePosition = Unit.corePosition.add(Unit.corePosition.direction_to(ct.get_position()))
                                        if outputPosition.distance_squared(closestCorePosition) <= GameConstants.BRIDGE_TARGET_RADIUS_SQ:
                                            if tryBuildBridge(ct, outputPosition, closestCorePosition):
                                                return
                                        # Try to build a conveyor
                                        if tryBuildConveyor(ct, outputPosition, d.opposite()):
                                            return
                                        else:
                                            continue
                                    
                                    if ct.get_team(outputId) != ct.get_team():
                                        continue
                                    
                                    if ct.get_entity_type(outputId) not in CONVEYOR_TYPES:
                                        continue

                                    # We've found a suitable position to build a foundry!
                                    for d2 in CARDINAL_DIRECTIONS:
                                        foundryPosition = splitterPosition.add(d2)
                                        if not onTheMap(ct, foundryPosition):
                                            continue

                                        if not ct.is_in_vision(foundryPosition):
                                            continue

                                        if foundryPosition.distance_squared(outputPosition) > 1:
                                            continue

                                        foundryCurrentId = ct.get_tile_building_id(foundryPosition)

                                        if foundryCurrentId is None or (ct.get_team(foundryCurrentId) == ct.get_team() and ct.get_entity_type(foundryCurrentId) in (EntityType.ROAD, EntityType.MARKER)):
                                            Unit.astar.moveTo(foundryPosition)

                                            if ct.is_in_vision(foundryPosition):
                                                tryBuildFoundry(ct, foundryPosition)
                                            return
                            # Otherwise, try to build a splitter
                            else:
                                Unit.astar.moveTo(splitterPosition)
                                if ct.is_in_vision(splitterPosition):
                                    tryBuildSplitter(ct, splitterPosition, inputDirection)
                                return