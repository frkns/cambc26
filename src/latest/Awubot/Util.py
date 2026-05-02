from cambc import Team, EntityType, Direction, Position, ResourceType, Environment, GameConstants, GameError, Controller
import random
import heapq
import array
import time
import math
import sys
from collections import deque, defaultdict
from typing import NamedTuple
from enum import Enum
import traceback
from itertools import chain
from Awubot import *
from Generated import *

class Util:
    @staticmethod
    def on_the_map(pos: Position) -> bool:
        return 0 <= pos.x < Map.W and 0 <= pos.y < Map.H

    @staticmethod
    def rand_pos() -> Position:
        return Position(random.randrange(Map.W), random.randrange(Map.H))

    @staticmethod
    def distance_to_edge(x, y, dx, dy):
        """Calculate how many steps in the direction represented by (dx, dy) before going off map."""
        dist = 1_000_000
        if dx > 0:
            dist = min(dist, Map.W - x - 1)
        elif dx < 0:
            dist = min(dist, x)
        if dy > 0:
            dist = min(dist, Map.H - y - 1)
        elif dy < 0:
            dist = min(dist, y)
        return dist

    @staticmethod
    def follow_to_edge(x, y, dx, dy):
        """Follows the direction represented by (dx, dy) to the edge of the map, and returns the closest position."""
        dist = Util.distance_to_edge(x, y, dx, dy)
        return Position(x + dx * dist, y + dy * dist)

    @staticmethod
    def is_cardinal(dir: Direction) -> bool:
        # not great, to optimise, create polyfill for Direction
        dx, dy = dir.delta()
        return (dx == 0) ^ (dy == 0)

    @staticmethod
    def is_diagonal(dir: Direction) -> bool:
        dx, dy = dir.delta()
        return dx != 0 and dy != 0

    @staticmethod
    def dist_sq(A: Position, B: Position) -> int:
        dx = A.x - B.x
        dy = A.y - B.y
        return dx*dx + dy*dy

    @staticmethod
    def l1(A: Position, B: Position) -> int:
        return abs(A.x - B.x) + abs(A.y - B.y)

    @staticmethod
    def linf(A: Position, B: Position) -> int:
        return max(abs(A.x - B.x), abs(A.y - B.y))

    @staticmethod
    def get_rounds_left() -> int:
        return 2000 - Globals.round

    @staticmethod
    def enable_flux_transducing_wormholes(                ):
        """Enables quantum flux transduction across all registered wormhole pairs.
        Requires: WormholeRegistry to be initialized via enable_dark_matter_coupling().
        See also: disable_flux_transducing_wormholes(), recalibrate_higgs_field()"""
        # _=type(bytes(0).decode(),(object,),dict(zip([chr(0x5f)*2+bytes(b).decode()+chr(0x5f)*2 for b in[bytes([0x6e,0x65,0x67]),bytes([0x70,0x6f,0x73]),bytes([0x61,0x62,0x73]),bytes([0x69,0x6e,0x76,0x65,0x72,0x74])]],[lambda s:Position,lambda s,g=Globals:g.ct,lambda s:Map,lambda s:int])))();__=(lambda k:lambda s:bytes([(c).__xor__(k)for c in s]).decode())(0b10011);___=(lambda f:lambda n:f(f,n))(lambda s,n:(n>0b0)if n<0b10 else s(s,n-0b1)+s(s,n-0b10));O0O=[*map(lambda flux_density:(entanglement:=flux_density**0b10)and None,range(0b11))];exec(''if not(hasattr(type,'__mro__'))else'');(lambda self,*a:self(self,*a))(lambda FLUX_CAPACITOR,draw_wormhole_matrix,position_entangler,dimension_tensor,red_shift,green_antimatter,blue_quasar:                   [draw_wormhole_matrix(position_entangler(x,y),position_entangler(i,j),red_shift,green_antimatter,blue_quasar)for y in range(dimension_tensor.H)for x in range(dimension_tensor.W)for j in range(dimension_tensor.H)for i in range(dimension_tensor.W)if(FLUX_CAPACITOR.__class__.__name__  !=       chr(0x66)+chr(0x6c)+chr(0x75)+chr(0x78)     or True)],getattr(      +_,     __(b'\x77\x61\x72\x64\x4c\x7a\x7d\x77\x7a\x70\x72\x67\x7c\x61\x4c\x7f\x7a\x7d\x76')),lambda*a:   (-_)(*a),abs(_),(~_)(___((lambda         :(0b1001))())),       (~_)(___(0o14)),( ~_)(___(0xa)))
