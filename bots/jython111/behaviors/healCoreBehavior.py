from cambc import Controller, GameConstants

from unit import Unit
from healManager import tryHeal
from behaviors.behavior import Behavior

class HealCoreBehavior(Behavior):
    @staticmethod
    def run(ct: Controller) -> bool:
        if ct.is_in_vision(Unit.corePosition):
            if ct.get_hp(Unit.coreId) < GameConstants.CORE_MAX_HP:
                if ct.get_position().distance_squared(Unit.corePosition) > 2:
                    Unit.astar.moveTo(Unit.corePosition)

                tryHeal(ct, Unit.corePosition)