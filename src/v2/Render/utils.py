import inspect
from functools import cache


def num_fmt(x):
    return str(x).replace("-", "_neg_").replace(".", "_dot_")


def bitwise_and(a, b):
    return a & b


def bitwise_or(a, b):
    return a | b


def bitwise_xor(a, b):
    return a ^ b


def bitwise_not(a):
    return ~a


def left_shift(a, shift):
    return a << shift


def right_shift(a, shift):
    return a >> shift


def capitalize(s):
    return s[0].upper() + s[1:]


def int_div(i, d):
    return i // d


def static_assert(cond):
    if not cond:
        raise Exception('static assertion failed')
    return ''


def bit_length(x):
    return (x).bit_length()


@cache
def ctz(x):
    return (x & -x).bit_length() - 1


@cache
def submasks(mask):
    sub = mask
    ret = []
    while sub:
        ret.append(sub)
        sub = (sub - 1) & mask
    ret.append(0)
    return tuple(ret)


def upper_to_pascal(s: str) -> str:
    return ''.join(word.capitalize() for word in s.split('_') if word)


def sign(x: int):
    return f'{x:+d}'

def sign0(x: int):
    if x == 0:
        return ''
    return f'{x:+d}'


def register(env):
    env.globals.update({
        name: obj
        for name, obj in globals().items()
        if callable(obj)
        and not name.startswith('_')
        and name != 'register'
        and getattr(obj, '__module__', None) == __name__
    })
