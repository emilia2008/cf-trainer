"""Core analysis: pure functions, no database and no network. Easy to test.

This is the heart of the project and what interviewers will ask about most.
Implement the functions marked TODO until tests/test_analysis.py is all green.

Data shapes from the Codeforces API (only the fields used here):

A submission (from user.status), newest first in the API response:
    {
        "verdict": "OK",                      # "OK" means accepted
        "creationTimeSeconds": 1727000000,
        "author": {"participantType": "CONTESTANT"},   # or "PRACTICE", "VIRTUAL", ...
        "problem": {
            "contestId": 1850, "index": "C",
            "rating": 1200,                   # may be missing
            "tags": ["greedy", "math"],
        },
    }

A rating change (from user.rating), oldest first:
    {"contestId": 1850, "contestName": "...", "rank": 1234,
     "oldRating": 1100, "newRating": 1180, "ratingUpdateTimeSeconds": 1727000000}

A problem (from problemset.problems, with "solvedCount" merged in by the client):
    {"contestId": 1850, "index": "C", "name": "...", "rating": 1200,
     "tags": ["greedy"], "solvedCount": 25000}
"""

from dataclasses import dataclass

# Codeforces ranks: (minimum rating, title). Stable, part of the rating system.
RANKS: list[tuple[int, str]] = [
    (0, "Newbie"),
    (1200, "Pupil"),
    (1400, "Specialist"),
    (1600, "Expert"),
    (1900, "Candidate Master"),
    (2100, "Master"),
    (2300, "International Master"),
    (2400, "Grandmaster"),
    (2600, "International Grandmaster"),
    (3000, "Legendary Grandmaster"),
]

# Tags that are not real topics and should be ignored in topic analysis.
IGNORED_TAGS = {"*special"}


# ---- Result types ---------------------------------------------------------------

@dataclass(frozen=True)
class RankInfo:
    rank: str
    next_rank: str | None         # None at the top rank
    next_threshold: int | None    # rating needed for next_rank
    points_to_next: int | None


@dataclass(frozen=True)
class BucketStat:
    rating: int      # problem rating bucket, e.g. 1200
    solved: int      # distinct problems solved at this rating
    attempted: int   # distinct problems tried at this rating (solved or not)


@dataclass(frozen=True)
class TagStat:
    tag: str
    solved: int
    attempted: int
    first_try_rate: float          # share of solved problems accepted on the first submission
    max_solved_rating: int | None  # hardest solved problem with this tag


@dataclass(frozen=True)
class WeakTopic:
    tag: str
    importance: float     # share of problems in the target range that have this tag
    solved_in_range: int  # problems with this tag the user solved in the target range
    score: float          # higher = more urgent to practise


@dataclass(frozen=True)
class VerdictStats:
    total_submissions: int
    accepted: int
    by_verdict: dict[str, int]  # counts of every non-OK verdict, e.g. {"WRONG_ANSWER": 12}
    first_try_rate: float       # over all solved problems


@dataclass(frozen=True)
class RatingTrend:
    contests: int
    current: int | None
    max_rating: int | None
    recent_change: int          # total rating change over the last `last_n` contests
    best_gain: int | None
    worst_drop: int | None


# ---- Provided helpers -----------------------------------------------------------

def problem_key(problem: dict) -> str:
    """Unique id for a problem, e.g. '1850C'."""
    return f"{problem.get('contestId', '')}{problem.get('index', '')}"


def real_tags(problem: dict) -> list[str]:
    """The problem's tags without IGNORED_TAGS."""
    return [t for t in problem.get("tags", []) if t not in IGNORED_TAGS]


# ---- Overview -------------------------------------------------------------------

def rank_info(rating: int | None) -> RankInfo:
    """Current rank and distance to the next one. Treat None (unrated) as 0."""
    # TODO
    raise NotImplementedError


def solved_problems(submissions: list[dict]) -> dict[str, dict]:
    """{problem_key: problem} for every problem with at least one 'OK' verdict (counted once)."""
    # TODO
    raise NotImplementedError


def rating_trend(history: list[dict], last_n: int = 5) -> RatingTrend:
    """Summary of the rating history (oldest first). Empty history: contests=0,
    current/max/best/worst None, recent_change 0."""
    # TODO
    raise NotImplementedError


# ---- Difficulty -----------------------------------------------------------------

def difficulty_profile(submissions: list[dict], bucket: int = 100) -> list[BucketStat]:
    """Solved/attempted counts per rating bucket (rating // bucket * bucket),
    sorted by rating. Problems without a rating are skipped."""
    # TODO
    raise NotImplementedError


def comfort_rating(profile: list[BucketStat], min_solved: int = 3) -> int | None:
    """Highest bucket rating where the user solved at least `min_solved` problems."""
    # TODO
    raise NotImplementedError


def target_range(user_rating: int | None, comfort: int | None) -> tuple[int, int]:
    """Rating range to practise in to improve.

    base = max(user_rating, comfort, 800), with None treated as 0, rounded down to a multiple of 100.
    Return (base + 100, base + 300).
    """
    # TODO
    raise NotImplementedError


# ---- Topics ---------------------------------------------------------------------

def tag_stats(submissions: list[dict]) -> list[TagStat]:
    """One TagStat per real tag seen, sorted by solved descending, then tag name.

    "First try" means the earliest submission (by creationTimeSeconds) for that
    problem was accepted. first_try_rate is 0.0 when nothing is solved.
    """
    # TODO
    raise NotImplementedError


def tag_importance(all_problems: list[dict], lo: int, hi: int) -> dict[str, float]:
    """For problems rated in [lo, hi]: the fraction that has each real tag.
    Empty dict if there are no problems in range."""
    # TODO
    raise NotImplementedError


def weak_topics(
    submissions: list[dict],
    all_problems: list[dict],
    lo: int,
    hi: int,
    k: int = 5,
    min_importance: float = 0.05,
) -> list[WeakTopic]:
    """Topics that matter in the target range but the user has rarely solved there.

    For every tag with importance >= min_importance (see tag_importance):
        solved_in_range = distinct solved problems with that tag rated in [lo, hi]
        score = importance / (1 + solved_in_range)
    Return the top k by score descending, ties by tag name.
    """
    # TODO
    raise NotImplementedError


# ---- Habits ---------------------------------------------------------------------

def verdict_breakdown(submissions: list[dict]) -> VerdictStats:
    """Count submissions by verdict. Skip submissions with no verdict or verdict 'TESTING'."""
    # TODO
    raise NotImplementedError


def contest_level(submissions: list[dict]) -> dict[str, float]:
    """In contests the user took part in live (participantType 'CONTESTANT'):
    for each problem letter (first character of index, e.g. 'C1' -> 'C'),
    the fraction of those contests where the user solved a problem with that letter.
    Only letters solved at least once appear. Empty dict if no live contests.
    """
    # TODO
    raise NotImplementedError


def upsolve_list(submissions: list[dict]) -> list[dict]:
    """Problems attempted live in a contest (CONTESTANT) but never accepted in any submission.
    Each problem once, sorted by rating ascending (no rating last), then problem_key."""
    # TODO
    raise NotImplementedError


# ---- Recommendations ------------------------------------------------------------

def recommend(
    all_problems: list[dict],
    solved_keys: set[str],
    weak_tags: list[str],
    lo: int,
    hi: int,
    limit: int = 10,
) -> list[dict]:
    """Unsolved problems rated in [lo, hi] with at least one weak tag.

    Sort by: number of weak tags matched (desc), rating (asc), solvedCount (desc,
    missing = 0), problem_key (asc). Return at most `limit`.
    """
    # TODO
    raise NotImplementedError
