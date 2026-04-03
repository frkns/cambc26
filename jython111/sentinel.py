from itertools import chain

from cambc import Controller, EntityType

from data import CONVEYOR_TYPES, TURRET_TYPES
from fireManager import tryFire
from unit import Unit

ct: Controller = None

class Sentinel(Unit):
    def __init__(self, _ct: Controller):
        global ct
        super().__init__(_ct)
        ct = _ct

    def updateCt(self, _ct: Controller):
        super().updateCt(_ct)
        global ct
        ct = _ct

    def startTurn(self):
        super().startTurn()

    def runTurn(self) -> None:
        super().runTurn()
        Unit.indicator += f"Loaded: {ct.get_ammo_type()} (x{ct.get_ammo_amount()})\n"

        bestTarget = None
        bestPriority = -1_000_000

        for enemyId in chain(ct.get_nearby_units(), ct.get_nearby_buildings()):
            if ct.get_team(enemyId) == ct.get_team():
                continue

            enemyPos = ct.get_position(enemyId)
            if not ct.is_in_vision(enemyPos):
                continue

            if not ct.can_fire(enemyPos):
                continue

            buildingId = ct.get_tile_building_id(enemyPos)

            if buildingId is not None and ct.get_team(buildingId) == ct.get_team() and ct.get_entity_type(buildingId) in CONVEYOR_TYPES:
                continue

            # Prioritize: builder bots (3) > low-HP targets we can kill (2) > buildings (1) > other (0)
            etype = ct.get_entity_type(enemyId)

            if etype == EntityType.HARVESTER:
                continue

            hp = ct.get_hp(enemyId)
            priority = 0
            if etype in TURRET_TYPES:
                priority = 1000
            elif etype == EntityType.BUILDER_BOT:
                priority = 300
            elif etype == EntityType.CORE:
                priority = 200
            else:
                priority = 100
            # Prefer low HP targets (tiebreak within category)
            priority -= hp

            if priority > bestPriority:
                bestPriority = priority
                bestTarget = enemyPos

        if bestTarget is not None:
            tryFire(ct, bestTarget)

    def endTurn(self):
        super().endTurn()