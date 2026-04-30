"""Mythos-simple: stripped-down test bot. Spawn 7 builders, each does
starter-like random walk + harvester building. Used to isolate why
mythos's structured strategy underperforms starter."""

import random
import sys
import traceback
from cambc import Controller, Direction, EntityType, Environment, Position, Team

DIRS_8 = [d for d in Direction if d != Direction.CENTRE]
TARGET_POP = 4


class Player:
    def __init__(self):
        self.spawned = 0

    def run(self, ct: Controller) -> None:
        try:
            etype = ct.get_entity_type()
            if etype == EntityType.CORE:
                self._core_turn(ct)
            elif etype == EntityType.BUILDER_BOT:
                self._builder_turn(ct)
        except Exception:
            sys.stderr.write(traceback.format_exc())

    def _core_turn(self, ct: Controller) -> None:
        if ct.get_action_cooldown() > 0:
            return
        if self.spawned >= TARGET_POP:
            return
        try:
            if ct.get_unit_count() >= 49:
                return
        except Exception:
            pass
        my_pos = ct.get_position()
        for d in DIRS_8:
            cand = my_pos.add(d)
            try:
                if ct.can_spawn(cand):
                    ct.spawn_builder(cand)
                    self.spawned += 1
                    return
            except Exception:
                continue

    def _builder_turn(self, ct: Controller) -> None:
        pos = ct.get_position()
        # Build harvester on any adjacent ore
        for d in DIRS_8:
            check = pos.add(d)
            try:
                if ct.can_build_harvester(check):
                    ct.build_harvester(check)
                    break
            except Exception:
                continue
        # Random walk: lay road then move
        d = random.choice(DIRS_8)
        nxt = pos.add(d)
        try:
            if ct.can_build_road(nxt):
                ct.build_road(nxt)
        except Exception:
            pass
        try:
            if ct.can_move(d):
                ct.move(d)
        except Exception:
            pass
