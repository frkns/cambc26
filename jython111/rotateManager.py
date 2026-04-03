from cambc import Controller, Direction

def tryRotate(ct: Controller, dir: Direction) -> bool:
    if ct.can_rotate(dir):
        ct.rotate(dir)
        return True
    return False