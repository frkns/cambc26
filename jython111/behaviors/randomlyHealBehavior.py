from itertools import chain

from cambc import Controller

from healManager import tryHeal
from behaviors.behavior import Behavior

class RandomlyHealBehavior(Behavior):
    @staticmethod
    def run(ct: Controller) -> None:
        if ct.get_hp() <= ct.get_max_hp()-4:
            if tryHeal(ct, ct.get_position()):
                return

        for allyId in chain(ct.get_nearby_units(), ct.get_nearby_buildings()):
            if ct.get_team(allyId) != ct.get_team():
                continue

            if ct.get_hp(allyId) > ct.get_max_hp(allyId)-4:
                continue

            if tryHeal(ct, ct.get_position(allyId)):
                return