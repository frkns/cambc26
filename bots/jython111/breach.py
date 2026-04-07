from cambc import Controller

from unit import Unit

ct: Controller = None

class Breach(Unit):
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
        for enemyId in ct.get_nearby_entities():
            if ct.get_team(enemyId) == ct.get_team():
                continue

            if ct.can_fire(ct.get_position(enemyId)):
                ct.fire(ct.get_position(enemyId))

    def endTurn(self):
        super().endTurn()