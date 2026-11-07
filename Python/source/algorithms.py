"""Implement algorithm bodies. See docs/guide/CONTRACTS.md; inputs and outputs are dictionaries."""
def lcs(request):
    """Find the length and a witness of a longest common subsequence."""
    a, b = request["a"], request["b"]
    if not a or not b:
        return {"length": 0, "sequence": ""}

    lengths = [[0] * (len(b) + 1) for _ in range(len(a) + 1)]
    for i, left in enumerate(a, 1):
        previous, current = lengths[i - 1], lengths[i]
        for j, right in enumerate(b, 1):
            if left == right:
                current[j] = previous[j - 1] + 1
            else:
                current[j] = max(previous[j], current[j - 1])

    i, j = len(a), len(b)
    sequence = []
    while i and j:
        if a[i - 1] == b[j - 1]:
            sequence.append(a[i - 1])
            i -= 1
            j -= 1
        elif lengths[i - 1][j] >= lengths[i][j - 1]:
            i -= 1
        else:
            j -= 1
    sequence.reverse()
    return {"length": lengths[-1][-1], "sequence": "".join(sequence)}


def merge(request):
    """Minimize adjacent merge costs and return a chronological plan."""
    sizes = request["sizes"]
    n = len(sizes)
    if n <= 1:
        return {"cost": 0, "plan": []}

    prefix = [0]
    for size in sizes:
        prefix.append(prefix[-1] + size)

    costs = [[0] * n for _ in range(n)]
    splits = [[0] * n for _ in range(n)]
    for width in range(2, n + 1):
        for left in range(n - width + 1):
            right = left + width - 1
            best_split = left
            best_cost = costs[left + 1][right]
            for split in range(left + 1, right):
                subcost = costs[left][split] + costs[split + 1][right]
                if subcost < best_cost:
                    best_cost = subcost
                    best_split = split
            costs[left][right] = best_cost + prefix[right + 1] - prefix[left]
            splits[left][right] = best_split

    plan = []

    def emit(left, right):
        if left == right:
            return
        split = splits[left][right]
        emit(left, split)
        emit(split + 1, right)
        plan.append([left, split, right])

    emit(0, n - 1)
    return {"cost": costs[0][-1], "plan": plan}


def tree(request):
    """Find a maximum-weight independent set of an undirected tree."""
    n = request["n"]
    if n == 0:
        return {"weight": 0, "selected": []}

    neighbors = [[] for _ in range(n)]
    for u, v in request["edges"]:
        neighbors[u].append(v)
        neighbors[v].append(u)

    parent = [-1] * n
    order = [0]
    # Append children so each parent precedes them in the traversal.
    for vertex in order:
        for neighbor in neighbors[vertex]:
            if neighbor != parent[vertex]:
                parent[neighbor] = vertex
                order.append(neighbor)

    take = request["weights"].copy()
    skip = [0] * n
    for index in range(n - 1, 0, -1):
        vertex = order[index]
        ancestor = parent[vertex]
        take[ancestor] += skip[vertex]
        skip[ancestor] += max(take[vertex], skip[vertex])

    chosen = bytearray(n)
    selected = []
    for vertex in order:
        ancestor = parent[vertex]
        if (ancestor == -1 or not chosen[ancestor]) and take[vertex] > skip[vertex]:
            chosen[vertex] = 1
            selected.append(vertex)
    return {"weight": max(take[0], skip[0]), "selected": selected}



def _window_matches(text, pattern, start):
    for offset, character in enumerate(pattern):
        if text[start + offset] != character:
            return False
    return True


def naive(request):
    """Test every possible start by comparing characters."""
    text = request["text"]
    pattern = request["pattern"]
    if not pattern:
        return {"positions": list(range(len(text) + 1))}

    positions = []
    for start in range(len(text) - len(pattern) + 1):
        if _window_matches(text, pattern, start):
            positions.append(start)
    return {"positions": positions}


def kmp(request):
    """Search using the longest proper border of each pattern prefix."""
    text = request["text"]
    pattern = request["pattern"]
    length = len(pattern)
    if length == 0:
        return {"positions": list(range(len(text) + 1))}
    if length > len(text):
        return {"positions": []}

    prefix = [0] * length
    matched = 0
    for index in range(1, length):
        character = pattern[index]
        while matched and character != pattern[matched]:
            matched = prefix[matched - 1]
        if character == pattern[matched]:
            matched += 1
        prefix[index] = matched

    positions = []
    matched = 0
    for index, character in enumerate(text):
        while matched and character != pattern[matched]:
            matched = prefix[matched - 1]
        if character == pattern[matched]:
            matched += 1
        if matched == length:
            positions.append(index - length + 1)
            matched = prefix[matched - 1]
    return {"positions": positions}


def rk(request):
    """Use a rolling hash to filter windows before exact comparison."""
    text = request["text"]
    pattern = request["pattern"]
    length = len(pattern)
    if length == 0:
        return {"positions": list(range(len(text) + 1))}
    if length > len(text):
        return {"positions": []}

    base, modulus = 31, 101
    highest_power = pow(base, length - 1, modulus)
    pattern_hash = window_hash = 0
    for index, character in enumerate(pattern):
        pattern_hash = (pattern_hash * base + ord(character)) % modulus
        window_hash = (window_hash * base + ord(text[index])) % modulus

    positions = []
    last_start = len(text) - length
    for start in range(last_start + 1):
        if window_hash == pattern_hash and _window_matches(text, pattern, start):
            positions.append(start)
        if start < last_start:
            remainder = window_hash - ord(text[start]) * highest_power
            window_hash = (remainder * base + ord(text[start + length])) % modulus
    return {"positions": positions}


def suffix(request):
    """Build the suffix order by doubling and adjacent LCPs with Kasai."""
    text = request["text"]
    size = len(text)
    if size == 0:
        return {"sa": [], "lcp": [], "repeated": ""}

    order = list(range(size))
    ranks = [ord(character) for character in text]
    width = 1
    while width < size:
        pairs = [
            (ranks[start], ranks[start + width] if start + width < size else -1)
            for start in range(size)
        ]
        order.sort(key=pairs.__getitem__)
        ranks = [0] * size
        rank = 0
        for index in range(1, size):
            previous, current = order[index - 1], order[index]
            if pairs[previous] != pairs[current]:
                rank += 1
            ranks[current] = rank
        if rank == size - 1:
            break
        width *= 2

    inverse_order = [0] * size
    for index, start in enumerate(order):
        inverse_order[start] = index

    lcp = [0] * size
    common = 0
    for start, rank in enumerate(inverse_order):
        if rank == 0:
            common = 0
            continue
        previous = order[rank - 1]
        while (
            start + common < size
            and previous + common < size
            and text[start + common] == text[previous + common]
        ):
            common += 1
        lcp[rank] = common
        common = max(0, common - 1)

    best_rank = max(range(size), key=lcp.__getitem__)
    repeat_start = order[best_rank]
    return {
        "sa": order,
        "lcp": lcp,
        "repeated": text[repeat_start:repeat_start + lcp[best_rank]],
    }


def aho(request):
    """Count dictionary matches with trie transitions and failure links."""
    patterns = request["patterns"]
    texts = request["texts"]
    if not texts:
        return {"counts": []}
    if not patterns:
        return {"counts": [[] for _ in texts]}

    transitions = [{}]
    terminals = []
    for pattern in patterns:
        state = 0
        for character in pattern:
            child = transitions[state].get(character)
            if child is None:
                child = len(transitions)
                transitions[state][character] = child
                transitions.append({})
            state = child
        terminals.append(state)

    failure = [0] * len(transitions)
    # Appending children to the end makes this list a breadth-first queue.
    breadth_first = list(transitions[0].values())
    for state in breadth_first:
        for character, child in transitions[state].items():
            fallback = failure[state]
            while fallback and character not in transitions[fallback]:
                fallback = failure[fallback]
            failure[child] = transitions[fallback].get(character, 0)
            breadth_first.append(child)

    counts = []
    for text in texts:
        if not text:
            counts.append([0] * len(patterns))
            continue
        state = 0
        visits = [0] * len(transitions)
        for character in text:
            while state and character not in transitions[state]:
                state = failure[state]
            state = transitions[state].get(character, 0)
            visits[state] += 1
        for state in reversed(breadth_first):
            visits[failure[state]] += visits[state]
        counts.append([visits[state] for state in terminals])
    return {"counts": counts}
