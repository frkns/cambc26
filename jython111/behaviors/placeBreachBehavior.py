from cambc import Controller, Direction

from buildManager import tryBuildBreach
from behaviors.behavior import Behavior

class PlaceBreachBehavior(Behavior):
    @staticmethod
    def run(ct: Controller, direction: Direction) -> None:
        tryBuildBreach(ct, ct.get_position().add(direction), direction)