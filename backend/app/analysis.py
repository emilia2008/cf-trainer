"""Core analysis: pure functions, no database and no network. Easy to test.

Every function takes the data exactly as the Codeforces API returns it, and problems are
always counted once each (by problem_key), never once per submission.

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

import heapq
from bisect import bisect_right
from collections import Counter, defaultdict
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

# A rating only counts as comfortable after MORE than 20 solves at it, so a handful of hard
# problems solved in practice cannot push the target range above the user's real level.
COMFORT_MIN_SOLVED = 21

# Verdicts of submissions that are still being judged. They say nothing yet, so the
# per-problem analysis skips them.
PENDING_VERDICTS = {None, "TESTING"}


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


# ---- Internal helpers -----------------------------------------------------------

@dataclass
class _ProblemHistory:
    """Everything the user did on one problem."""

    problem: dict
    solved: bool = False
    first: dict | None = None  # earliest judged submission

    @property
    def first_try(self) -> bool:
        return self.first is not None and self.first.get("verdict") == "OK"


def _is_judged(submission: dict) -> bool:
    return submission.get("verdict") not in PENDING_VERDICTS


def _is_live(submission: dict) -> bool:
    return submission.get("author", {}).get("participantType") == "CONTESTANT"


def _submitted_order(submission: dict) -> tuple[int, int]:
    # Submission ids increase over time, so they break ties within the same second.
    return submission.get("creationTimeSeconds", 0), submission.get("id", 0)


def _in_range(problem: dict, lo: int, hi: int) -> bool:
    rating = problem.get("rating")
    return rating is not None and lo <= rating <= hi


def _problem_histories(submissions: list[dict]) -> dict[str, _ProblemHistory]:
    """{problem_key: history} over judged submissions. One pass, in any input order."""
    histories: dict[str, _ProblemHistory] = {}
    for submission in submissions:
        if not _is_judged(submission):
            continue
        problem = submission.get("problem", {})
        key = problem_key(problem)
        history = histories.get(key)
        if history is None:
            history = histories[key] = _ProblemHistory(problem)
        if submission["verdict"] == "OK":
            history.solved = True
        if history.first is None or _submitted_order(submission) < _submitted_order(history.first):
            history.first = submission
    return histories


# ---- Overview -------------------------------------------------------------------

_RANK_THRESHOLDS = [threshold for threshold, _ in RANKS]


def rank_info(rating: int | None) -> RankInfo:
    """Current rank and distance to the next one. Treat None (unrated) as 0."""
    value = rating or 0
    i = max(bisect_right(_RANK_THRESHOLDS, value) - 1, 0)
    title = RANKS[i][1]
    if i + 1 == len(RANKS):
        return RankInfo(title, None, None, None)
    threshold, next_title = RANKS[i + 1]
    return RankInfo(title, next_title, threshold, threshold - value)


def solved_problems(submissions: list[dict]) -> dict[str, dict]:
    """{problem_key: problem} for every problem with at least one 'OK' verdict (counted once)."""
    solved: dict[str, dict] = {}
    for submission in submissions:
        if submission.get("verdict") == "OK":
            problem = submission.get("problem", {})
            solved.setdefault(problem_key(problem), problem)
    return solved


def rating_trend(history: list[dict], last_n: int = 5) -> RatingTrend:
    """Summary of the rating history (oldest first). Empty history: contests=0,
    current/max/best/worst None, recent_change 0."""
    if not history:
        return RatingTrend(0, None, None, 0, None, None)
    deltas = [change["newRating"] - change["oldRating"] for change in history]
    return RatingTrend(
        contests=len(history),
        current=history[-1]["newRating"],
        max_rating=max(change["newRating"] for change in history),
        recent_change=sum(deltas[-last_n:]) if last_n > 0 else 0,
        best_gain=max(deltas),
        worst_drop=min(deltas),
    )


# ---- Difficulty -----------------------------------------------------------------

def difficulty_profile(submissions: list[dict], bucket: int = 100) -> list[BucketStat]:
    """Solved/attempted counts per rating bucket (rating // bucket * bucket),
    sorted by rating. Problems without a rating are skipped."""
    solved: Counter[int] = Counter()
    attempted: Counter[int] = Counter()
    for history in _problem_histories(submissions).values():
        rating = history.problem.get("rating")
        if rating is None:
            continue
        rating_bucket = rating // bucket * bucket
        attempted[rating_bucket] += 1
        if history.solved:
            solved[rating_bucket] += 1
    return [BucketStat(r, solved[r], attempted[r]) for r in sorted(attempted)]


def comfort_rating(profile: list[BucketStat], min_solved: int = COMFORT_MIN_SOLVED) -> int | None:
    """Highest bucket rating where the user solved at least `min_solved` problems."""
    return max((stat.rating for stat in profile if stat.solved >= min_solved), default=None)


def target_range(user_rating: int | None, comfort: int | None) -> tuple[int, int]:
    """Rating range to practise in to improve.

    base = max(user_rating, comfort, 800), with None treated as 0, rounded down to a multiple of 100.
    Return (base + 100, base + 300).
    """
    base = max(user_rating or 0, comfort or 0, 800) // 100 * 100
    return base + 100, base + 300


# ---- Topics ---------------------------------------------------------------------

def tag_stats(submissions: list[dict]) -> list[TagStat]:
    """One TagStat per real tag seen, sorted by solved descending, then tag name.

    "First try" means the earliest submission (by creationTimeSeconds) for that
    problem was accepted. first_try_rate is 0.0 when nothing is solved.
    """
    attempted: Counter[str] = Counter()
    solved: Counter[str] = Counter()
    first_try: Counter[str] = Counter()
    hardest: dict[str, int] = {}
    for history in _problem_histories(submissions).values():
        rating = history.problem.get("rating")
        for tag in set(real_tags(history.problem)):
            attempted[tag] += 1
            if not history.solved:
                continue
            solved[tag] += 1
            if history.first_try:
                first_try[tag] += 1
            if rating is not None and rating > hardest.get(tag, -1):
                hardest[tag] = rating
    stats = [
        TagStat(
            tag=tag,
            solved=solved[tag],
            attempted=attempted[tag],
            first_try_rate=first_try[tag] / solved[tag] if solved[tag] else 0.0,
            max_solved_rating=hardest.get(tag),
        )
        for tag in attempted
    ]
    return sorted(stats, key=lambda stat: (-stat.solved, stat.tag))


def tag_importance(all_problems: list[dict], lo: int, hi: int) -> dict[str, float]:
    """For problems rated in [lo, hi]: the fraction that has each real tag.
    Empty dict if there are no problems in range."""
    in_range = [problem for problem in all_problems if _in_range(problem, lo, hi)]
    if not in_range:
        return {}
    counts = Counter(tag for problem in in_range for tag in set(real_tags(problem)))
    return {tag: count / len(in_range) for tag, count in counts.items()}


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
    importance = tag_importance(all_problems, lo, hi)
    solved_in_range = Counter(
        tag
        for problem in solved_problems(submissions).values()
        if _in_range(problem, lo, hi)
        for tag in set(real_tags(problem))
    )
    topics = [
        WeakTopic(tag, share, solved_in_range[tag], share / (1 + solved_in_range[tag]))
        for tag, share in importance.items()
        if share >= min_importance
    ]
    # Round before comparing so scores that are equal on paper (0.6 / 3 vs 0.2) tie on
    # floats too and fall back to the tag name.
    topics.sort(key=lambda topic: (-round(topic.score, 12), topic.tag))
    return topics[:k]


# ---- Habits ---------------------------------------------------------------------

def verdict_breakdown(submissions: list[dict]) -> VerdictStats:
    """Count submissions by verdict. Skip submissions with no verdict or verdict 'TESTING'."""
    judged = [submission for submission in submissions if _is_judged(submission)]
    failures = Counter(s["verdict"] for s in judged if s["verdict"] != "OK")
    solved = [h for h in _problem_histories(judged).values() if h.solved]
    return VerdictStats(
        total_submissions=len(judged),
        accepted=len(judged) - failures.total(),
        by_verdict=dict(failures.most_common()),
        first_try_rate=sum(h.first_try for h in solved) / len(solved) if solved else 0.0,
    )


def contest_level(submissions: list[dict]) -> dict[str, float]:
    """In contests the user took part in live (participantType 'CONTESTANT'):
    for each problem letter (first character of index, e.g. 'C1' -> 'C'),
    the fraction of those contests where the user solved a problem with that letter.
    Only letters solved at least once appear. Empty dict if no live contests.
    """
    live = [submission for submission in submissions if _is_live(submission)]
    contests = {submission.get("problem", {}).get("contestId") for submission in live}
    if not contests:
        return {}
    contests_by_letter: dict[str, set] = defaultdict(set)
    for submission in live:
        problem = submission.get("problem", {})
        index = problem.get("index", "")
        if submission.get("verdict") == "OK" and index:
            contests_by_letter[index[0]].add(problem.get("contestId"))
    return {
        letter: len(solved_in) / len(contests)
        for letter, solved_in in sorted(contests_by_letter.items())
    }


def upsolve_list(submissions: list[dict]) -> list[dict]:
    """Problems attempted live in a contest (CONTESTANT) but never accepted in any submission.
    Each problem once, sorted by rating ascending (no rating last), then problem_key."""
    solved = solved_problems(submissions)
    unsolved: dict[str, dict] = {}
    for submission in submissions:
        if not (_is_live(submission) and _is_judged(submission)):
            continue
        problem = submission.get("problem", {})
        key = problem_key(problem)
        if key not in solved:
            unsolved.setdefault(key, problem)
    return sorted(
        unsolved.values(),
        key=lambda p: (p.get("rating") is None, p.get("rating") or 0, problem_key(p)),
    )


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
    weak = set(weak_tags)
    candidates = []
    for problem in all_problems:
        if not _in_range(problem, lo, hi) or problem_key(problem) in solved_keys:
            continue
        matched = len(weak.intersection(real_tags(problem)))
        if matched:
            candidates.append((matched, problem))
    # nsmallest keeps only `limit` items: O(n log limit) instead of sorting everything.
    best = heapq.nsmallest(
        limit,
        candidates,
        key=lambda item: (
            -item[0],
            item[1]["rating"],
            -item[1].get("solvedCount", 0),
            problem_key(item[1]),
        ),
    )
    return [problem for _, problem in best]
