#main.py
import random

from cambc import *
from utils.constants import Constants
from core import Core
from builder import Builder
from turret import Turret
from launcher import Launcher
import traceback
import sys

class Player:
    def __init__(self):
        Constants.init()
        self.bot = 0

    def run(self, ct: Controller) -> None:
        random.seed(1) 
        try:
            etype = ct.get_entity_type()
            if(etype == EntityType.CORE):
                Core.tick(ct)
            elif etype == EntityType.BUILDER_BOT:
                Builder.tick(ct)
            elif etype == EntityType.GUNNER or etype == EntityType.SENTINEL:
                Turret.tick(ct)
            elif etype == EntityType.LAUNCHER:
                Launcher.tick(ct)
            else:
                print("Hey I'm not implemented ):")
        except Exception as e:
            print("Error in Player.run:", e, file=sys.stderr)
            print(traceback.format_exc(), file=sys.stderr)
