from cambc import Controller, EntityType, Position, Environment

from mapUtils import cardinalBetween, onTheMap
from buildManager import enoughResources, tryBuildGunner, tryBuildLauncher, tryBuildSentinel
from fireManager import tryFireAtSelf
from destroyManager import tryDestroy
from movementManager import lockMovement
from data import CARDINAL_DIRECTIONS, DIRECTIONS, SOURCE_TYPES, TURRET_TYPES, CONVEYOR_TYPES, DIRECTIONAL_TURRET_TYPES
from unit import Unit
from behaviors.behavior import Behavior

class TurretHunterBehavior(Behavior):
    def findSource(ct: Controller, turretPosition: Position, nearbyBuildings: list[int]):
        targetSource = None

        # Check for adjacent conveyors or harvesters
        for d in CARDINAL_DIRECTIONS:
            sourcePosition = turretPosition.add(d)

            if not onTheMap(ct, sourcePosition):
                continue

            if not ct.is_in_vision(sourcePosition):
                continue

            sourceId = ct.get_tile_building_id(sourcePosition)

            if sourceId is None:
                continue

            sourceType = ct.get_entity_type(sourceId)

            if sourceType not in SOURCE_TYPES:
                continue

            if sourceType == EntityType.SPLITTER:
                # Ignore splitters facing the opposite way
                if d.opposite() == ct.get_direction(sourceId).opposite():
                    continue
            elif sourceType == EntityType.BRIDGE:
                # Ignore bridges not feeding directly to the turret
                if ct.get_bridge_target(sourceId) != turretPosition:
                    continue
            elif sourceType == EntityType.HARVESTER:
                # Harvesters are only invalid if the turret is pointing directly into them
                turretId = ct.get_tile_building_id(turretPosition)
                if turretId is not None and ct.get_entity_type(turretId) in DIRECTIONAL_TURRET_TYPES:
                    if d == ct.get_direction(turretId):
                        continue
            else:
                # Ignore conveyors facing the wrong way
                if d.opposite() != ct.get_direction(sourceId):
                    continue

            targetSource = sourceId
            break

        # Check for bridges
        if targetSource is None:
            for bridgeId in nearbyBuildings:
                if ct.get_entity_type(bridgeId) != EntityType.BRIDGE:
                    continue

                # Ignore bridges not feeding directly to the turret
                if ct.get_bridge_target(bridgeId) != turretPosition:
                    continue
                
                targetSource = bridgeId
                break

        return targetSource

    @staticmethod
    def run(ct: Controller) -> bool:
        targetSource = None
        fallbackPosition = None

        nearbyBuildings = ct.get_nearby_buildings()
        for turretId in nearbyBuildings:
            if ct.get_team(turretId) == ct.get_team():
                continue

            if ct.get_entity_type(turretId) not in DIRECTIONAL_TURRET_TYPES:
                continue

            turretPosition = ct.get_position(turretId)
            fallbackPosition = turretPosition

            targetSource = TurretHunterBehavior.findSource(ct, turretPosition, nearbyBuildings)

            if targetSource is not None:
                break

        if targetSource is None:
            # if fallbackPosition is not None and ct.get_position().distance_squared(targetSource) >= 18:
            #     Unit.astar.moveTo(fallbackPosition)
            return False
        
        targetPosition = ct.get_position(targetSource)
        
        visited = set()

        # If there's someone on that source, try to move upstream
        while ct.get_tile_builder_bot_id(ct.get_position(targetSource)) is not None:
            visited.add(targetSource)

            upstream = TurretHunterBehavior.findSource(ct, ct.get_position(targetSource), nearbyBuildings)

            if upstream in visited:
                break

            if upstream:
                if ct.get_entity_type(upstream) == EntityType.HARVESTER:
                    break
                
                targetSource = upstream
                targetPosition = ct.get_position(upstream)
            else:
                break

        Unit.astar.moveTo(targetPosition)
        
        Unit.indicator += "Hunting turrets\n"

        ct.draw_indicator_line(ct.get_position(), targetPosition, 255, 0, 0)

        if not ct.is_in_vision(targetPosition):
            return False
        
        # If there's a sitter, try to build launchers to throw them off
        if ct.get_team(ct.get_tile_builder_bot_id(targetPosition)) != ct.get_team():
            for d in DIRECTIONS:
                launcherPosition = targetPosition.add(d)
                if onTheMap(ct, launcherPosition) and ct.is_in_vision(launcherPosition):
                    if tryBuildLauncher(ct, launcherPosition):
                        break
            
        if ct.get_team(targetSource) == ct.get_team():
            isHarvester = ct.get_entity_type(ct.get_tile_building_id(targetPosition)) == EntityType.HARVESTER
            if isHarvester and enoughResources(ct.get_global_resources(), ct.get_gunner_cost()):
                turretToMe = turretPosition.direction_to(targetPosition)
                for turretDir in (turretToMe.rotate_left().rotate_left(), turretToMe.rotate_right().rotate_right()):
                    gunnerPosition = targetPosition.add(turretDir)
                    if onTheMap(ct, gunnerPosition) and ct.is_in_vision(gunnerPosition):
                        if ct.get_position() == gunnerPosition:
                            Unit.pathfind.goAway(targetPosition, buildRoads=False)
                        if ct.get_entity_type(ct.get_tile_building_id(gunnerPosition)) in CONVEYOR_TYPES:
                            tryDestroy(ct, gunnerPosition)
                        tryBuildGunner(ct, gunnerPosition, gunnerPosition.direction_to(turretPosition))
            else:
                tryDestroy(ct, targetPosition)

                # If the source is an ally, replace it with a sentinel
                if ct.get_tile_env(targetPosition) == Environment.EMPTY and enoughResources(ct.get_global_resources(), ct.get_gunner_cost()):
                    tryBuildSentinel(ct, targetPosition, targetPosition.direction_to(turretPosition))
        elif ct.get_position() == targetPosition:
            # If the source is an enemy, blow it up to stop the turret
            if tryFireAtSelf(ct):
                lockMovement()
        elif ct.get_entity_type(ct.get_tile_building_id(targetPosition)) == EntityType.HARVESTER:
            if ct.get_position().distance_squared(targetPosition) <= 2:
                Unit.pathfind.goAway(targetPosition)
            dirToMe = cardinalBetween(targetPosition, ct.get_position())
            tryBuildGunner(ct, targetPosition.add(dirToMe), targetPosition.add(dirToMe).direction_to(turretPosition))

        return True