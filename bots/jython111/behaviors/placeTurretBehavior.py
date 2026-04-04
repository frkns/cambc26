from cambc import Controller, Direction, EntityType, Environment

from unit import Unit
from data import ALL_DIRECTIONS, CARDINAL_DIRECTIONS, CONVEYOR_TYPES, TURRET_TYPES
from buildManager import tryBuildSentinel, tryBuildGunner, tryBuildSplitter, enoughResources
from mapUtils import onTheMap
from behaviors.behavior import Behavior

class PlaceTurretBehavior(Behavior):
    @staticmethod
    def run(ct: Controller, direction: Direction) -> None:
        Unit.indicator += f"Trying to place a turret facing {direction.value}\n"

        buildingId = ct.get_tile_building_id(ct.get_position())
        if buildingId is None or ct.get_entity_type(buildingId) in (EntityType.ROAD, EntityType.MARKER) + CONVEYOR_TYPES:
            if enoughResources(ct.get_global_resources(), (
                ct.get_splitter_cost()[0] + ct.get_sentinel_cost()[0], 
                ct.get_splitter_cost()[1] + ct.get_sentinel_cost()[1]
            )):
                inputs = 0
                outputs = 0
                splitterPosition = None
                splitterDir = None
                for d in CARDINAL_DIRECTIONS:
                    sourcePosition = ct.get_position().add(d)
                    if not onTheMap(ct, sourcePosition):
                        continue
                    sourcePositionId = ct.get_tile_building_id(sourcePosition)
                    if sourcePositionId is None:
                        continue
                    if (ct.get_entity_type(sourcePositionId) in [EntityType.CONVEYOR, EntityType.ARMOURED_CONVEYOR]):
                        if ct.get_direction(sourcePositionId).opposite() == d:
                            splitterDir = d.opposite()
                            inputs += 1
                        else:
                            outputs += 1
                    if (ct.get_entity_type(sourcePositionId) == EntityType.HARVESTER):
                        splitterDir = d.opposite()
                        inputs += 1
                        if outputs == 0:
                            outputs = 1
                    if (ct.get_entity_type(sourcePositionId) == EntityType.SPLITTER):
                        splitterPosition = sourcePosition
                        splitterDir = ct.get_direction(sourcePositionId)
                        break
                if splitterDir is not None:
                    if splitterPosition is not None:
                        for d in [splitterDir, splitterDir.rotate_left().rotate_left(), splitterDir.rotate_right().rotate_right()]:
                            # We can't feed directly inward
                            if direction == d.opposite():
                                continue
                            
                            turretPosition = splitterPosition.add(d)

                            if not onTheMap(ct, turretPosition):
                                continue

                            if ct.get_tile_env(turretPosition) != Environment.EMPTY:
                                continue

                            occupyingId = ct.get_tile_building_id(turretPosition)

                            # Don't make large turret turns (is this backwards?)
                            if (occupyingId is not None and ct.get_team(occupyingId) == ct.get_team() and ct.get_entity_type(occupyingId) in TURRET_TYPES and (ct.get_entity_type(occupyingId) == EntityType.LAUNCHER or ct.get_direction(occupyingId) in (direction, direction.rotate_left(), direction.rotate_right()))):
                                continue

                            if ct.get_tile_builder_bot_id(turretPosition) is not None:
                                continue

                            # Don't build if there's already an adjacent allied turret
                            # This stops us from forming turret walls that stop conveyors
                            adjacentTurret = False
                            for d2 in CARDINAL_DIRECTIONS:
                                adjacentPosition = turretPosition.add(d2)
                                if onTheMap(ct, adjacentPosition) and ct.is_in_vision(adjacentPosition):
                                    adjacentId = ct.get_tile_building_id(adjacentPosition)

                                    if (adjacentId is not None and ct.get_team(adjacentId) == ct.get_team() and ct.get_entity_type(adjacentId) in TURRET_TYPES):
                                        adjacentTurret = True

                            if adjacentTurret:
                                continue

                            enemyTurrets = 0
                            for enemyPosition in (ct.get_position().add(d),ct.get_position().add(d).add(d),):
                                if not onTheMap(ct, enemyPosition):
                                    continue
                                enemyId = ct.get_tile_building_id(enemyPosition)
                                
                                if ct.get_team(enemyId) == ct.get_team():
                                    continue

                                if ct.get_entity_type(enemyId) not in TURRET_TYPES:
                                    continue

                                enemyTurrets += 1

                            if enemyTurrets > 0:
                                if tryBuildGunner(ct, turretPosition, direction):
                                    break
                            else:
                                if tryBuildSentinel(ct, turretPosition, direction):
                                    break
                    elif (inputs == 1 or buildingId is None) and ct.get_entity_type(buildingId) != EntityType.BRIDGE and outputs > 0:
                        tryBuildSplitter(ct, ct.get_position(), splitterDir)