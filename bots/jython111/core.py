import sys

from cambc import Controller, EntityType, Environment, GameConstants

from spawnManager import trySpawn
from data import DIRECTIONS, TURRET_TYPES
from unit import Unit

ct: Controller = None

class Core(Unit):
    def __init__(self, _ct: Controller):
        global ct
        super().__init__(_ct)
        ct = _ct

        self.lastTitanium = GameConstants.STARTING_TITANIUM
        self.staticCount = 0
        self.spawnDirection = ct.get_position().direction_to(Unit.center)

    def updateCt(self, _ct: Controller):
        super().updateCt(_ct)
        global ct
        ct = _ct    

    def startTurn(self):
        super().startTurn()

    def runTurn(self) -> None:
        super().runTurn()
        
        titanium, axionite = ct.get_global_resources()

        if titanium <= self.lastTitanium:
            self.staticCount += 1
        else:
            self.staticCount = 0
            
        enemyUnitCount = 0
        allyUnitCount = 0
        for unitId in ct.get_nearby_units():
            if unitId == ct.get_id():
                continue
 
            if ct.get_team(unitId) == ct.get_team():
                allyUnitCount += 1
            else:
                enemyUnitCount += 1

                
        if allyUnitCount < 3:
            for enemyId in ct.get_nearby_buildings():
                if ct.get_team(enemyId) == ct.get_team():
                    continue
                
                if ct.get_entity_type(enemyId) not in TURRET_TYPES:
                    continue

                if ct.get_entity_type(enemyId) == EntityType.LAUNCHER:
                    continue

                # try to spawn defenders
                spawnPos = ct.get_position().add(ct.get_position().direction_to(ct.get_position(enemyId)))
                trySpawn(ct, spawnPos)

        earlyGame = ct.get_current_round() < (ct.get_map_width() + ct.get_map_height())*10
        # botSpam = titanium - ct.get_builder_bot_cost()[0] > 100 and ct.get_current_round() > 150 + (ct.get_map_width() + ct.get_map_height()) * 2
        lateGame = ct.get_current_round() >= GameConstants.MAX_TURNS - 500

        if (
            (self.staticCount == 0 or titanium >= ct.get_conveyor_cost()[0] * 3) and # Make sure we don't completely strand ourselves 
            (
                (
                    (titanium >= GameConstants.STARTING_TITANIUM - 150 - ct.get_current_round()/10 or lateGame) and
                    (
                        not lateGame or # Only do this in the last few hundred rounds
                        axionite > 0 or # We've already made a foundry
                        titanium-ct.get_builder_bot_cost()[0] > ct.get_foundry_cost()[0] # Or we have enough to make a foundry
                    )
                ) or
                (self.staticCount >= 4 and ct.get_current_round() > max(ct.get_map_width(), ct.get_map_height()) * 6) or
                enemyUnitCount-allyUnitCount > 5 or # We're being swarmed
                (ct.get_current_round() < 250 and enemyUnitCount-allyUnitCount > 0) # We're being rushed
            )
            ):
            # # Pick spawn direction towards nearest visible unoccupied ore
            # bestOreDir = None
            # bestOreDist = 1_000_000
            # for tile in ct.get_nearby_tiles():
            #     if ct.get_tile_env(tile) in (Environment.ORE_TITANIUM, Environment.ORE_AXIONITE):
            #         if ct.get_tile_building_id(tile) is None:
            #             d = ct.get_position().distance_squared(tile)
            #             if d < bestOreDist:
            #                 bestOreDist = d
            #                 bestOreDir = ct.get_position().direction_to(tile)
            # if bestOreDir is not None:
            #     self.spawnDirection = bestOreDir

            # try to spawn bots
            spawnPos = ct.get_position().add(self.spawnDirection)
            if trySpawn(ct, spawnPos):
                self.staticCount = 0
                self.spawnDirection = self.spawnDirection.opposite().rotate_right()

        self.lastTitanium = titanium

        Unit.indicator += f"Static rounds: {self.staticCount}"

    def endTurn(self):
        super().endTurn()