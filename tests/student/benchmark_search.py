from pathlib import Path
from random import Random
from statistics import median
import sys
from time import perf_counter_ns


sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "Python" / "source"))
from algorithms import kmp, naive, rk


def cases():
    for n, m in [(500, 50), (1500, 150), (3000, 300)]:
        seed = 2026 + n
        rng = Random(seed)
        text = "".join(rng.choice("abcd") for _ in range(n))
        start = rng.randrange(n - m + 1)
        yield "random", n, m, str(seed), text, text[start:start + m]
        yield "repetitive", n, m, "none", "a" * (n - 1) + "b", "a" * (m - 1) + "b"


def main():
    print("case,n,m,seed,algorithm,run_1_ms,run_2_ms,run_3_ms,median_ms,matches")
    for case, n, m, seed, text, pattern in cases():
        request = {"text": text, "pattern": pattern}
        expected = {"positions": [i for i in range(n - m + 1) if text.startswith(pattern, i)]}
        algorithms = (naive, kmp, rk)
        times = {algorithm: [] for algorithm in algorithms}
        for algorithm in algorithms:
            assert algorithm(request) == expected
        for _ in range(3):
            for algorithm in algorithms:
                start = perf_counter_ns()
                result = algorithm(request)
                elapsed = perf_counter_ns() - start
                assert result == expected
                times[algorithm].append(elapsed / 1_000_000)
        for algorithm, samples in times.items():
            measurements = ",".join(f"{sample:.4f}" for sample in [*samples, median(samples)])
            print(f"{case},{n},{m},{seed},{algorithm.__name__},{measurements},{len(expected['positions'])}")


if __name__ == "__main__":
    main()
