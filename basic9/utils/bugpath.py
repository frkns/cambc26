from cambc import *


class BugPath:
    def __init__(self, c: Controller, vision):
        self.c = c
        self.vision = vision

        self.W = c.get_map_width()
        self.H = c.get_map_height()

        self.states = [[0 for _ in range(self.H)] for _ in range(self.W)]

        self.bugPathIndex = 0
        self.rotateRight = None
        self.lastObstacleFound = None

        self.minDistToTarget = 10**9
        self.minLocationToTarget = None
        self.prevTarget = None

        self.turnsMovingToObstacle = 0
        self.MAX_TURNS_MOVING_TO_OBSTACLE = 2
        self.MIN_DIST_RESET = 3

    def can_move(self, d):
        newloc = self.myLoc.add(d)
        return self.vision.in_bounds(newloc) and (
            self.c.is_tile_passable(newloc)
            or (self.c.is_tile_empty(newloc) and self.c.get_global_resources()[0] > 100)
        )

    def move(self, d):
        if self.c.can_move(d):
            self.c.move(d)
            return
        if (
            self.c.can_build_road(self.c.get_position().add(d))
            and self.c.get_global_resources()[0] > 100
        ):
            self.c.build_road(self.c.get_position().add(d))
            if self.c.can_move(d):
                self.c.move(d)

    def update(self):
        if self.c.get_move_cooldown() != 0:
            return False
        self.myLoc = self.c.get_position()
        return True

    def move_to(self, target: Position):
        if not self.update():
            return

        if target is None:
            target = self.myLoc

        if self.prevTarget is None:
            self.reset_pathfinding()
            self.rotateRight = None
        else:
            distTargets = target.distance_squared(self.prevTarget)
            if distTargets > 0:
                if distTargets >= self.MIN_DIST_RESET:
                    self.rotateRight = None
                    self.reset_pathfinding()
                else:
                    self.soft_reset(target)

        self.prevTarget = target

        self.check_state()
        self.myLoc = self.c.get_position()

        d = self.myLoc.distance_squared(target)
        if d == 0:
            return

        if d < self.minDistToTarget:
            self.reset_pathfinding()
            self.minDistToTarget = d
            self.minLocationToTarget = self.myLoc

        dir = self.myLoc.direction_to(target)

        if self.lastObstacleFound is None:
            if self.try_greedy_move():
                self.reset_pathfinding()
                return
        else:
            dir = self.myLoc.direction_to(self.lastObstacleFound)

        # try direct
        if self.can_move(dir):
            self.move(dir)

            if self.lastObstacleFound is not None:
                self.turnsMovingToObstacle += 1
                self.lastObstacleFound = self.c.get_position().add(dir)

                if self.turnsMovingToObstacle >= self.MAX_TURNS_MOVING_TO_OBSTACLE:
                    self.reset_pathfinding()

            return
        else:
            self.turnsMovingToObstacle = 0

        self.check_rotate(dir)

        # wall following
        for _ in range(8):
            if self.can_move(dir):
                self.move(dir)
                return

            newLoc = self.myLoc.add(dir)

            if not self.in_bounds(newLoc):
                self.rotateRight = not self.rotateRight
            else:
                self.lastObstacleFound = newLoc

            dir = dir.rotate_right() if self.rotateRight else dir.rotate_left()

        self.vision.update()

    def try_greedy_move(self):
        myLoc = self.c.get_position()
        dir = myLoc.direction_to(self.prevTarget)

        if self.can_move(dir):
            self.move(dir)
            return True

        dirR = dir.rotate_right()
        dirL = dir.rotate_left()

        dist = myLoc.distance_squared(self.prevTarget)

        best_dir = None
        best_dist = dist

        if self.can_move(dirR):
            dR = myLoc.add(dirR).distance_squared(self.prevTarget)
            if dR < best_dist:
                best_dist = dR
                best_dir = dirR

        if self.can_move(dirL):
            dL = myLoc.add(dirL).distance_squared(self.prevTarget)
            if dL < best_dist:
                best_dist = dL
                best_dir = dirL

        if best_dir is not None:
            self.move(best_dir)
            return True

        return False

    def check_rotate(self, dir):
        if self.rotateRight is not None:
            return

        dirL = dir
        dirR = dir

        for _ in range(8):
            if not self.can_move(dirL):
                dirL = dirL.rotate_left()
            else:
                break

        for _ in range(8):
            if not self.can_move(dirR):
                dirR = dirR.rotate_right()
            else:
                break

        distL = self.myLoc.add(dirL).distance_squared(self.prevTarget)
        distR = self.myLoc.add(dirR).distance_squared(self.prevTarget)

        self.rotateRight = distR < distL

    def reset_pathfinding(self):
        self.lastObstacleFound = None
        self.minDistToTarget = 10**9
        self.bugPathIndex += 1
        self.turnsMovingToObstacle = 0

    def soft_reset(self, target):
        if self.minLocationToTarget is not None:
            self.minDistToTarget = self.minLocationToTarget.distance_squared(target)
        else:
            self.reset_pathfinding()

    def check_state(self):
        if self.lastObstacleFound is None:
            x, y = 61, 61
        else:
            x, y = self.lastObstacleFound.x, self.lastObstacleFound.y

        state = (self.bugPathIndex << 14) | (x << 8) | (y << 2)

        if self.rotateRight is not None:
            state |= 1 if self.rotateRight else 2

        if self.states[self.myLoc.x][self.myLoc.y] == state:
            self.reset_pathfinding()

        self.states[self.myLoc.x][self.myLoc.y] = state

    def in_bounds(self, pos: Position):
        return 0 <= pos.x < self.W and 0 <= pos.y < self.H
