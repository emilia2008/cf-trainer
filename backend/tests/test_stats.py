from app.stats import TagStat, recommend, solved_problems, tag_stats, weakest_tags


def sub(contest, index, verdict, tags, rating=None):
    problem = {"contestId": contest, "index": index, "tags": tags}
    if rating is not None:
        problem["rating"] = rating
    return {"verdict": verdict, "creationTimeSeconds": 0, "problem": problem}


SUBMISSIONS = [
    sub(1, "A", "OK", ["math"], 800),
    sub(1, "A", "OK", ["math"], 800),               # accepted twice: count once
    sub(2, "B", "WRONG_ANSWER", ["graphs"], 1400),
    sub(2, "B", "OK", ["graphs"], 1400),
    sub(3, "C", "WRONG_ANSWER", ["graphs", "dp"], 1600),
    sub(4, "D", "TIME_LIMIT_EXCEEDED", ["dp"], 1500),
    sub(5, "E", "OK", ["math", "greedy"]),          # no rating
]


def test_solved_problems_counts_each_problem_once():
    solved = solved_problems(SUBMISSIONS)
    assert set(solved) == {"1A", "2B", "5E"}


def test_tag_stats():
    stats = {s.tag: s for s in tag_stats(SUBMISSIONS)}
    assert stats["math"] == TagStat("math", solved=2, attempted=2, avg_rating=800.0)
    assert stats["graphs"] == TagStat("graphs", solved=1, attempted=2, avg_rating=1400.0)
    assert stats["dp"] == TagStat("dp", solved=0, attempted=2, avg_rating=0.0)
    assert stats["greedy"] == TagStat("greedy", solved=1, attempted=1, avg_rating=0.0)


def test_tag_stats_sorted_by_solved_then_name():
    tags = [s.tag for s in tag_stats(SUBMISSIONS)]
    assert tags == ["math", "graphs", "greedy", "dp"]


def test_weakest_tags():
    assert weakest_tags(tag_stats(SUBMISSIONS), k=2) == ["dp", "graphs"]


def test_recommend_filters_and_sorts():
    problems = [
        {"contestId": 10, "index": "A", "rating": 1500, "tags": ["dp"]},
        {"contestId": 10, "index": "B", "rating": 1300, "tags": ["dp", "math"]},
        {"contestId": 10, "index": "C", "rating": 2000, "tags": ["dp"]},      # too hard
        {"contestId": 10, "index": "D", "rating": 1400, "tags": ["strings"]},  # not a weak tag
        {"contestId": 2, "index": "B", "rating": 1400, "tags": ["graphs"]},   # already solved
        {"contestId": 10, "index": "E", "tags": ["dp"]},                      # no rating
    ]
    result = recommend(problems, solved_keys={"2B"}, weak_tags=["dp", "graphs"],
                       user_rating=1400, limit=5)
    assert [f"{p['contestId']}{p['index']}" for p in result] == ["10B", "10A"]


def test_recommend_unrated_user_starts_at_800():
    problems = [
        {"contestId": 1, "index": "A", "rating": 800, "tags": ["dp"]},
        {"contestId": 1, "index": "B", "rating": 1200, "tags": ["dp"]},
    ]
    result = recommend(problems, set(), ["dp"], user_rating=None, limit=5)
    assert [p["index"] for p in result] == ["A"]
