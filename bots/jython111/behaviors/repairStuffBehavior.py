from cambc import Controller, GameError, GameConstants

from mapUtils import sortIds
from unit import Unit
from healManager import tryHeal
from movementManager import lockMovement, movementIsLocked
from behaviors.behavior import Behavior

class RepairStuffBehavior(Behavior):
    @staticmethod
    def run(ct: Controller) -> None:
        if ct.get_global_resources()[0] < GameConstants.BUILDER_BOT_HEAL_COST[0]:
            return

        for allyId in sortIds(ct, ct.get_position(), ct.get_nearby_buildings()):
            try:
                if ct.get_team(allyId) != ct.get_team():
                    continue

                if ct.get_hp(allyId) >= ct.get_max_hp(allyId):
                    continue

                allyPosition = ct.get_position(allyId)

                Unit.indicator += f"Trying to heal at {allyPosition}...\n"

                ct.draw_indicator_dot(allyPosition, 64, 255, 128)

                if ct.get_position().distance_squared(allyPosition) > 2:
                    Unit.astar.moveTo(allyPosition)
                else:
                    lockMovement()

                if tryHeal(ct, allyPosition):
                    return
                
                if ct.get_move_cooldown() > 0 or movementIsLocked():
                    break
            except GameError:
                continue