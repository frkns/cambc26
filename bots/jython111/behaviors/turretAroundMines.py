from cambc import Controller, Environment, Direction, EntityType

from movementManager import lockMovement
from destroyManager import tryDestroy
from data import DIRECTIONS, CARDINAL_DIRECTIONS, DIRECTIONAL_TURRET_TYPES
from unit import Unit
from buildManager import enoughResources, tryBuildSentinel
from fireManager import tryFireAtSelf
from mapUtils import cardinalBetween, filterEnvironment, onTheMap, sortPositions
from behaviors.behavior import Behavior

class TurretAroundMines(Behavior):
    @staticmethod
    def run(ct: Controller) -> bool:
        if not enoughResources(ct.get_global_resources(), ct.get_sentinel_cost()):
            return

        directionDensities = [0] * 8

        for enemyId in ct.get_nearby_entities():
            if ct.get_team(enemyId) == ct.get_team():
                continue

            if ct.get_position(enemyId) == ct.get_position():
                continue

            enemyDirection = ct.get_position().direction_to(ct.get_position(enemyId))
            directionIndex = DIRECTIONS.index(enemyDirection)

            enemyType = ct.get_entity_type(enemyId)

            if enemyType in DIRECTIONAL_TURRET_TYPES:
                directionDensities[directionIndex] += 50
            elif enemyType == EntityType.CORE:
                directionDensities[directionIndex] += 20
            else:
                directionDensities[directionIndex] += 1

        denseDirection: Direction = None
        bestDensity = 0

        for d in range(8):
            if directionDensities[d] > bestDensity:
                bestDensity = directionDensities[d]
                denseDirection = DIRECTIONS[d]

        for tile in sortPositions(ct.get_position(), filterEnvironment(ct, Environment.ORE_TITANIUM, ct.get_nearby_tiles())):
            if ct.get_entity_type(ct.get_tile_building_id(tile)) != EntityType.HARVESTER:
                continue

            ct.draw_indicator_dot(tile, 128, 255, 0)
            
            builtTurret = False
            
            for direction in CARDINAL_DIRECTIONS:
                # Turrets can't intake from the front
                if direction == denseDirection.opposite():
                    continue

                turretPosition = tile.add(direction)
                if not onTheMap(ct, turretPosition) or not ct.is_in_vision(turretPosition):
                    continue

                if not builtTurret:
                    buildingId = ct.get_tile_building_id(turretPosition)
                    if buildingId is not None:
                        if ct.get_team(buildingId) == ct.get_team():
                            if ct.get_entity_type(buildingId) in (EntityType.ROAD, EntityType.MARKER):
                                tryDestroy(ct, turretPosition)
                            else:
                                continue
                        elif ct.get_position() == turretPosition:
                            if tryFireAtSelf(ct):
                                lockMovement()
                    else:
                        if ct.get_position() == turretPosition:
                            Unit.pathfind.goAway(turretPosition)
                    if tryBuildSentinel(ct, turretPosition, denseDirection):
                        builtTurret = True

            Unit.astar.moveTo(tile)

            # Only run the first valid ore
            break