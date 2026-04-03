from cambc import Controller, Direction, EntityType

from unit import Unit
from movementManager import tryMove
from mapUtils import isMoveableDirection, enableBreakBarriers, disableBreakBarriers
from data import DIRECTIONS, DIAGONAL_DIRECTIONS

ct: Controller = None

# Map direction to (dx, dy) for distance-to-edge calculation
_DIR_DELTAS = {
    Direction.NORTH: (0, -1),
    Direction.SOUTH: (0, 1),
    Direction.EAST: (1, 0),
    Direction.WEST: (-1, 0),
    Direction.NORTHEAST: (1, -1),
    Direction.NORTHWEST: (-1, -1),
    Direction.SOUTHEAST: (1, 1),
    Direction.SOUTHWEST: (-1, 1),
}

def _distToEdge(x, y, w, h, dx, dy):
    """Calculate how many steps in direction (dx,dy) before going off map."""
    dist = 1_000_000
    if dx > 0:
        dist = min(dist, w - x - 1)
    elif dx < 0:
        dist = min(dist, x)
    if dy > 0:
        dist = min(dist, h - y - 1)
    elif dy < 0:
        dist = min(dist, y)
    return dist

class Explore:
    def __init__(self, _ct: Controller):
        global ct
        ct = _ct
        self.exploreDirection = None

        self.visited = set()
        self.visitedOrder = []

    def setBestExploreDirection(self) -> None:
        myPos = ct.get_position()
        w = ct.get_map_width()
        h = ct.get_map_height()

        # find the direction that will let us move the furthest before hitting the edge of the map
        newDir = None
        bestDist = -10_000
        for d in DIRECTIONS:
            if not isMoveableDirection(ct, d):
                continue

            dx, dy = _DIR_DELTAS[d]
            dist = _distToEdge(myPos.x, myPos.y, w, h, dx, dy)

            if d in DIAGONAL_DIRECTIONS:
                dist += 1

            if d.opposite() == self.exploreDirection:
                dist -= 1_000

            if myPos.add(d) in self.visited:
                ct.draw_indicator_dot(myPos.add(d), 255, 0, 0)
                dist -= self.visitedOrder.index(myPos.add(d))*1_000

            nextBuildingId = ct.get_tile_building_id(myPos.add(d))

            if (nextBuildingId is not None
                and ct.get_entity_type(nextBuildingId) != EntityType.MARKER
                and ct.get_team(nextBuildingId) == ct.get_team()
            ):
                dist -= 500 # Give a large penalty to directions that have our own buildings, since we want to explore new areas

            if dist > bestDist:
                bestDist = dist
                newDir = d

        if newDir != None:
            self.exploreDirection = newDir

    def reset(self) -> None:
        self.exploreDirection = None
        self.visited = set()
        self.visitedOrder = []

    def explore(self) -> None:
        if self.exploreDirection is not None:
            if ct.get_position().add(self.exploreDirection) not in self.visited:
                disableBreakBarriers()

        if self.exploreDirection is None or not isMoveableDirection(ct, self.exploreDirection):
            self.setBestExploreDirection()
        if self.exploreDirection is not None:
            tryMove(ct, self.exploreDirection)

        enableBreakBarriers()

        print(f"Trying to explore {self.exploreDirection}")

    def update(self) -> None:
        self.visited.add(ct.get_position())
        if ct.get_position() not in self.visitedOrder:
            self.visitedOrder.append(ct.get_position())