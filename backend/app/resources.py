"""What to study for each Codeforces tag, and advice for frequent verdicts.

The report shows these next to each weak topic. Every deep link below was checked to return
HTTP 200 with a page title matching the topic. CSES links point to the problem set home page,
and the title names the section to work through.
Sources: cp-algorithms.com, usaco.guide, the CSES Problem Set (cses.fi/problemset).
"""

CSES = "https://cses.fi/problemset/"
CP_ALGORITHMS = "https://cp-algorithms.com/"
USACO_GUIDE = "https://usaco.guide/"


def _cp(title: str, path: str) -> dict[str, str]:
    return {"title": f"CP-Algorithms: {title}", "url": CP_ALGORITHMS + path}


def _usaco(title: str, path: str) -> dict[str, str]:
    return {"title": f"USACO Guide: {title}", "url": USACO_GUIDE + path}


def _cses(section: str) -> dict[str, str]:
    return {"title": f"CSES Problem Set: {section} section", "url": CSES}


RESOURCES: dict[str, list[dict[str, str]]] = {
    "binary search": [
        _cp("Binary search", "num_methods/binary_search.html"),
        _usaco("Binary Search", "silver/binary-search"),
        _cses("Sorting and Searching"),
    ],
    "bitmasks": [
        _usaco("Intro to Bitwise Operators", "silver/intro-bitwise"),
        _cp("Bit manipulation", "algebra/bit-manipulation.html"),
        _cp("Enumerating submasks of a bitmask", "algebra/all-submasks.html"),
        _usaco("Bitmask DP", "gold/dp-bitmasks"),
    ],
    "brute force": [
        _usaco("Simulation", "bronze/simulation"),
        _cp("Enumerating submasks of a bitmask", "algebra/all-submasks.html"),
        _cses("Introductory Problems"),
    ],
    "combinatorics": [
        _cp("Binomial Coefficients", "combinatorics/binomial-coefficients.html"),
        _cp("The Inclusion-Exclusion Principle", "combinatorics/inclusion-exclusion.html"),
        _usaco("Modular Arithmetic", "gold/modular"),
        _cses("Mathematics"),
    ],
    "constructive algorithms": [
        _usaco("Ad Hoc Problems", "bronze/ad-hoc"),
        _cses("Introductory Problems"),
    ],
    "data structures": [
        _usaco("Point Update Range Sum", "gold/PURS"),
        _cp("Fenwick Tree", "data_structures/fenwick.html"),
        _cp("Segment Tree", "data_structures/segment_tree.html"),
        _cp("Sparse Table", "data_structures/sparse-table.html"),
        _cses("Range Queries"),
    ],
    "dfs and similar": [
        _usaco("Graph Traversal", "silver/graph-traversal"),
        _cp("Depth First Search", "graph/depth-first-search.html"),
        _cp("Topological Sorting", "graph/topological-sort.html"),
        _cses("Graph Algorithms"),
    ],
    "dp": [
        _cp("Introduction to Dynamic Programming", "dynamic_programming/intro-to-dp.html"),
        _usaco("Introduction to DP", "gold/intro-dp"),
        _cp("Knapsack Problem", "dynamic_programming/knapsack.html"),
        _cses("Dynamic Programming"),
    ],
    "dsu": [
        _cp("Disjoint Set Union", "data_structures/disjoint_set_union.html"),
        _usaco("Disjoint Set Union", "gold/dsu"),
        _cp("Minimum Spanning Tree - Kruskal with DSU", "graph/mst_kruskal_with_dsu.html"),
    ],
    "graphs": [
        _usaco("Introduction to Graphs", "bronze/intro-graphs"),
        _usaco("Graph Traversal", "silver/graph-traversal"),
        _cp("Breadth First Search", "graph/breadth-first-search.html"),
        _cses("Graph Algorithms"),
    ],
    "greedy": [
        _usaco("Introduction to Greedy Algorithms", "bronze/intro-greedy"),
        _usaco("Greedy Algorithms with Sorting", "silver/greedy-sorting"),
        _cses("Sorting and Searching"),
    ],
    "hashing": [
        _cp("String Hashing", "string/string-hashing.html"),
    ],
    "implementation": [
        _usaco("Simulation", "bronze/simulation"),
        _cses("Introductory Problems"),
    ],
    "math": [
        _cp("Binary Exponentiation", "algebra/binary-exp.html"),
        _usaco("Modular Arithmetic", "gold/modular"),
        _cp("Modular Inverse", "algebra/module-inverse.html"),
        _cses("Mathematics"),
    ],
    "number theory": [
        _usaco("Divisibility", "gold/divisibility"),
        _cp("Sieve of Eratosthenes", "algebra/sieve-of-eratosthenes.html"),
        _cp("Euclidean algorithm (GCD)", "algebra/euclid-algorithm.html"),
        _cp("Integer factorization", "algebra/factorization.html"),
    ],
    "shortest paths": [
        _usaco("Shortest Paths with Non-Negative Edge Weights", "gold/shortest-paths"),
        _cp("Dijkstra", "graph/dijkstra.html"),
        _cp("Bellman-Ford", "graph/bellman_ford.html"),
        _cp("Floyd-Warshall", "graph/all-pair-shortest-path-floyd-warshall.html"),
    ],
    "sortings": [
        _usaco("Introduction to Sorting", "bronze/intro-sorting"),
        _usaco("Custom Comparators and Coordinate Compression", "silver/sorting-custom"),
        _cses("Sorting and Searching"),
    ],
    "strings": [
        _cp("String Hashing", "string/string-hashing.html"),
        _cp("Prefix function (KMP)", "string/prefix-function.html"),
        _cp("Z-function", "string/z-function.html"),
        _cses("String Algorithms"),
    ],
    "trees": [
        _usaco("Introduction to Tree Algorithms", "silver/intro-tree"),
        _usaco("DP on Trees", "gold/dp-trees"),
        _cp("Lowest Common Ancestor", "graph/lca.html"),
        _cses("Tree Algorithms"),
    ],
    "two pointers": [
        _usaco("Two Pointers", "silver/two-pointers"),
        _usaco("Introduction to Prefix Sums", "silver/prefix-sums"),
        _cses("Sorting and Searching"),
    ],
}

# Shown for tags without a curated list above.
GENERAL_RESOURCES: list[dict[str, str]] = [
    {"title": "CP-Algorithms (search for the topic)", "url": CP_ALGORITHMS},
    {"title": "USACO Guide (modules by difficulty)", "url": USACO_GUIDE},
    {"title": "CSES Problem Set", "url": CSES},
]


def resources_for(tag: str) -> list[dict[str, str]]:
    return RESOURCES.get(tag, GENERAL_RESOURCES)


# Human-readable names for Codeforces verdicts.
VERDICT_LABELS: dict[str, str] = {
    "OK": "Accepted",
    "WRONG_ANSWER": "Wrong answer",
    "TIME_LIMIT_EXCEEDED": "Time limit exceeded",
    "MEMORY_LIMIT_EXCEEDED": "Memory limit exceeded",
    "RUNTIME_ERROR": "Runtime error",
    "COMPILATION_ERROR": "Compilation error",
    "IDLENESS_LIMIT_EXCEEDED": "Idleness limit exceeded",
    "CHALLENGED": "Hacked",
    "SKIPPED": "Skipped",
    "PRESENTATION_ERROR": "Presentation error",
    "PARTIAL": "Partial",
    "FAILED": "Judge failure",
    "CRASHED": "Crashed",
    "SECURITY_VIOLATED": "Security violated",
    "INPUT_PREPARATION_CRASHED": "Input preparation crashed",
    "REJECTED": "Rejected",
}


def verdict_label(verdict: str) -> str:
    return VERDICT_LABELS.get(verdict, verdict.replace("_", " ").capitalize())


# Advice for each frequent non-accepted verdict. The report shows it when a verdict makes up
# more than 15% of the user's failed submissions.
VERDICT_ADVICE: dict[str, str] = {
    "WRONG_ANSWER": (
        "Before submitting, test the edge cases (n = 1, all values equal, maximum values) and "
        "convince yourself the idea is correct; write a brute force to compare on small inputs."
    ),
    "TIME_LIMIT_EXCEEDED": (
        "Estimate the complexity from the constraints before coding: about 1e8 simple operations "
        "per second. Use fast I/O and avoid copying large containers inside loops."
    ),
    "MEMORY_LIMIT_EXCEEDED": (
        "Estimate memory before coding: an int array of 1e8 elements is 400 MB. Reuse arrays, "
        "and pass containers by reference instead of copying them."
    ),
    "RUNTIME_ERROR": (
        "Check array bounds, recursion depth, division by zero and empty containers; compile "
        "locally with sanitizers (-fsanitize=address,undefined) to find the line."
    ),
    "COMPILATION_ERROR": (
        "Compile locally with the same compiler and standard you pick on Codeforces before "
        "submitting, and double-check the selected language."
    ),
    "CHALLENGED": (
        "Your solution was hacked: think about worst-case inputs (overflow, anti-hash tests, "
        "slow cases for unordered_map) before locking a problem."
    ),
    "IDLENESS_LIMIT_EXCEEDED": (
        "In interactive problems, flush the output after every query and read exactly what the "
        "interactor sends."
    ),
}
