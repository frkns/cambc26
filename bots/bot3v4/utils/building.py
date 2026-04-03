#utils/building.py
from cambc import *
class Building:
    passableBuildings = [
        EntityType.CONVEYOR,
        EntityType.SPLITTER,
        EntityType.ARMOURED_CONVEYOR,
        EntityType.BRIDGE,
        EntityType.ROAD,
    ]
    def __init__(self, ct: Controller, id: int, tile):
        self.team = ct.get_team(id)
        self.position = tile
        self.id = id
        self.hp = ct.get_hp(id)
        self.max_hp = ct.get_max_hp(id)
        self.entityType = ct.get_entity_type(id)
        self.playerTeam = ct.get_team()
        try:
            self.direction = ct.get_direction(id)
        except Exception as e:
            self.direction = None
        if(self.entityType == self.entityType.BRIDGE):
            self.target = ct.get_bridge_target(id)
        else:
            self.target= None
    def is_passable(self):
        fun = self.entityType in Building.passableBuildings
        if fun:
            return True
        if self.team == self.playerTeam and (self.entityType == EntityType.CORE):
            return True
        if(self.team != self.playerTeam and self.entityType == EntityType.MARKER): #run over enemy markers
            return True
        return False