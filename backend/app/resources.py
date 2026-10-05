"""What to study for each Codeforces tag.

The report shows these next to each weak topic. Two entries are filled in as examples;
add the tags that show up most in your target range (check the links open before adding).
Good sources: cp-algorithms.com, usaco.guide, the CSES Problem Set (cses.fi/problemset).
"""

RESOURCES: dict[str, list[dict[str, str]]] = {
    "binary search": [
        {"title": "CP-Algorithms: Binary search",
         "url": "https://cp-algorithms.com/num_methods/binary_search.html"},
    ],
    "dsu": [
        {"title": "CP-Algorithms: Disjoint Set Union",
         "url": "https://cp-algorithms.com/data_structures/disjoint_set_union.html"},
    ],
    # TODO: "dp", "graphs", "greedy", "math", "number theory", "strings", "trees", ...
}


# Advice for each frequent non-accepted verdict. Used when a verdict is a large share of
# the user's submissions. Rewrite these in your own words.
VERDICT_ADVICE: dict[str, str] = {
    "WRONG_ANSWER": "Test edge cases (n = 1, all equal, maximum values) and prove the idea before coding.",
    "TIME_LIMIT_EXCEEDED": "Estimate complexity from the constraints before coding; about 1e8 simple operations per second.",
    "RUNTIME_ERROR": "Check array bounds, recursion depth and division by zero.",
    "MEMORY_LIMIT_EXCEEDED": "Estimate memory: an int array of 1e8 is 400 MB; reuse arrays instead of copying.",
}
