"""
Adapted by Claude Code from XSquare's 2026 Battlecode public repo.
"""

from cambc import Controller, Direction, Position

from mapUtils import onTheMap, isMoveableDirection
from movementManager import lockMovement, tryMove
from data import DEBUG

ct: Controller = None

INF = 1000000
MAX_TURNS_MOVING_TO_OBSTACLE = 3


class BugNav:
    def __init__(self, _ct: Controller):
        global ct
        ct = _ct
        self.turnsMovingToObstacle = 0
        self.rotateRight = None  # None means undecided, True/False once chosen
        self.lastObstacleFound: Position = None
        self.minDistToTarget = INF
        self.minLocToTarget: Position = None
        self.prevTarget: Position = None
        self.states: set = set()

    def canMove(self, direction: Direction) -> bool:
        if direction == Direction.CENTRE:
            return False
        return isMoveableDirection(ct, direction)

    def moveTo(self, target: Position):
        if target is None:
            return
        if ct.get_move_cooldown() > 0:
            return
        myLoc = ct.get_position()
        if myLoc.distance_squared(target) == 0:
            return

        if DEBUG:
            ct.draw_indicator_line(ct.get_position(), target, 255, 255, 255)

        distBetweenTargets = 0
        if self.prevTarget is None:
            self.resetPathfinding(True)
        else:
            distBetweenTargets = self.prevTarget.distance_squared(target)

        self.prevTarget = target
        if distBetweenTargets > 2:
            self.resetPathfinding(True)
        elif distBetweenTargets > 0:
            self.softResetPathfinding()

        self.checkStates()

        myLoc = ct.get_position()
        d = myLoc.distance_squared(target)
        if d < self.minDistToTarget:
            self.resetPathfinding(False)
            self.minDistToTarget = d
            self.minLocToTarget = ct.get_position()

        direction = myLoc.direction_to(target)
        if self.lastObstacleFound is not None:
            direction = myLoc.direction_to(self.lastObstacleFound)

        if self.canMove(direction):
            self.doMove(direction)
            if self.lastObstacleFound is not None:
                self.turnsMovingToObstacle += 1
                self.lastObstacleFound = ct.get_position().add(direction)
                if self.turnsMovingToObstacle >= MAX_TURNS_MOVING_TO_OBSTACLE or not onTheMap(ct, self.lastObstacleFound):
                    self.resetPathfinding(False)
            return
        else:
            self.turnsMovingToObstacle = 0

        self.updateRotation()

        for i in range(16):
            if self.canMove(direction):
                self.doMove(direction)
                return
            newLoc = myLoc.add(direction)
            if not onTheMap(ct, newLoc.add(direction)):
                self.rotateRight = not self.rotateRight
            else:
                self.lastObstacleFound = myLoc.add(direction)
            if self.rotateRight:
                direction = direction.rotate_right()
            else:
                direction = direction.rotate_left()

        if self.canMove(direction):
            self.doMove(direction)

    def resetPathfinding(self, resetRotation: bool):
        self.lastObstacleFound = None
        self.minDistToTarget = INF
        self.minLocToTarget = None
        self.turnsMovingToObstacle = 0
        if resetRotation:
            self.rotateRight = None
        self.states = set()

    def softResetPathfinding(self):
        if self.minLocToTarget is not None:
            dist = self.minLocToTarget.distance_squared(self.prevTarget)
            currentDist = ct.get_position().distance_squared(self.prevTarget)
            if dist < currentDist:
                self.minDistToTarget = dist
            else:
                self.minDistToTarget = currentDist
                self.minLocToTarget = ct.get_position()
        else:
            self.resetPathfinding(False)

    def checkStates(self):
        if self.lastObstacleFound is None:
            return
        myLoc = ct.get_position()
        dirToObstacle = myLoc.direction_to(self.lastObstacleFound)
        code = (myLoc.x, myLoc.y, self.rotateRight, dirToObstacle)
        if code in self.states:
            self.resetPathfinding(False)
        else:
            self.states.add(code)

    def updateRotation(self):
        if self.rotateRight is not None:
            return
        myLoc = ct.get_position()
        direction = myLoc.direction_to(self.prevTarget)
        dirL = direction
        dirR = direction
        locL = myLoc
        locR = myLoc
        for i in range(8):
            dirL = dirL.rotate_left()
            locL = myLoc.add(dirL)
            if self.canMove(dirL):
                break
        for i in range(8):
            dirR = dirR.rotate_right()
            locR = myLoc.add(dirR)
            if self.canMove(dirR):
                break
        if locL.distance_squared(self.prevTarget) < locR.distance_squared(self.prevTarget):
            self.rotateRight = False
            return
        self.rotateRight = True

    def doMove(self, direction: Direction):
        tryMove(ct, direction)
        lockMovement()
