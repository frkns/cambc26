from cambc import Controller, EntityType

from mapUtils import DIRECTIONS, onTheMap, sortPositions
from movementManager import movementIsLocked
from buildManager import Unit, enoughResources, tryBuildBarrier
from fireManager import tryFireAtSelf
from behaviors.behavior import Behavior

class BarricadeBehavior(Behavior):
    @staticmethod
    def run(ct: Controller) -> bool:
        if not enoughResources(ct.get_global_resources(), ct.get_barrier_cost()):
            return
        
        corePosition = None

        for buildingId in ct.get_nearby_buildings():
            if ct.get_team(buildingId) == ct.get_team():
                continue

            if ct.get_entity_type(buildingId) != EntityType.CORE:
                continue

            corePosition = ct.get_position(buildingId)
            break

        if corePosition is not None:
            targets = set()

            for dir in DIRECTIONS:
                for dir2 in (dir, dir.rotate_left(), dir.rotate_right()):
                    targets.add(corePosition.add(dir).add(dir2))

            for targetPos in sortPositions(ct.get_position(), targets):
                if not onTheMap(ct, targetPos) or not ct.is_in_vision(targetPos):
                    continue
                
                targetId = ct.get_tile_building_id(targetPos)

                if ct.get_entity_type(targetId) == EntityType.MARKER:
                    targetId = None

                if targetId is not None and ct.get_team(targetId) == ct.get_team():
                    continue
                    
                if ct.get_position() != targetPos:
                    if targetId is None or ct.get_position().distance_squared(targetPos) > 2:
                        Unit.astar.moveTo(targetPos)

                if not ct.is_in_vision(targetPos):
                    continue

                if ct.get_position() == targetPos:
                    if targetId is not None:
                        tryFireAtSelf(ct)
                        targetId = ct.get_tile_building_id(targetPos)
                        if ct.get_entity_type(targetId) == EntityType.MARKER:
                            targetId = None
                    if targetId is None:
                        Unit.pathfind.goAway(targetPos)
                
                if tryBuildBarrier(ct, targetPos):
                    break

                if ct.get_move_cooldown() > 0 or movementIsLocked():
                    break