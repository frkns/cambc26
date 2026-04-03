from cambc import Controller

from behaviors.behavior import Behavior
from unit import Unit

class GoTowardsEnemyCoreBehavior(Behavior):
    @staticmethod
    def run(ct: Controller) -> None:
            if Unit.symmetry.canPredict():
                target = Unit.symmetry.getSymmetryType()(ct, Unit.corePosition)
                if ct.get_position().distance_squared(target) > 8:
                    Unit.astar.moveTo(target)