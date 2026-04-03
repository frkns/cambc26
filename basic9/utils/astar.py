from cambc import *
from utils.constants import DIRECTIONS
import heapq


class Astar:
    def __init__(self, c: Controller, vision):
        self.c = c
        self.vision = vision

        self.W = c.get_map_width()
        self.H = c.get_map_height()

    def in_bounds(self, pos: Position):
        return 0 <= pos.x < self.W and 0 <= pos.y < self.H

    def move_to(self, target: Position):
        if self.vision.mapdata.get(target, -1) == -1:
            return False

        start = self.c.get_position()
        if start == target:
            return True

        parent = {}
        dist = {start: 0}
        visited = set()

        counter = 0
        heap = []
        heapq.heappush(heap, (0, counter, start))
        parent[start] = None

        while heap:
            curr_dist, _, curr = heapq.heappop(heap)

            if curr in visited:
                continue
            visited.add(curr)

            if curr == target:
                break

            for d in DIRECTIONS:
                nextpos = curr.add(d)

                if not self.in_bounds(nextpos):
                    continue

                if nextpos in self.vision.walkable:
                    weight = 1
                elif nextpos in self.vision.empty:
                    weight = 2
                else:
                    continue

                new_dist = curr_dist + weight

                if nextpos not in dist or new_dist < dist[nextpos]:
                    dist[nextpos] = new_dist
                    parent[nextpos] = curr

                    counter += 1
                    heapq.heappush(heap, (new_dist, counter, nextpos))

        if target not in parent:
            return False

        # Reconstruct first step
        step = target
        while parent[step] != start:
            self.c.draw_indicator_line(step, parent[step], 255, 0, 0)
            step = parent[step]

        direction = start.direction_to(step)
        move_pos = start.add(direction)

        if self.c.can_move(direction):
            self.c.move(direction)
            return True
        elif self.c.can_build_road(move_pos):
            self.c.build_road(move_pos)
            if self.c.can_move(direction):
                self.c.move(direction)
                return True

        return False
