from cambc import Controller, Position

from movementManager import tryMove

ct: Controller = None

class Pathfind:
    def __init__(self, _ct: Controller):
        global ct
        ct = _ct

    def goTowards(self, target: Position, buildRoads: bool = True) -> None:
        myPos = ct.get_position()
        dir = myPos.direction_to(target)
        tryMove(ct, dir, buildRoads)
        tryMove(ct, dir.rotate_left(), buildRoads)
        tryMove(ct, dir.rotate_right(), buildRoads)
        
    def goAway(self, target: Position, buildRoads: bool = True) -> None:
        myPos = ct.get_position()
        dir = myPos.direction_to(target).opposite()
        tryMove(ct, dir, buildRoads)
        tryMove(ct, dir.rotate_left(), buildRoads)
        tryMove(ct, dir.rotate_right(), buildRoads)