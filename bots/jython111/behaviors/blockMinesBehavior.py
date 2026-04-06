from cambc import Controller, EntityType, Environment

from buildManager import tryBuildRoad
from fireManager import tryFireAtSelf
from data import CARDINAL_DIRECTIONS, WALKABLE_ENTITIES
from movementManager import lockMovement
from buildManager import Unit, enoughResources, tryBuildBarrier, tryDestroy
from mapUtils import onTheMap, filterEnvironment, sortPositions, enableBreakBarriers, disableBreakBarriers
from behaviors.behavior import Behavior

class BlockMinesBehavior(Behavior):
    @staticmethod
    def run(ct: Controller) -> bool:
        if not enoughResources(ct.get_global_resources(), ct.get_barrier_cost()):
            return False
        
        enoughBarriers = True

        for orePos in sortPositions(ct.get_position(), filterEnvironment(ct, Environment.ORE_TITANIUM, ct.get_nearby_tiles())):
            # This completely ruins the bot for some reasons
            # if ct.is_in_vision(orePos) and ct.get_entity_type(ct.get_tile_building_id(orePos)) == EntityType.BARRIER and ct.get_team():
            #     continue
            
            barriers = 0

            barrierPositions = set()
            for dir in CARDINAL_DIRECTIONS:
                barrierPos = orePos.add(dir)
                if not onTheMap(ct, barrierPos) or (ct.is_in_vision(barrierPos) and ct.get_tile_env(barrierPos) == Environment.WALL):
                    barriers += 1
                    continue
                if not ct.is_in_vision(barrierPos):
                    barriers += 1
                    continue
                barrierPositions.add(barrierPos)
                if ct.get_entity_type(ct.get_tile_building_id(barrierPos)) == EntityType.BARRIER:
                    barriers += 1

            if barriers < 3:
                enoughBarriers = False
            else:
                continue

            for barrierPos in sortPositions(Unit.corePosition, barrierPositions, reverse=(barriers > 0)):
                if onTheMap(ct, barrierPos) and ct.is_in_vision(barrierPos):
                    barrierId = ct.get_tile_building_id(barrierPos)
                    if barrierId is None or ct.get_entity_type(barrierId) in (EntityType.ROAD, EntityType.MARKER) or (ct.get_team(barrierId) != ct.get_team() and ct.get_entity_type(barrierId) in WALKABLE_ENTITIES):
                        ct.draw_indicator_dot(barrierPos, 128, 128, 128)
                        
                        disableBreakBarriers()
                        
                        if ct.get_position() == barrierPos:
                            if barrierId is None or ct.get_team(barrierId) == ct.get_team():
                                Unit.pathfind.goAway(orePos)
                            else:
                                if ct.get_team(barrierId) != ct.get_team():
                                    tryFireAtSelf(ct)
                                    lockMovement()  
                        elif ct.get_position().distance_squared(barrierPos) > 2:
                            Unit.astar.moveTo(barrierPos)

                        enableBreakBarriers()

                        if not ct.is_in_vision(barrierPos) or not ct.is_in_vision(orePos):
                            break
                        
                        if ct.get_entity_type(ct.get_tile_building_id(orePos)) != EntityType.HARVESTER:
                            if tryBuildRoad(ct, orePos):
                                barriers += 1
                                break
                        else:
                            tryDestroy(ct, barrierPos)
                            if tryBuildBarrier(ct, barrierPos):
                                barriers += 1
                                break
                    else:
                        barriers += 1
                        ct.draw_indicator_dot(barrierPos, 128, 255, 128)

        return not enoughBarriers