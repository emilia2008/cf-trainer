"""Edge cases on top of the specification in test_analysis.py."""

import pytest

from app.analysis import (
    COMFORT_MIN_SOLVED,
    BucketStat,
    RankInfo,
    comfort_rating,
    contest_level,
    difficulty_profile,
    rank_info,
    rating_trend,
    recommend,
    tag_stats,
    upsolve_list,
    verdict_breakdown,
    weak_topics,
)


def sub(contest, index, verdict, tags=(), rating=None, t=0, live=False, sub_id=0):
    problem = {"contestId": contest, "index": index, "tags": list(tags)}
    if rating is not None:
        problem["rating"] = rating
    return {
        "id": sub_id,
        "verdict": verdict,
        "creationTimeSeconds": t,
        "author": {"participantType": "CONTESTANT" if live else "PRACTICE"},
        "problem": problem,
    }


@pytest.mark.parametrize(
    "rating, expected",
    [
        (1200, RankInfo("Pupil", "Specialist", 1400, 200)),        # exactly on a threshold
        (1199, RankInfo("Newbie", "Pupil", 1200, 1)),
        (2999, RankInfo("International Grandmaster", "Legendary Grandmaster", 3000, 1)),
        (3000, RankInfo("Legendary Grandmaster", None, None, None)),
        (-50, RankInfo("Newbie", "Pupil", 1200, 1250)),            # below every threshold
    ],
)
def test_rank_info_boundaries(rating, expected):
    assert rank_info(rating) == expected


def test_rating_trend_window_larger_than_history():
    history = [{"oldRating": 0, "newRating": 500}, {"oldRating": 500, "newRating": 450}]
    trend = rating_trend(history, last_n=10)
    assert trend.recent_change == 450
    assert rating_trend(history, last_n=0).recent_change == 0


def test_first_try_uses_earliest_submission_in_any_input_order():
    # Oldest first this time, and a same-second tie broken by submission id.
    subs = [
        sub(1, "A", "WRONG_ANSWER", ["math"], 800, t=10, sub_id=1),
        sub(1, "A", "OK", ["math"], 800, t=10, sub_id=2),
        sub(2, "A", "OK", ["math"], 900, t=20, sub_id=3),
    ]
    stats = {s.tag: s for s in tag_stats(subs)}
    assert stats["math"].first_try_rate == pytest.approx(0.5)
    assert verdict_breakdown(subs).first_try_rate == pytest.approx(0.5)


def test_pending_submissions_are_ignored():
    subs = [
        sub(1, "A", "OK", ["math"], 800, t=20),
        sub(1, "A", "TESTING", ["math"], 800, t=10),   # still in the queue: not a "first try"
        sub(2, "B", None, ["dp"], 1000, t=5),          # no verdict yet: not attempted
    ]
    stats = {s.tag: s for s in tag_stats(subs)}
    assert stats["math"].first_try_rate == 1.0
    assert "dp" not in stats
    assert difficulty_profile(subs) == [BucketStat(800, 1, 1)]


def test_difficulty_buckets_round_down():
    subs = [sub(1, "A", "OK", rating=1450), sub(1, "B", "WRONG_ANSWER", rating=1499)]
    assert difficulty_profile(subs) == [BucketStat(1400, solved=1, attempted=2)]
    assert difficulty_profile(subs, bucket=500) == [BucketStat(1000, solved=1, attempted=2)]


def test_weak_topics_float_ties_fall_back_to_tag_name():
    # 10 problems in range: "a" on 6 (user solved 2 of them) -> 0.6 / 3; "b" on 2 -> 0.2 / 1.
    # On floats 0.6 / 3 < 0.2, so without rounding "b" would wrongly come first.
    problems = [{"contestId": i, "index": "A", "rating": 1500, "tags": ["a"]} for i in range(6)]
    problems += [{"contestId": 10 + i, "index": "A", "rating": 1500, "tags": ["b"]} for i in range(2)]
    problems += [{"contestId": 20 + i, "index": "A", "rating": 1500, "tags": []} for i in range(2)]
    subs = [sub(0, "A", "OK", ["a"], 1500), sub(1, "A", "OK", ["a"], 1500)]
    result = weak_topics(subs, problems, 1400, 1600)
    assert 0.6 / 3 < 0.2  # the float trap this guards against
    assert [w.tag for w in result] == ["a", "b"]


def test_weak_topics_empty_when_no_problems_in_range():
    assert weak_topics([], [{"contestId": 1, "index": "A", "rating": 800, "tags": ["dp"]}],
                       3900, 4100) == []


def test_contest_level_counts_each_contest_once_per_letter():
    subs = [
        sub(1, "C1", "OK", live=True),
        sub(1, "C2", "OK", live=True),       # same letter, same contest: counted once
        sub(1, "A", "OK", live=True),
        sub(2, "A", "WRONG_ANSWER", live=True),
        sub(3, "D", "OK"),                    # practice: ignored
    ]
    assert contest_level(subs) == pytest.approx({"A": 1 / 2, "C": 1 / 2})


def test_upsolve_ignores_problems_solved_later_in_practice():
    subs = [
        sub(1, "B", "OK", rating=1200, t=50),                       # upsolved in practice
        sub(1, "B", "WRONG_ANSWER", rating=1200, t=10, live=True),
        sub(1, "C", "WRONG_ANSWER", t=11, live=True),               # no rating: goes last
        sub(1, "D", "WRONG_ANSWER", rating=1900, t=12, live=True),
    ]
    assert [p["index"] for p in upsolve_list(subs)] == ["D", "C"]


def test_recommend_ignores_special_tag_and_missing_solved_count():
    problems = [
        {"contestId": 1, "index": "A", "rating": 1500, "tags": ["*special"]},
        {"contestId": 1, "index": "B", "rating": 1500, "tags": ["dp"]},                     # no solvedCount
        {"contestId": 1, "index": "C", "rating": 1500, "tags": ["dp"], "solvedCount": 5},
    ]
    result = recommend(problems, set(), ["dp", "*special"], 1400, 1600)
    assert [p["index"] for p in result] == ["C", "B"]


def test_recommend_respects_limit_and_inclusive_bounds():
    problems = [
        {"contestId": 1, "index": "A", "rating": 1400, "tags": ["dp"]},
        {"contestId": 1, "index": "B", "rating": 1600, "tags": ["dp"]},
        {"contestId": 1, "index": "C", "rating": 1700, "tags": ["dp"]},
    ]
    assert [p["index"] for p in recommend(problems, set(), ["dp"], 1400, 1600)] == ["A", "B"]
    assert len(recommend(problems, set(), ["dp"], 1400, 1600, limit=1)) == 1


def test_comfort_needs_more_than_20_solves_by_default():
    profile = [BucketStat(1400, 21, 25), BucketStat(1500, 20, 30), BucketStat(1600, 3, 3)]
    assert COMFORT_MIN_SOLVED == 21
    assert comfort_rating(profile) == 1400  # 20 solves at 1500 are not enough
    assert comfort_rating([BucketStat(1500, 20, 20)]) is None
