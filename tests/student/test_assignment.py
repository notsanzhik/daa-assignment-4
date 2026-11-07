import itertools
import json
from pathlib import Path
import random
import subprocess
import sys
import unittest


PROGRAM = Path(__file__).resolve().parents[2] / "Python" / "source" / "main.py"


def is_subsequence(sequence, text):
    remaining = iter(text)
    return all(character in remaining for character in sequence)


def brute_lcs_length(a, b):
    for length in range(len(a), -1, -1):
        for letters in itertools.combinations(a, length):
            if is_subsequence(letters, b):
                return length


def brute_merge_cost(sizes):
    if len(sizes) <= 1:
        return 0
    costs = []
    for i in range(len(sizes) - 1):
        merged = sizes[i] + sizes[i + 1]
        smaller = sizes[:i] + [merged] + sizes[i + 2:]
        costs.append(merged + brute_merge_cost(smaller))
    return min(costs)


def brute_tree_weight(weights, edges):
    best = 0
    vertices = range(len(weights))
    for size in range(len(weights) + 1):
        for choice in itertools.combinations(vertices, size):
            selected = set(choice)
            if all(u not in selected or v not in selected for u, v in edges):
                best = max(best, sum(weights[u] for u in choice))
    return best


def expected_positions(text, pattern):
    return [i for i in range(len(text) - len(pattern) + 1)
            if text.startswith(pattern, i)]


def direct_lcp(first, second):
    for length, (left, right) in enumerate(zip(first, second)):
        if left != right:
            return length
    return min(len(first), len(second))


class AssignmentTests(unittest.TestCase):
    def run_batch(self, requests):
        data = "".join(json.dumps(request) + "\n" for request in requests)
        result = subprocess.run(
            [sys.executable, str(PROGRAM)],
            input=data,
            capture_output=True,
            encoding="utf-8",
            timeout=20,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        lines = result.stdout.splitlines()
        self.assertEqual(len(lines), len(requests))
        answers = [json.loads(line) for line in lines]
        for answer in answers:
            self.assertIsInstance(answer, dict)
        return answers

    def check_lcs(self, answer, a, b, length):
        sequence = answer["sequence"]
        self.assertIs(type(answer["length"]), int)
        self.assertIsInstance(sequence, str)
        self.assertEqual(answer["length"], length)
        self.assertEqual(len(sequence), length)
        self.assertTrue(is_subsequence(sequence, a))
        self.assertTrue(is_subsequence(sequence, b))

    def check_merge(self, answer, sizes, expected_cost):
        cost, plan = answer["cost"], answer["plan"]
        self.assertIs(type(cost), int)
        self.assertEqual(cost, expected_cost)
        self.assertIsInstance(plan, list)
        self.assertEqual(len(plan), max(0, len(sizes) - 1))
        current = {(i, i): size for i, size in enumerate(sizes)}
        paid = 0
        for step in plan:
            self.assertIsInstance(step, list)
            self.assertEqual(len(step), 3)
            for index in step:
                self.assertIs(type(index), int)
            left, split, right = step
            self.assertIn((left, split), current)
            self.assertIn((split + 1, right), current)
            merged = current.pop((left, split)) + current.pop((split + 1, right))
            current[left, right] = merged
            paid += merged
        self.assertEqual(paid, cost)
        if sizes:
            self.assertEqual(current, {(0, len(sizes) - 1): sum(sizes)})

    def check_tree(self, answer, weights, edges, expected_weight):
        weight, chosen = answer["weight"], answer["selected"]
        self.assertIs(type(weight), int)
        self.assertEqual(weight, expected_weight)
        self.assertIsInstance(chosen, list)
        for vertex in chosen:
            self.assertIs(type(vertex), int)
            self.assertTrue(0 <= vertex < len(weights))
        selected = set(chosen)
        self.assertEqual(len(selected), len(chosen))
        self.assertFalse(any(u in selected and v in selected for u, v in edges))
        self.assertEqual(sum(weights[vertex] for vertex in chosen), weight)

    def test_lcs_small_and_ties(self):
        pairs = [("", ""), ("", "x"), ("x", ""), ("a!b?c", "abc"),
                 ("baaa", "aaaa"), ("abc", "bac")]
        rng = random.Random(4)
        for _ in range(30):
            pairs.append(("".join(rng.choices("aA! ", k=rng.randrange(8))),
                          "".join(rng.choices("aA! ", k=rng.randrange(8)))))
        results = self.run_batch([dict(task="lcs", a=a, b=b) for a, b in pairs])
        for (a, b), answer in zip(pairs, results):
            with self.subTest(a=a, b=b):
                self.check_lcs(answer, a, b, brute_lcs_length(a, b))

    def test_lcs_at_limit(self):
        a = "aB" * 500
        b = "Ba" * 500
        answer, = self.run_batch([dict(task="lcs", a=a, b=b)])
        self.check_lcs(answer, a, b, 999)

    def test_merge_small_and_chronological(self):
        sizes_list = [[], [1_000_000_000], [0, 0, 0], [1, 1, 1], [1, 9, 1],
                      [4, 2, 3, 0], [1_000_000_000] * 4]
        rng = random.Random(5)
        for _ in range(24):
            sizes_list.append(rng.choices(range(8), k=rng.randrange(7)))
        results = self.run_batch([dict(task="merge", sizes=sizes) for sizes in sizes_list])
        for sizes, answer in zip(sizes_list, results):
            with self.subTest(sizes=sizes):
                self.check_merge(answer, sizes, brute_merge_cost(sizes))

    def test_merge_at_limit(self):
        sizes = [1_000_000_000] * 200
        answer, = self.run_batch([dict(task="merge", sizes=sizes)])
        # The shallowest full binary tree has 56 leaves at depth 7 and 144 at 8.
        self.check_merge(answer, sizes, 1_000_000_000 * (56 * 7 + 144 * 8))

    def test_tree_small_and_ties(self):
        cases = [([], []), ([0], []), ([-1], []), ([6], []),
                 ([-7, -5, -6], [(1, 0), (2, 1)]),
                 ([2, 2, 0], [(2, 0), (0, 1)])]
        rng = random.Random(6)
        for _ in range(24):
            n = rng.randrange(2, 9)
            edges = [(i, rng.randrange(i)) for i in range(1, n)]
            rng.shuffle(edges)
            cases.append((rng.choices(range(-5, 6), k=n), edges))
        results = self.run_batch(
            [dict(task="tree", n=len(w), weights=w, edges=e) for w, e in cases]
        )
        for (weights, edges), answer in zip(cases, results):
            with self.subTest(weights=weights, edges=edges):
                self.check_tree(answer, weights, edges, brute_tree_weight(weights, edges))

    def test_tree_deep_chain_at_limit(self):
        n = 100_000
        weights = [1_000_000_000] * n
        edges = [(i + 1, i) for i in range(n - 1)]
        answer, = self.run_batch([dict(task="tree", n=n, weights=weights, edges=edges)])
        self.check_tree(answer, weights, edges, 50_000 * 1_000_000_000)

    def test_search_common_domain(self):
        pairs = [("", ""), ("ab", ""), ("", "ab"), ("ab", "abc"),
                 ("A!?a!? A!?", "A!?"), ("aaaaa", "aaa"), ("abababa", "aba"),
                 ("a" * 3_000, "a" * 1_500), ("!" * 3_000, "!" * 3_000)]
        rng = random.Random(7)
        for _ in range(30):
            text = "".join(rng.choices("aA! ", k=25))
            pattern = "".join(rng.choices("aA! ", k=rng.randrange(6)))
            pairs.append((text, pattern))
        requests = [dict(task=task, text=text, pattern=pattern)
                    for text, pattern in pairs for task in ("naive", "kmp", "rk")]
        for request, answer in zip(requests, self.run_batch(requests)):
            with self.subTest(task=request["task"], n=len(request["text"]),
                              pattern=request["pattern"][:20]):
                positions = answer["positions"]
                self.assertTrue(all(type(pos) is int for pos in positions))
                self.assertEqual(positions, expected_positions(request["text"], request["pattern"]))

    def test_rk_collisions_and_negative_update(self):
        pairs = [("abdj", "ab"), ("djdjabdjdjab", "ab"),
                 ("ababdjabab", "dj"), ("ababa", "ba"), ("dj" * 5000, "ab")]
        requests = [dict(task="rk", text=text, pattern=pattern) for text, pattern in pairs]
        for (text, pattern), answer in zip(pairs, self.run_batch(requests)):
            self.assertEqual(answer["positions"], expected_positions(text, pattern))

    def test_search_at_larger_limits(self):
        requests = [
            dict(task="kmp", text="a" * 200_000, pattern="a" * 100_000),
            dict(task="kmp", text="a" * 200_000, pattern="a" * 99_999 + "!"),
            dict(task="rk", text="!" * 10_000, pattern="!" * 2_000),
            dict(task="rk", text="!", pattern="!" * 10_000),
        ]
        expected = [list(range(100_001)), [], list(range(8_001)), []]
        for answer, positions in zip(self.run_batch(requests), expected):
            self.assertEqual(answer["positions"], positions)

    def test_suffix_against_direct_oracle(self):
        texts = ["", "!", "aaaaa", "~! Ba", "banana", "abXabYcdZcd"]
        rng = random.Random(8)
        for _ in range(24):
            texts.append("".join(rng.choices("aA! ", k=rng.randrange(24))))
        answers = self.run_batch([dict(task="suffix", text=text) for text in texts])
        for text, answer in zip(texts, answers):
            with self.subTest(text=text):
                ordered = sorted(range(len(text)), key=lambda i: text[i:])
                lcp = [0] if text else []
                for left, right in zip(ordered, ordered[1:]):
                    lcp.append(direct_lcp(text[left:], text[right:]))
                self.assertEqual(answer["sa"], ordered)
                self.assertEqual(answer["lcp"], lcp)
                repeated = answer["repeated"]
                self.assertIsInstance(repeated, str)
                self.assertEqual(len(repeated), max(lcp, default=0))
                if repeated:
                    self.assertGreaterEqual(len(expected_positions(text, repeated)), 2)

    def test_suffix_at_limit(self):
        n = 50_000
        answer, = self.run_batch([dict(task="suffix", text="!" * n)])
        self.assertEqual(answer["sa"], list(range(n - 1, -1, -1)))
        self.assertEqual(answer["lcp"], list(range(n)))
        self.assertEqual(answer["repeated"], "!" * (n - 1))

    def test_aho_boundaries_suffixes_duplicates_and_reset(self):
        cases = [([], []), ([], ["", "ab", "ab"]), (["a"], []),
                 (["a", "aa", "a", "A!", "!"], ["aaa", "aaa", "", "A!A!"]),
                 (["ba", "aba", "a", "ba"], ["ababa", "", "ba", "ababa"]),
                 (["ab"], ["a", "b"])]
        rng = random.Random(9)
        for _ in range(20):
            patterns = ["".join(rng.choices("aA! ", k=rng.randrange(1, 6)))
                        for _ in range(rng.randrange(8))]
            texts = ["".join(rng.choices("aA! ", k=rng.randrange(30)))
                     for _ in range(rng.randrange(5))]
            cases.append((patterns, texts))
        requests = [dict(task="aho", patterns=p, texts=t) for p, t in cases]
        for (patterns, texts), answer in zip(cases, self.run_batch(requests)):
            expected = [[len(expected_positions(text, pattern)) for pattern in patterns]
                        for text in texts]
            self.assertEqual(answer["counts"], expected)

    def test_aho_at_limits(self):
        patterns = ["a" * length for length in range(1, 20)] * 500 + ["a" * 10] * 500
        text = "a" * 2_000
        long_pattern = "a" * 99_999 + "!"
        requests = [
            dict(task="aho", patterns=patterns, texts=[text] * 100),
            dict(task="aho", patterns=[long_pattern], texts=[long_pattern * 2, ""]),
        ]
        dense, deep = self.run_batch(requests)
        row = [len(text) - len(pattern) + 1 for pattern in patterns]
        self.assertEqual(dense["counts"], [row] * 100)
        self.assertEqual(deep["counts"], [[2], [0]])

    def test_repeated_mixed_jsonl_batch(self):
        requests = [
            dict(task="aho", patterns=["ab", "b", "ab"], texts=["abab", "", "abab"]),
            dict(task="lcs", a="a-b", b="ab"),
            dict(task="rk", text="abdj", pattern="ab"),
            dict(task="merge", sizes=[2, 3, 4]),
            dict(task="tree", n=3, weights=[4, 9, 6], edges=[[1, 0], [2, 1]]),
            dict(task="naive", text="aaa", pattern="aa"),
            dict(task="suffix", text="aba"),
            dict(task="kmp", text="abababa", pattern="aba"),
            dict(task="aho", patterns=["b"], texts=["a", "b", ""]),
        ]
        expected = [
            {"counts": [[2, 2, 2], [0, 0, 0], [2, 2, 2]]},
            {"length": 2, "sequence": "ab"},
            {"positions": [0]},
            {"cost": 14, "plan": [[0, 0, 1], [0, 1, 2]]},
            {"weight": 10, "selected": [0, 2]},
            {"positions": [0, 1]},
            {"sa": [2, 0, 1], "lcp": [0, 1, 0], "repeated": "a"},
            {"positions": [0, 2, 4]},
            {"counts": [[0], [1], [0]]},
        ]
        actual = self.run_batch(requests * 3)
        for request, answer, want in zip(requests * 3, actual, expected * 3):
            if request["task"] == "tree":
                self.check_tree(answer, request["weights"], request["edges"], want["weight"])
            else:
                for field, value in want.items():
                    self.assertEqual(answer[field], value)


if __name__ == "__main__":
    unittest.main()
