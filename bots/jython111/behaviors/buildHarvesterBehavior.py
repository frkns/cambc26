from cambc import Controller, Environment

from buildManager import EntityType, enoughResources, tryBuildHarvester
from movementManager import tryMove
from mapUtils import findCardinalBetween, onTheMap
from behaviors.behavior import Behavior
from unit import Unit
from data import DIRECTIONS, DIRECTIONAL_TURRET_TYPES, CARDINAL_DIRECTIONS

class BuildHarvesterBehavior(Behavior):
    @staticmethod
    def run(ct: Controller) -> None:
        if not enoughResources(ct.get_global_resources(), ct.get_harvester_cost()):
            return

        myPos = ct.get_position()

        for d in DIRECTIONS:
            checkPos = ct.get_position().add(d)
            if not onTheMap(ct, checkPos):
                continue
            buildingId = ct.get_tile_building_id(checkPos)
            if ct.get_tile_building_id(checkPos) is not None:
                if ct.get_team(buildingId) != ct.get_team() or ct.get_entity_type(buildingId) not in (EntityType.BARRIER, EntityType.MARKER):
                    continue
            env = ct.get_tile_env(checkPos)
            if env != Environment.ORE_TITANIUM:
                continue

            feedingEnemyTurret = False
            for d2 in CARDINAL_DIRECTIONS:
                turretPos = checkPos.add(d2)

                if not onTheMap(ct, turretPos) or not ct.is_in_vision(turretPos):
                    continue

                buildingId = ct.get_tile_building_id(turretPos)

                if buildingId is None:
                    continue

                if ct.get_team(buildingId) != ct.get_team() and ct.get_entity_type(buildingId) in DIRECTIONAL_TURRET_TYPES:
                    feedingEnemyTurret = True
                    break

            # If we feed enemy turrets, turret hunting can lead to resource leaks
            if feedingEnemyTurret:
                continue
            
            if tryBuildHarvester(ct, checkPos):
                # try to move next to the harvester we just built if we're not at a cardinal direction
                if (myPos.distance_squared(checkPos) > 1):
                    tryMove(ct, findCardinalBetween(ct, myPos, checkPos))

                Unit.startPath(checkPos)
                break