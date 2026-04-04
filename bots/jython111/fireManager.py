from cambc import Controller, Position

def tryFire(ct: Controller, target: Position) -> bool:
    if ct.can_fire(target):
        ct.fire(target)
        return True
    return False

def tryFireAtSelf(ct: Controller) -> bool:
    return tryFire(ct, ct.get_position())