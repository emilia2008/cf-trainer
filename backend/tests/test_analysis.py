import pytest

from app.analysis import (
    BucketStat,
    RankInfo,
    RatingTrend,
    TagStat,
    VerdictStats,
    comfort_rating,
    contest_level,
    difficulty_profile,
    rank_info,
    rating_trend,
    recommend,
    solved_problems,
    tag_importance,
    tag_stats,
    target_range,
    upsolve_list,
    verdict_breakdown,
    weak_topics,
)


def sub(contest, index, verdict, tags, rating=None, t=0, live=False):
    problem = {"contestId": contest, "index": index, "tags": tags}
    if rating is not None:
        problem["rating"] = rating
    return {
        "verdict": verdict,
        "creationTimeSeconds": t,
        "author": {"participantType": "CONTESTANT" if live else "PRACTICE"},
        "problem": problem,
    }


# Newest first, like the real API.
SUBMISSIONS = [
    sub(5, "E", "OK", ["math", "greedy"], t=90),                        # no rating
    sub(4, "D", "TIME_LIMIT_EXCEEDED", ["dp"], 1500, t=80, live=True),  # never solved, live
    sub(3, "C", "WRONG_ANSWER", ["graphs", "dp"], 1600, t=70, live=True),  # never solved, live
    sub(2, "B", "OK", ["graphs"], 1400, t=60, live=True),
    sub(2, "B", "WRONG_ANSWER", ["graphs"], 1400, t=50, live=True),
    sub(1, "A", "OK", ["math"], 800, t=40),                             # accepted twice
    sub(1, "A", "OK", ["math"], 800, t=30, live=True),
    sub(6, "A", "OK", ["implementation", "*special"], 800, t=20, live=True),
    sub(6, "B", "COMPILATION_ERROR", ["greedy"], 1000, t=10, live=True),  # never solved, live
]


# ---- Overview -------------------------------------------------------------------

@pytest.mark.parametrize(
    "rating, expected",
    [
        (1350, RankInfo("Pupil", "Specialist", 1400, 50)),
        (1900, RankInfo("Candidate Master", "Master", 2100, 200)),
        (None, RankInfo("Newbie", "Pupil", 1200, 1200)),
        (3100, RankInfo("Legendary Grandmaster", None, None, None)),
    ],
)
def test_rank_info(rating, expected):
    assert rank_info(rating) == expected


def test_solved_problems_counts_each_problem_once():
    assert set(solved_problems(SUBMISSIONS)) == {"5E", "2B", "1A", "6A"}


def test_rating_trend():
    history = [
        {"oldRating": 0, "newRating": 400},
        {"oldRating": 400, "newRating": 700},
        {"oldRating": 700, "newRating": 650},
        {"oldRating": 650, "newRating": 900},
    ]
    assert rating_trend(history, last_n=2) == RatingTrend(
        contests=4, current=900, max_rating=900, recent_change=200,
        best_gain=400, worst_drop=-50,
    )


def test_rating_trend_empty():
    assert rating_trend([]) == RatingTrend(0, None, None, 0, None, None)


# ---- Difficulty -----------------------------------------------------------------

def test_difficulty_profile():
    assert difficulty_profile(SUBMISSIONS) == [
        BucketStat(800, solved=2, attempted=2),
        BucketStat(1000, solved=0, attempted=1),
        BucketStat(1400, solved=1, attempted=1),
        BucketStat(1500, solved=0, attempted=1),
        BucketStat(1600, solved=0, attempted=1),
    ]


def test_comfort_rating():
    profile = [BucketStat(800, 5, 5), BucketStat(900, 3, 4), BucketStat(1000, 2, 6)]
    assert comfort_rating(profile, min_solved=3) == 900
    assert comfort_rating(profile, min_solved=6) is None


@pytest.mark.parametrize(
    "rating, comfort, expected",
    [
        (1350, 1200, (1400, 1600)),
        (None, None, (900, 1100)),
        (1200, 1500, (1600, 1800)),
    ],
)
def test_target_range(rating, comfort, expected):
    assert target_range(rating, comfort) == expected


# ---- Topics ---------------------------------------------------------------------

def test_tag_stats():
    stats = {s.tag: s for s in tag_stats(SUBMISSIONS)}
    assert "*special" not in stats
    assert stats["math"] == TagStat("math", solved=2, attempted=2, first_try_rate=1.0,
                                    max_solved_rating=800)
    # 2B was wrong first, then accepted.
    assert stats["graphs"] == TagStat("graphs", solved=1, attempted=2, first_try_rate=0.0,
                                      max_solved_rating=1400)
    assert stats["dp"] == TagStat("dp", solved=0, attempted=2, first_try_rate=0.0,
                                  max_solved_rating=None)
    # 5E has no rating, 6B is unsolved.
    assert stats["greedy"] == TagStat("greedy", solved=1, attempted=2, first_try_rate=1.0,
                                      max_solved_rating=None)


def test_tag_stats_sorted_by_solved_then_name():
    tags = [s.tag for s in tag_stats(SUBMISSIONS)]
    assert tags == ["math", "graphs", "greedy", "implementation", "dp"]


PROBLEMS = [
    {"contestId": 10, "index": "A", "rating": 1400, "tags": ["dp", "math"], "solvedCount": 500},
    {"contestId": 10, "index": "B", "rating": 1500, "tags": ["dp"], "solvedCount": 900},
    {"contestId": 10, "index": "C", "rating": 1500, "tags": ["graphs", "dp"], "solvedCount": 100},
    {"contestId": 2, "index": "B", "rating": 1400, "tags": ["graphs"], "solvedCount": 8000},
    {"contestId": 10, "index": "D", "rating": 2000, "tags": ["dp"], "solvedCount": 50},
    {"contestId": 10, "index": "E", "tags": ["dp"]},
    {"contestId": 10, "index": "F", "rating": 1450, "tags": ["*special", "dp"], "solvedCount": 1},
]


def test_tag_importance():
    importance = tag_importance(PROBLEMS, 1400, 1600)
    # 5 rated problems in range: 10A, 10B, 10C, 2B, 10F
    assert importance == pytest.approx({"dp": 4 / 5, "math": 1 / 5, "graphs": 2 / 5})


def test_tag_importance_empty_range():
    assert tag_importance(PROBLEMS, 3000, 3500) == {}


def test_weak_topics():
    result = weak_topics(SUBMISSIONS, PROBLEMS, 1400, 1600, k=2)
    # dp: 0.8 / (1+0) = 0.8; graphs: 0.4 / (1+1) = 0.2 (solved 2B); math: 0.2 / 1 = 0.2
    assert [w.tag for w in result] == ["dp", "graphs"]
    assert result[0].score == pytest.approx(0.8)
    assert result[1].solved_in_range == 1


def test_weak_topics_min_importance():
    tags = [w.tag for w in weak_topics(SUBMISSIONS, PROBLEMS, 1400, 1600, k=5, min_importance=0.3)]
    assert tags == ["dp", "graphs"]


# ---- Habits ---------------------------------------------------------------------

def test_verdict_breakdown():
    subs = SUBMISSIONS + [{"verdict": "TESTING", "creationTimeSeconds": 99, "problem": {}}]
    assert verdict_breakdown(subs) == VerdictStats(
        total_submissions=9,
        accepted=5,
        by_verdict={"TIME_LIMIT_EXCEEDED": 1, "WRONG_ANSWER": 2, "COMPILATION_ERROR": 1},
        first_try_rate=pytest.approx(3 / 4),
    )


def test_contest_level():
    # Live contests: 1, 2, 3, 4, 6 (5 contests). Solved live: 1A, 2B, 6A.
    assert contest_level(SUBMISSIONS) == pytest.approx({"A": 2 / 5, "B": 1 / 5})


def test_contest_level_no_live_contests():
    assert contest_level([sub(1, "A", "OK", [], 800)]) == {}


def test_upsolve_list():
    keys = [f"{p['contestId']}{p['index']}" for p in upsolve_list(SUBMISSIONS)]
    assert keys == ["6B", "4D", "3C"]


# ---- Recommendations ------------------------------------------------------------

def test_recommend():
    result = recommend(PROBLEMS, solved_keys={"2B"}, weak_tags=["dp", "graphs"],
                       lo=1400, hi=1600, limit=3)
    keys = [f"{p['contestId']}{p['index']}" for p in result]
    # 10C matches 2 weak tags, so it comes first. Then 1 match each, easiest first:
    # 10A (1400), 10F (1450), 10B (1500) -> limit 3 drops 10B.
    # Excluded: 2B (solved), 10D (out of range), 10E (no rating).
    assert keys == ["10C", "10A", "10F"]


def test_recommend_tie_breaks_by_solved_count():
    problems = [
        {"contestId": 1, "index": "A", "rating": 1200, "tags": ["dp"], "solvedCount": 10},
        {"contestId": 1, "index": "B", "rating": 1200, "tags": ["dp"], "solvedCount": 99},
    ]
    result = recommend(problems, set(), ["dp"], 1100, 1300)
    assert [p["index"] for p in result] == ["B", "A"]
