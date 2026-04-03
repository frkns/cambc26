#turret.py
from cambc import *
from utils.building import Building

class Turret:
    @staticmethod
    def tick(ct: Controller):
        tiles = ct.get_nearby_tiles()
        bestPos = None
        bestNum = 99999
        print("Ammo?",ct.get_ammo_amount())
        for tile in tiles:
            daBuildingID = ct.get_tile_building_id(tile)
            if daBuildingID is not None:
                building = Building(ct, daBuildingID, tile)
                if(building.team != ct.get_team()):
                    if building.entityType == EntityType.HARVESTER and tile.distance_squared(ct.get_position())<=2:
                        pass # don't attack harvester feeding us
                    elif(ct.can_fire(building.position)):
                        if(building.entityType == EntityType.CORE):
                            bestPos = building.position
                            bestNum = -1
                        else:
                            daDist = ct.get_position().distance_squared(building.position)
                            if(daDist < bestNum):
                                bestNum = daDist
                                bestPos = building.position
            daBotId = ct.get_tile_builder_bot_id(tile)
            if daBotId is not None:
                if ct.get_team(daBotId) != ct.get_team():
                    daDist = ct.get_position().distance_squared(tile)
                    if(daDist < bestNum):
                        bestNum = daDist
                        bestPos = tile

        if(bestPos != None):
            if(ct.can_fire(bestPos)):
                ct.fire(bestPos)
                ct.draw_indicator_line(ct.get_position(),bestPos,255,0,0)
