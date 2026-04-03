import time
import random
from cambc import Position

N = 1_000_000
R = 51  # values 0..50

# Build universe (small domain)
positions = [Position(i, j) for i in range(R) for j in range(R)]
tuples = [(i, j) for i in range(R) for j in range(R)]
ints = [i * R + j for i in range(R) for j in range(R)]

# Build sets
pos_set = set(positions)
tuple_set = set(tuples)
int_set = set(ints)

def bench_position():
    start = time.perf_counter()
    for _ in range(N):
        i = random.randrange(R)
        j = random.randrange(R)
        _ = Position(i, j) in pos_set
    return (time.perf_counter() - start) * 1e6 / N  # avg μs

def bench_tuple():
    start = time.perf_counter()
    for _ in range(N):
        i = random.randrange(R)
        j = random.randrange(R)
        _ = (i, j) in tuple_set
    return (time.perf_counter() - start) * 1e6 / N

def bench_int():
    start = time.perf_counter()
    for _ in range(N):
        i = random.randrange(R)
        j = random.randrange(R)
        _ = (i * R + j) in int_set
    return (time.perf_counter() - start) * 1e6 / N

pos_time = bench_position()
tuple_time = bench_tuple()
int_time = bench_int()

print(f"Position: {pos_time:.3f} μs")
print(f"Tuple:    {tuple_time:.3f} μs")
print(f"Int:      {int_time:.3f} μs")
