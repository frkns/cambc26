from cambc import Controller, Direction, Environment

from unit import Unit
from data import CARDINAL_AND_CENTER_DIRECTIONS, CARDINAL_DIRECTIONS, TURRET_TYPES
from buildManager import tryBuildLauncher
from mapUtils import onTheMap
from behaviors.behavior import Behavior

class PlaceLauncherBehavior(Behavior):
    @staticmethod
    def run(ct: Controller, direction: Direction) -> None:
        Unit.indicator += f"Trying to place a launcher facing {direction.value}\n"

        targetLoc = ct.get_position().add(direction)

        if not onTheMap(ct, targetLoc):
            return

        # Don't build if there's already an adjacent allied turret
        # This stops us from forming turret walls that stop conveyors
        for d in CARDINAL_AND_CENTER_DIRECTIONS:
            adjacentPosition = targetLoc.add(d)
            if onTheMap(ct, adjacentPosition) and ct.is_in_vision(adjacentPosition):
                adjacentId = ct.get_tile_building_id(adjacentPosition)

                if (adjacentId is not None and ct.get_team(adjacentId) == ct.get_team() and ct.get_entity_type(adjacentId) in TURRET_TYPES):
                    return

        # Don't build on top of ores
        if ct.get_tile_env(targetLoc) != Environment.EMPTY:
            return

        tryBuildLauncher(ct, targetLoc)