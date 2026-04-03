import time

def bench(n, trials=1000):
    s = set(range(n))

    # list(set)
    t0 = time.perf_counter()
    for _ in range(trials):
        list(s)
    t1 = time.perf_counter()

    # allocate list of same size
    t2 = time.perf_counter()
    for _ in range(trials):
        [None] * n
    t3 = time.perf_counter()

    return (
        (t1 - t0) / trials * 1e6,  # µs
        (t3 - t2) / trials * 1e6
    )

for n in [10, 100, 1000, 10000]:
    t_list_set, t_alloc = bench(n)
    print(f"n={n:5d}  list(set): {t_list_set:8.2f} µs   alloc: {t_alloc:8.2f} µs")
