from cambc import Controller, Direction, EntityType

from mapUtils import onTheMap
from launchManager import tryLaunch
from data import ALL_DIRECTIONS, DIRECTIONS, DIRECTION_TO_INDEX
from unit import Unit

ct: Controller = None

class Launcher(Unit):
    def __init__(self, _ct: Controller):
        global ct
        super().__init__(_ct)
        ct = _ct

        for buildingId in ct.get_nearby_buildings():
            if ct.get_team(buildingId) == ct.get_team() and ct.get_entity_type(buildingId) == EntityType.CORE:
                Unit.coreId = buildingId
                Unit.corePosition = ct.get_position(buildingId)

    def updateCt(self, _ct: Controller):
        super().updateCt(_ct)
        global ct
        ct = _ct    

    def startTurn(self):
        super().startTurn()

    def runTurn(self) -> None:
        super().runTurn()

        directionDensities = [0] * 8

        for enemyId in ct.get_nearby_entities():
            if ct.get_team(enemyId) == ct.get_team():
                continue

            enemyDirection = ct.get_position().direction_to(ct.get_position(enemyId))
            directionIndex = DIRECTION_TO_INDEX[enemyDirection]

            directionDensities[directionIndex] += 5 if ct.get_entity_type(enemyId) == EntityType.BUILDER_BOT else 1

        denseDirection: Direction = None
        bestDensity = 0

        for d in range(8):
            if directionDensities[d] > bestDensity:
                bestDensity = directionDensities[d]
                denseDirection = DIRECTIONS[d]

        for direction in DIRECTIONS:
            builderPosition = ct.get_position().add(direction)
            
            if not onTheMap(ct, builderPosition):
                continue

            builderId = ct.get_tile_builder_bot_id(builderPosition)

            if builderId is None:
                continue

            if ct.get_team(builderId) == ct.get_team():
                continue

            awayDirection = direction

            if bestDensity > 1:
                awayDirection = denseDirection

            if Unit.corePosition is not None:
                awayDirection = Unit.corePosition.direction_to(ct.get_position())

            corePosition = None
            for buildingId in ct.get_nearby_buildings():
                if ct.get_team(buildingId) == ct.get_team():
                    continue

                if ct.get_entity_type(buildingId) != EntityType.CORE:
                    continue
                
                corePosition = ct.get_position(buildingId)

            if corePosition is not None:
                for dir in ALL_DIRECTIONS:
                    if tryLaunch(ct, builderPosition, corePosition.add(dir)):
                        break

            for launchDirection in (awayDirection, awayDirection.rotate_left(), awayDirection.rotate_right(), awayDirection.rotate_left().rotate_left(), awayDirection.rotate_right().rotate_right()):
                end = ct.get_position().add(launchDirection)
                lastValid = end
                lastOnCore = None

                while ct.is_in_vision(end):
                    end = end.add(launchDirection)
                    if ct.can_launch(builderPosition, end):
                        lastValid = end
                        # Landing on the enemy core is super good
                        if ct.get_entity_type(ct.get_tile_building_id(end)) == EntityType.CORE:
                            lastOnCore = end

                targetEnd = lastValid

                if lastOnCore is not None:
                    targetEnd = lastOnCore

                if tryLaunch(ct, builderPosition, targetEnd):
                    break
            else:
                for end in ct.get_nearby_tiles():
                    if tryLaunch(ct, builderPosition, end):
                        break

    def endTurn(self):
        super().endTurn()