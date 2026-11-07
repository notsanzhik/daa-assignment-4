# Assignment 4 analysis

## Environment and commands

The selected language is Python. The local runs used CPython 3.12.10 on Windows 11 Pro (build 26200), an Intel Core i5-12450HX, and 15.7 GiB of installed RAM. The solution uses the standard library. The starter entry point processes one UTF-8 JSON request per line and returns one JSON result per line.

From the repository root:

```text
python tools/run.py --setup
python tools/run.py --check
python -m unittest discover -s tests/student -v
python tests/student/benchmark_search.py
```

The setup command launched the selected solution and passed the ping check. The public checker passed all 44 cases and two complete batches in one process. The student suite passed all 14 tests in 4.147 seconds. For a manual run against a JSON Lines input file, use `python tools/run.py --input path/to/requests.jsonl`. The benchmark imports the three search functions directly.

## Algorithms

### Longest common subsequence (`lcs`)

`lengths[i][j]` is the optimal length for the first `i` characters of `a` and the first `j` of `b`. An empty prefix has length zero. When the last characters match, appending that character to an optimal solution for the two shorter prefixes attains the optimum. An optimum must use at least one of the matching end positions, since otherwise it could be extended by their common character. Move the matching occurrence in the other string to its end to realize the diagonal case. With different last characters, at least one last position must be unused. The larger of the cells above and to the left therefore gives the optimum. Row-major order has all three predecessors ready.

Reconstruction moves diagonally on a match and records the character. On a mismatch it moves to a predecessor with the current optimal length, preferring to discard from `a` on a tie. Reversing the recorded characters produces a valid optimum. For nonempty inputs of lengths `a_len` and `b_len`, the time and auxiliary space are O(a_len × b_len), with O(L) output for an optimum of length L. The empty case returns immediately. The `a!b?c` / `abc` test detects code that requires a contiguous substring, and `abc` / `bac` admits both `ac` and `bc`.

### Ordered adjacent-block merging (`merge`)

`costs[left][right]` is the minimum cost of reducing the closed interval to one block. A single block needs zero work. The last merge across a split `k` combines `[left,k]` and `[k+1,right]`. Adjacency forces those two intervals, and their optimal subplans can run independently. Take the minimum sum of their costs and add the interval sum `prefix[right+1] - prefix[left]`. Increasing interval width ensures that both child costs are ready. Zero or one block returns an empty plan and cost zero.

The split table retains the first minimum. A postorder walk emits the left plan, right plan and then `[left,k,right]`, so both operands exist when each merge is executed. There are O(n²) intervals and O(n) candidate splits per interval. Time is O(n³), auxiliary space O(n²) including the reconstruction stack, and the plan has n−1 records for n≥1. The test `[1,9,1]` expects cost 21 and replays the plan, catching an illegal merge of the two outer blocks. The all-zero case exercises ties.

### Maximum-weight independent set (`tree`)

Root the tree at 0. A parent-first traversal records every parent, then reverse order computes optimal subtree weights. At each vertex, `take` starts at its weight and adds `skip` from each child, since an included parent excludes its children. `skip` starts at zero and adds the larger child state independently for each child. Leaves consequently have states `weight` and zero. These choices exhaust the valid sets because edges between child subtrees do not exist. The maximum of the root states is the answer, and the empty tree has weight zero.

A parent-first pass selects a vertex only when its parent is skipped and taking it improves the subtree optimum. Skipping wins ties. This realizes the states used by the recurrence and yields distinct nonadjacent vertices. The traversals are iterative and process each edge a constant number of times. Time and auxiliary space are O(n+1), and output contains k selected vertices. The 100,000-vertex path catches depth-dependent recursion failures and sums that exceed 32-bit range. All-negative weights exercise the empty optimum.

### Naive search (`naive`)

At every start from 0 through n−m, compare characters in order until a mismatch or until all m agree. Before comparing offset j, offsets below j agree, so a completed window is exactly a match. Each candidate is visited in increasing order, including overlapping starts. An empty pattern returns every boundary from 0 through n, and a longer pattern yields an empty list. For 1≤m≤n, worst-case time is O((n−m+1)m), with O(1) auxiliary space plus O(z) output for z positions. Empty patterns take O(n+1) to emit their output. The `aaaaa` / `aaa` test expects positions 0, 1 and 2 and catches a search that skips overlaps.

### Knuth–Morris–Pratt (`kmp`)

`prefix[i]` stores the longest proper border of `pattern[:i+1]`. Build it left to right, starting at length zero. On a mismatch, the next candidate is the longest border of the previously matched prefix, obtained from the already computed table. During search, `matched` is the longest available pattern prefix that is a suffix of the processed text. A mismatch eliminates the current length and follows border links to the next possible length. A successful comparison extends the current border by one. A full match emits its start and falls back to the longest proper border, preserving the suffix needed for overlaps.

Each fallback decreases the matched length, and each processed character can increase it by at most one. Time is O(n+m+z+1) and auxiliary space is O(m+1), plus O(z) output. Empty patterns return all n+1 boundaries. A pattern longer than the text returns immediately. Repetitive text with a pattern ending in a distinct character exercises long border chains, and the overlap cases verify fallback after a hit.

### Exact Rabin–Karp (`rk`)

Use a polynomial hash over character codes with base 31 and modulus 101. Initialize the pattern hash and the first window in left-to-right order. The loop invariant is that the current hash represents the length-m window at the current start. Removing the outgoing code times 31^(m−1), multiplying by 31 and adding the incoming code produces the next window's polynomial. Python's remainder with positive modulus normalizes negative intermediate results.

Equal strings have equal hashes. Every equal-hash candidate is compared character by character before its start is emitted, which rejects collisions and keeps overlapping matches. Empty and longer patterns use the same result conventions as KMP. For 1≤m≤n and c equal-hash candidates, time is O(n+m+c·m) and auxiliary space is O(1) beyond the z output positions. In the worst case every window is a candidate. Under this hash, `ab` and `dj` both hash to 75, so searching `djdjabdjdjab` for `ab` must report only the actual matches. The student suite also checks a rolling step with a negative intermediate value.

### Suffix array and Kasai LCP (`suffix`)

In the doubling step, ranks represent the ordered equivalence classes of prefixes of length `width`. Initially character codes give the one-character order. Sorting indices by their two consecutive ranks orders prefixes of length `2*width`. The second rank is −1 when it would start beyond the end, so a shorter prefix precedes an extension. Assign equal pairs the same new rank and double the width. When ranks are all distinct, the order is already final. Otherwise the process reaches full suffix lengths. Only original text indices appear in the array. Python's comparison sort takes O(n log(n+1)) worst-case time per round, so doubling takes O(n log²(n+1)) time and O(n+1) auxiliary space.

Kasai inverts the suffix array so `rank[start]` gives the suffix's position. Process suffixes in increasing text-start order. Each `lcp[r]` is the common prefix with the suffix at rank `r−1`, with zero at rank zero. After a common prefix of length h, shifting each suffix by one preserves at least h−1 characters. Their order is preserved when both start with the same removed character, and the new immediate predecessor shares at least that prefix because suffixes with a common prefix occupy a contiguous rank range. Thus the next comparison can start at max(h−1,0). Rank zero resets the bound. Increments amortize over the text, so Kasai takes O(n+1) time and O(n+1) auxiliary space.

Any substring shared by two suffixes occurs in an interval of suffix ranks, so some adjacent pair shares it. The largest LCP therefore gives an optimal repeat. The first maximum in suffix order breaks ties, with overlap allowed. The two arrays and repeat together use O(n+1) output space. Empty input returns two empty arrays and an empty repeat. The all-equal input of length 50,000 checks short-to-long ordering, overlaps and linear LCP construction. Small cases compare order and LCP with direct suffix comparisons.

### Aho–Corasick (`aho`)

A state represents a trie prefix. A failure link points to its longest proper suffix that is also a trie prefix. A breadth-first pass starts with the root children, whose failure is the root. For each other edge, extend the parent's longest available suffix by its character, following already built failure links when necessary. Shorter states are ready before longer ones. Scanning each text uses the same fallback rule, so the current state represents the longest trie prefix ending at the current character.

Count visits to the current state for each character. In reverse breadth-first order, add each state's visits to its failure state. Every shorter terminal suffix then receives one contribution for each end position where its pattern occurs, including overlaps. One terminal index per dictionary entry preserves input order and gives duplicate entries identical counts. Reset state and visit counts for each text. An empty dictionary yields an empty row per text, an empty text yields zeros, and no texts yields no rows.

Let L be the total dictionary length, S the number of trie states, p the number of entries, T the total text length and q the number of texts. Sparse dictionary lookups take expected constant time. The total construction time is O(L+S+p+1). To bound construction fallbacks, follow a dictionary pattern from the root and consider the depth of the failure target after each edge. Each extension increases that depth by at most one, and each failed lookup lowers it. Summing over all pattern paths bounds the work over the distinct trie edges. Each scan amortizes its fallback steps in the same way. Scans and propagation cost O(T+q(S+p+1)) as an upper bound. Auxiliary memory is O(S+p+1), with O(q(p+1)) for the output rows. The `a`, `aa`, `a` dictionary on `aaa` produces 3, 2, 3, and repeated texts exercise independent counts.

## Student tests

All cases below are executable in `tests/student/test_assignment.py`. Run the full suite with the command above or add `-k <name fragment>` to select tests.

| Command | Fixture or method fragment | Expected and observed | Checks |
|---|---|---|---|
| LCS | `lcs_small`, `lcs_at_limit` | Passed exhaustive small oracle and witness checks. Alternating 1,000-character inputs produced length 999. | Empty inputs, ties, subsequence order, scale |
| Merge | `merge_small`, `merge_at_limit` | Passed brute-force comparison and chronological replay. 200 blocks of 10⁹ each cost 1,544,000,000,000. | Adjacency, valid plan, zero sizes, large totals |
| Tree | `tree_small`, `tree_deep` | Passed subset oracle and witness checks. The 100,000-vertex path optimum was 50,000,000,000,000. | Negative and zero weights, ties, deep tree, large sums |
| Naive, KMP, RK | `search_common`, `search_at_larger` | Passed direct-start oracle on all cases, including larger KMP and RK inputs. | Empty patterns, overlapping hits, case and punctuation, limits |
| RK | `rk_collisions` | Passed the `ab` / `dj` collision and a negative rolling update. | Exact candidate verification and normalized remainder |
| Suffix | `suffix_against`, `suffix_at_limit` | Passed direct suffix and LCP comparisons, tied repeat witnesses and the 50,000-character uniform case. | Permutation, order, LCP, repeats and scale |
| Aho | `aho_boundaries`, `aho_at_limits` | Passed independent count oracle, a 100,000-character pattern and a 10,000-column result across 100 texts. | Empty inputs, suffix counts, duplicates, overlap and reset |
| JSON Lines | `repeated_mixed_jsonl_batch` | Passed 27 requests in one process with the expected results in order. | Entry point, mixed commands and independence across requests |

## Search comparison

Run `python tests/student/benchmark_search.py`. For each n and m, the random case uses a fresh `random.Random(2026+n)` to sample text uniformly from `abcd`, then chooses a uniformly sampled valid start and uses that text slice as the pattern. The repetitive case uses `a` repeated n−1 times then `b`, and its length-m suffix as the pattern. Each of the three implementations receives the same request. A separate `startswith` loop checks every returned position. All six inputs had one match.

Each algorithm was called once per input for untimed verification and warm-up, then measured three times in round-robin order. CPython ran without a JIT. The timer measured each full function call, including pattern preprocessing and output construction. Input generation, interpreter startup, imports and correctness checks were outside the measured region. Times below are in milliseconds.

| Case | n | m | Seed | Algorithm | Run 1 | Run 2 | Run 3 | Median | Output verified |
|---|---:|---:|---:|---|---:|---:|---:|---:|---|
| Random | 500 | 50 | 2526 | Naive | 0.0929 | 0.0935 | 0.0984 | 0.0935 | Yes |
| Random | 500 | 50 | 2526 | KMP | 0.0405 | 0.0432 | 0.0350 | 0.0405 | Yes |
| Random | 500 | 50 | 2526 | RK | 0.0993 | 0.0911 | 0.1002 | 0.0993 | Yes |
| Repetitive | 500 | 50 | — | Naive | 1.1579 | 1.2011 | 1.2038 | 1.2011 | Yes |
| Repetitive | 500 | 50 | — | KMP | 0.0683 | 0.0610 | 0.0626 | 0.0626 | Yes |
| Repetitive | 500 | 50 | — | RK | 0.0846 | 0.0891 | 0.1013 | 0.0891 | Yes |
| Random | 1500 | 150 | 3526 | Naive | 0.3697 | 0.4199 | 0.3844 | 0.3844 | Yes |
| Random | 1500 | 150 | 3526 | KMP | 0.2007 | 0.1678 | 0.1745 | 0.1745 | Yes |
| Random | 1500 | 150 | 3526 | RK | 0.4040 | 0.4030 | 0.3547 | 0.4030 | Yes |
| Repetitive | 1500 | 150 | — | Naive | 16.1010 | 13.8051 | 12.4350 | 13.8051 | Yes |
| Repetitive | 1500 | 150 | — | KMP | 0.2187 | 0.2836 | 0.1859 | 0.2187 | Yes |
| Repetitive | 1500 | 150 | — | RK | 0.3747 | 0.3717 | 0.2113 | 0.3717 | Yes |
| Random | 3000 | 300 | 5026 | Naive | 0.5989 | 0.6820 | 0.9021 | 0.6820 | Yes |
| Random | 3000 | 300 | 5026 | KMP | 0.3716 | 0.2844 | 0.2878 | 0.2878 | Yes |
| Random | 3000 | 300 | 5026 | RK | 0.7616 | 0.7146 | 0.5612 | 0.7146 | Yes |
| Repetitive | 3000 | 300 | — | Naive | 43.1954 | 42.4689 | 39.5320 | 42.4689 | Yes |
| Repetitive | 3000 | 300 | — | KMP | 0.3974 | 0.3788 | 0.7062 | 0.3974 | Yes |
| Repetitive | 3000 | 300 | — | RK | 0.4452 | 0.4385 | 0.8106 | 0.4452 | Yes |

Naive search rejects most random windows early. On the repetitive inputs, the first differing character occurs at the end of each unsuccessful window, and the largest median rose from 0.6820 ms on random text to 42.4689 ms on repetitive text. KMP reused prefix matches and had the lowest median in all six cases. RK hashes separated the repeated all-`a` windows from the ending-`b` pattern, so it verified only the true candidate on those inputs. Modulus 101 allows many different windows to share a hash. More such windows would raise the verification cost, as the separate collision test illustrates. These measurements describe the six benchmark inputs. The bounds above follow from the operations of each algorithm.

## Sources and AI assistance

- The [official Assignment 4 template](https://github.com/RZhaniya/daa-assignment-4-archive) supplied the starter interface, [contracts](docs/guide/CONTRACTS.md), [algorithm notes](docs/LECTURE_CLARIFICATIONS_EN_RU.md), public fixtures, and the analysis and benchmark requirements.
- OpenAI Codex generated the Python implementations, student tests, benchmark and this analysis. Codex verified the result by running the template checks, the student suite with independent small-input oracles and boundary cases, and the benchmark with an independent match check. The results above are from those runs.
