from cambc import Controller

from data import ALL_DIRECTIONS
from buildManager import tryPlaceMarker
from unit import Unit
from mapUtils import onTheMap
from behaviors.behavior import Behavior

class RandomlyMarkStuffBehavior(Behavior):
    @staticmethod
    def run(ct: Controller) -> None:
        for dir in Unit.rng.sample(ALL_DIRECTIONS, len(ALL_DIRECTIONS)):
            if onTheMap(ct, ct.get_position().add(dir)):
                if tryPlaceMarker(ct, ct.get_position().add(dir), 42):
                    return