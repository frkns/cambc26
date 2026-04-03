from cambc import Controller

from behaviors.behavior import Behavior
from unit import Unit

class GoTowardsCoreBehavior(Behavior):
    @staticmethod
    def run(ct: Controller) -> None:
        Unit.astar.moveTo(Unit.corePosition)