from cambc import Controller, EntityType

from data import CONVEYOR_TYPES, TURRET_TYPES
from fireManager import tryFire
from rotateManager import tryRotate
from unit import Unit

ct: Controller = None

class Gunner(Unit):
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
        targetDirection = None
        targetScore = -1_000_000

        for entityId in ct.get_nearby_entities():
            if ct.get_team(entityId) == ct.get_team():
                continue

            direction = ct.get_position().direction_to(ct.get_position(entityId))

            if not ct.can_fire_from(ct.get_position(), direction, EntityType.GUNNER, ct.get_position(entityId)):
                ct.draw_indicator_dot(ct.get_position(entityId), 255, 0, 0)
                continue

            ct.draw_indicator_dot(ct.get_position(entityId), 0, 255, 0)

            if ct.get_entity_type(entityId) == EntityType.GUNNER:
                score = 1000
            elif ct.get_entity_type(entityId) in TURRET_TYPES:
                score = 800
            elif ct.get_entity_type(entityId) == EntityType.CORE:
                score = 600
            elif ct.get_entity_type(entityId) in CONVEYOR_TYPES:
                score = 300
            elif ct.get_entity_type(entityId) == EntityType.BUILDER_BOT:
                score = 200
            else:
                score = 100

            if score > targetScore:
                targetScore = score
                targetDirection = direction

        if targetDirection is not None:
            ct.draw_indicator_line(ct.get_position(), ct.get_position().add(targetDirection), 255, 0, 255)
            if targetDirection == ct.get_direction():
                target = ct.get_gunner_target()

                if target is not None:
                    buildingId = ct.get_tile_building_id(target)
                    builderId = ct.get_tile_builder_bot_id(target)

                    # Make sure we don't fire on our core
                    if ct.get_team(buildingId) != ct.get_team() or ct.get_entity_type(buildingId) != EntityType.CORE:            
                        if (ct.get_team(buildingId) != ct.get_team() or (ct.get_team(builderId) != ct.get_team() and (buildingId is None or ct.get_entity_type(buildingId) not in CONVEYOR_TYPES))):
                            tryFire(ct, target)
            else:
                Unit.indicator += f"Trying to rotate {targetDirection} towards target\n"
                Unit.indicator += f"Global Titanium: {ct.get_global_resources()[0]}\nAction Cooldown: {ct.get_action_cooldown()}\nCan rotate to {targetDirection}: {ct.can_rotate(targetDirection)}"
                tryRotate(ct, targetDirection)

    def endTurn(self):
        super().endTurn()