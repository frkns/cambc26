from itertools import chain

from cambc import Controller, EntityType, GameConstants

from behaviors import *
from movementManager import unlockMovement
from data import ENEMY_WALKABLE_ENTITIES, TURRET_TYPES
from pathfind import Pathfind
from explore import Explore
from bugnav import BugNav
from astar import AStar
from symmetry import Symmetry
from unit import Unit
from mapUtils import enableBreakBarriers

from buildManager import enoughResources

import pathfind as m_pathfind, explore as m_explore, bugnav as m_bugnav

ct: Controller = None

class Builder(Unit):
    def __init__(self, _ct: Controller):
        global ct
        super().__init__(_ct)
        ct = _ct

        Unit.coreId = ct.get_tile_building_id(ct.get_position())

        Unit.corePosition = ct.get_position(Unit.coreId) # get the position of the core we spawned from

        Unit.pathfind = Pathfind(ct)
        Unit.explore = Explore(ct)
        Unit.bugnav = BugNav(ct)
        Unit.astar = AStar(ct)

        Unit.symmetry = Symmetry()

        if ct.get_current_round() > 1500:
            Unit.explore.exploreDirection = Unit.corePosition.direction_to(ct.get_position())

        self.explore = Explore(ct) # helper class for exploring the map

    def updateCt(self, _ct: Controller):
        super().updateCt(_ct)
        global ct
        ct = _ct
        
        m_pathfind.ct = _ct
        m_explore.ct = _ct
        m_bugnav.ct = _ct

    def startTurn(self):
        super().startTurn()

        unlockMovement()
        enableBreakBarriers()

    def runTurn(self) -> None:
        super().runTurn()

        destroyingSupplies = False

        rushing = enoughResources(ct.get_global_resources(), ct.get_sentinel_cost()) and Unit.spawnRound % 3 == 0

        if not rushing and ct.get_current_round() % 100 > 90:
            if ct.get_id() % 2 == (ct.get_current_round() // 100) % 2 and not Unit.connecting:
                InspectConveyorBehavior.run(ct)
            else:
                if Unit.inspecting:
                    Unit.indicator += "Ending path because we're done inspecting\n"
                    Unit.clearPath()

        allyUnits = 0
        enemyUnits = 0
        enemyHarvesters = 0
        allyBuildings = 0
        enemyBuildings = 0
        unitsNearCore = 0
        for enemyId in ct.get_nearby_units():
            if ct.get_team(enemyId) == ct.get_team():
                allyUnits += 1
                continue

            enemyUnits += 1

            if ct.get_position(enemyId).distance_squared(Unit.corePosition) < 36:
                unitsNearCore += 1

        for enemyId in ct.get_nearby_buildings():
            if ct.get_team(enemyId) == ct.get_team():
                continue

            if ct.get_entity_type(enemyId) == EntityType.HARVESTER:
                enemyHarvesters += 1

        for enemyId in ct.get_nearby_buildings():
            if ct.get_team(enemyId) == ct.get_team():
                allyBuildings += 1
                continue

            enemyBuildings += 1

        RepairStuffBehavior.run(ct)

        if Unit.connecting:
            TurretHunterBehavior.run(ct)

            # blockingMines = BlockMinesBehavior.run(ct)

            # if not blockingMines:
            PlaceConveyorBehavior.run(ct, Unit.corePosition)

            myBuildingId = ct.get_tile_building_id(ct.get_position())
            myBuildingType = ct.get_entity_type(myBuildingId)
            if (myBuildingType in (EntityType.CONVEYOR, EntityType.CORE)
                and ct.get_team(myBuildingId) == ct.get_team()):

                if Builder.coreId in ct.get_nearby_buildings(1):
                    Unit.indicator += "Ending path because we reached the core\n"
                    Unit.clearPath()

            Unit.explore.reset()
        else:
            # BarricadeBehavior.run(ct)

            if enemyUnits > 2 or enemyHarvesters > 0:
                TurretAroundMines.run(ct)
                
            # if rushing:
            #     CommandeerBehavior.run(ct)

            resources = ct.get_global_resources()
            if enoughResources(resources, ct.get_foundry_cost()) and resources[1] == 0 and ct.get_current_round() > 50:
                BuildFoundriesBehavior.run(ct)

            if enoughResources(resources, ct.get_harvester_cost()):
                BuildHarvesterBehavior.run(ct)
                
                GoTowardsOreBehavior.run(ct)

            # BlockMinesBehavior.run(ct)

            TurretHunterBehavior.run(ct)

            if not rushing or not enoughResources(resources, ct.get_sentinel_cost()):
                destroyingSupplies = BombSuppliesBehavior.run(ct)

            if ct.get_current_round() > max(ct.get_map_width(), ct.get_map_height()):
                for enemyId in chain(ct.get_nearby_units(), ct.get_nearby_buildings(17)):
                    if ct.get_action_cooldown() > 0:
                        break

                    if ct.get_team(enemyId) == ct.get_team():
                        continue

                    enemyType = ct.get_entity_type(enemyId)
                    enemyPosition = ct.get_position(enemyId)

                    if enemyType == EntityType.MARKER:
                        continue

                    if enemyType in ENEMY_WALKABLE_ENTITIES:
                        continue

                    if enemyType == EntityType.BUILDER_BOT and ct.get_position().distance_squared(enemyPosition) <= 16:
                        if ct.get_position().distance_squared(enemyPosition) >= 9:
                            Unit.pathfind.goTowards(enemyPosition)
                        if ct.get_position().distance_squared(enemyPosition) <= 2:
                            Unit.pathfind.goAway(enemyPosition)
                        PlaceLauncherBehavior.run(ct, ct.get_position().direction_to(enemyPosition))

                    # if enemyType == EntityType.CORE and ct.get_position().distance_squared(enemyPosition) <= 9:
                    #     dirToEnemyCore = ct.get_position().direction_to(enemyPosition)
                    #     for dir in (dirToEnemyCore, dirToEnemyCore.rotate_left(), dirToEnemyCore.rotate_right(), dirToEnemyCore.rotate_left().rotate_left(), dirToEnemyCore.rotate_right().rotate_right()):
                    #         PlaceLauncherBehavior.run(ct, dir)

                    #         if ct.get_action_cooldown() > 0:
                    #             break
                    
                    if enemyType in TURRET_TYPES:
                        PlaceTurretBehavior.run(ct, ct.get_position().direction_to(enemyPosition))

                    break

            if rushing:
                GoTowardsEnemyCoreBehavior.run(ct)

        if not rushing:
            BombEverythingBehavior.run(ct)

        # if unitsNearCore >= allyUnits and ct.get_current_round() < 150 and ct.get_position().distance_squared(Unit.corePosition) > 16:
        #     Unit.astar.moveTo(Unit.corePosition)

        HealCoreBehavior.run(ct)

        if not Unit.connecting and Unit.alive and not destroyingSupplies:   
            if (ct.get_action_cooldown() == 0):
                self.explore.explore()

        RandomlyHealBehavior.run(ct) # TODO: Try moving this up
        TerraformEverythingBehavior.run(ct)

        RandomlyMarkStuffBehavior.run(ct)

    def endTurn(self):
        Unit.indicator += f"{str(Unit.symmetry)}\nConnecting: {Unit.connecting}\nInspecting: {Unit.inspecting}\n"

        Unit.explore.update()

        super().endTurn()

        Unit.symmetry.update(ct)