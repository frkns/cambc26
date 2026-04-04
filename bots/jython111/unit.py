from __future__ import annotations
from typing import TYPE_CHECKING

from cambc import Controller, Position
import random

if TYPE_CHECKING:
    from pathfind import Pathfind
    from explore import Explore
    from bugnav import BugNav
    from astar import AStar
    from symmetry import Symmetry

ct: Controller = None

class Unit:
    spawnRound = -1
    spawnPosition = None
    roundsAlive = 0
    center = None

    rng: random.Random = None

    alive: bool = True

    pathfind: Pathfind = None
    explore: Explore = None
    bugnav: BugNav = None
    astar: AStar = None

    symmetry: Symmetry = None
    
    startedConnection = False
    connecting = False
    inspecting = False
    roundsSinceBuild = 0

    path: list[Position] = []
    pathSet: set[Position] = set()

    coreId = None
    corePosition: Position = None

    harvesterPosition: Position = None

    indicator = ""

    def __init__(self, _ct: Controller):
        global ct
        Unit.rng = random.Random(_ct.get_id())

        Unit.spawnRound = _ct.get_current_round()
        Unit.spawnPosition = _ct.get_position()
        Unit.roundsAlive = 0
        Unit.center = Position(_ct.get_map_width() // 2, _ct.get_map_height() // 2)

        ct = _ct

    def clearPath():
        Unit.connecting = False
        Unit.path = []
        Unit.pathSet = set()
        Unit.startedConnection = False
        Unit.inspecting = False

    def startPath(pos: Position, inspecting: bool = False):
        Unit.path = []
        Unit.pathSet = set()
        Unit.connecting = True
        Unit.harvesterPosition = pos
        Unit.startedConnection = False
        Unit.inspecting = inspecting
        Unit.roundsSinceBuild = 0

    def updateCt(self, _ct: Controller):
        global ct
        ct = _ct

    def startTurn(self) -> None:
        Unit.indicator = ""
    
    def runTurn(self) -> None:
        pass

    def endTurn(self) -> None:
        self.roundsAlive += 1

        print(Unit.indicator)