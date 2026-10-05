"""Build the analysis report from a user's stored data and the (cached) Codeforces problem list."""

import logging
import threading
import time
from collections.abc import Callable

from app import analysis
from app.analysis import problem_key, real_tags
from app.cf_client import CodeforcesError
from app.models import User
from app.resources import VERDICT_ADVICE, resources_for, verdict_label
from app.schemas import (
    Bucket,
    ContestLetter,
    DifficultySection,
    HabitsSection,
    Overview,
    ProblemOut,
    RatingPoint,
    RatingTrendSection,
    Recommendation,
    Report,
    Resource,
    TargetRange,
    TopicStat,
    UpsolveSection,
    VerdictShare,
    WeakTopicOut,
)

logger = logging.getLogger(__name__)

RECENT_CONTESTS = 5
ADVICE_MIN_SHARE = 0.15     # show advice for verdicts above 15% of failed submissions
USUAL_LEVEL_MIN_RATE = 0.5  # "usually solves up to X": X solved in at least half the contests
UPSOLVE_LIMIT = 10
RECOMMEND_LIMIT = 10


# ---- Problem list cache -------------------------------------------------------------

class ProblemCache:
    """In-memory copy of the full Codeforces problem list, refreshed at most once per `ttl_seconds`.

    `clock` is injectable so tests can move time forward without waiting. The lock is held
    while fetching, so concurrent requests on a cold cache wait for one download instead of
    each starting their own. If a refresh fails but an older copy exists, the old copy is
    served and the refresh is retried after `retry_seconds`.
    """

    def __init__(
        self,
        ttl_seconds: float = 24 * 60 * 60,
        clock: Callable[[], float] = time.monotonic,
        retry_seconds: float = 5 * 60,
    ) -> None:
        self.ttl_seconds = ttl_seconds
        self.retry_seconds = retry_seconds
        self._clock = clock
        self._lock = threading.Lock()
        self._problems: list[dict] | None = None
        self._expires_at = 0.0

    def get(self, fetch: Callable[[], list[dict]]) -> list[dict]:
        with self._lock:
            now = self._clock()
            if self._problems is not None and now < self._expires_at:
                return self._problems
            try:
                problems = fetch()
            except CodeforcesError:
                if self._problems is None:
                    raise
                logger.warning("Problem list refresh failed; serving the cached copy", exc_info=True)
                self._expires_at = now + self.retry_seconds
                return self._problems
            self._problems = problems
            self._expires_at = now + self.ttl_seconds
            return problems

    def clear(self) -> None:
        with self._lock:
            self._problems = None
            self._expires_at = 0.0


problem_cache = ProblemCache()


def get_problem_cache() -> ProblemCache:
    """FastAPI dependency; tests override it with a fresh cache."""
    return problem_cache


# ---- Report -------------------------------------------------------------------------

def problem_url(contest_id: int | None, index: str) -> str:
    # Gym contests (id >= 100000) are not in the problemset and live under /gym instead.
    if contest_id is not None and contest_id >= 100_000:
        return f"https://codeforces.com/gym/{contest_id}/problem/{index}"
    return f"https://codeforces.com/problemset/problem/{contest_id}/{index}"


def _problem_out(problem: dict, solved_count: int | None) -> dict:
    contest_id = problem.get("contestId")
    index = problem.get("index", "")
    return {
        "contest_id": contest_id,
        "index": index,
        "name": problem.get("name"),
        "rating": problem.get("rating"),
        "tags": real_tags(problem),
        "solved_count": solved_count,
        "url": problem_url(contest_id, index),
    }


def weak_topic_reason(importance: float, solved_in_range: int, lo: int, hi: int) -> str:
    share = f"Appears in {round(importance * 100)}% of problems rated {lo}–{hi}"
    if solved_in_range == 0:
        return f"{share}, and you have not solved any of them yet."
    noun = "problem" if solved_in_range == 1 else "problems"
    return f"{share}, but you have solved only {solved_in_range} {noun} with this tag there."


def usually_solves_up_to(level: dict[str, float]) -> str | None:
    """The furthest problem letter solved in at least half of the live contests."""
    letters = [letter for letter, rate in level.items() if rate >= USUAL_LEVEL_MIN_RATE]
    return max(letters, default=None)


def _verdict_shares(by_verdict: dict[str, int]) -> list[VerdictShare]:
    failed = sum(by_verdict.values())
    shares = []
    for verdict, count in sorted(by_verdict.items(), key=lambda item: (-item[1], item[0])):
        share = count / failed
        shares.append(VerdictShare(
            verdict=verdict,
            label=verdict_label(verdict),
            count=count,
            share=share,
            advice=VERDICT_ADVICE.get(verdict) if share > ADVICE_MIN_SHARE else None,
        ))
    return shares


def build_report(user: User, problems: list[dict]) -> Report:
    """Assemble every report section from the functions in app.analysis."""
    snapshot = user.snapshot
    submissions = snapshot.submissions if snapshot else []
    history = snapshot.rating_history if snapshot else []
    solved_counts = {problem_key(p): p.get("solvedCount") for p in problems}

    # Overview
    rank = analysis.rank_info(user.rating)
    solved = analysis.solved_problems(submissions)
    overview = Overview(
        handle=user.handle,
        rank=rank.rank,
        rating=user.rating,
        max_rating=user.max_rating,
        max_rank=analysis.rank_info(user.max_rating).rank,
        next_rank=rank.next_rank,
        next_threshold=rank.next_threshold,
        points_to_next=rank.points_to_next,
        solved_count=len(solved),
        contests=len(history),
    )

    # Rating trend
    trend = analysis.rating_trend(history, last_n=RECENT_CONTESTS)
    rating_section = RatingTrendSection(
        contests=trend.contests,
        current=trend.current,
        max_rating=trend.max_rating,
        recent_window=min(RECENT_CONTESTS, trend.contests),
        recent_change=trend.recent_change,
        best_gain=trend.best_gain,
        worst_drop=trend.worst_drop,
        history=[
            RatingPoint(
                contest_id=change["contestId"],
                contest_name=change.get("contestName", ""),
                rank=change.get("rank", 0),
                old_rating=change["oldRating"],
                new_rating=change["newRating"],
                delta=change["newRating"] - change["oldRating"],
                time=change.get("ratingUpdateTimeSeconds", 0),
            )
            for change in history
        ],
    )

    # Difficulty
    profile = analysis.difficulty_profile(submissions)
    comfort = analysis.comfort_rating(profile)
    lo, hi = analysis.target_range(user.rating, comfort)
    difficulty = DifficultySection(
        buckets=[Bucket(rating=b.rating, solved=b.solved, attempted=b.attempted) for b in profile],
        comfort_rating=comfort,
        target_range=TargetRange(lo=lo, hi=hi),
        problems_in_range=sum(
            1 for p in problems if p.get("rating") is not None and lo <= p["rating"] <= hi
        ),
    )

    # Topics and weak topics
    topics = [TopicStat(**vars(stat)) for stat in analysis.tag_stats(submissions)]
    weak = analysis.weak_topics(submissions, problems, lo, hi)
    weak_out = [
        WeakTopicOut(
            tag=w.tag,
            importance=w.importance,
            solved_in_range=w.solved_in_range,
            score=w.score,
            reason=weak_topic_reason(w.importance, w.solved_in_range, lo, hi),
            resources=[Resource(**link) for link in resources_for(w.tag)],
        )
        for w in weak
    ]

    # Habits
    verdicts = analysis.verdict_breakdown(submissions)
    level = analysis.contest_level(submissions)
    live_contests = {
        s.get("problem", {}).get("contestId")
        for s in submissions
        if s.get("author", {}).get("participantType") == "CONTESTANT"
    }
    habits = HabitsSection(
        total_submissions=verdicts.total_submissions,
        accepted=verdicts.accepted,
        failed=verdicts.total_submissions - verdicts.accepted,
        first_try_rate=verdicts.first_try_rate,
        verdicts=_verdict_shares(verdicts.by_verdict),
        live_contests=len(live_contests),
        contest_level=[ContestLetter(letter=k, rate=v) for k, v in level.items()],
        usually_solves_up_to=usually_solves_up_to(level),
    )

    # Upsolve and recommendations
    upsolve = analysis.upsolve_list(submissions)
    upsolve_section = UpsolveSection(
        total=len(upsolve),
        problems=[
            ProblemOut(**_problem_out(p, solved_counts.get(problem_key(p))))
            for p in upsolve[:UPSOLVE_LIMIT]
        ],
    )
    weak_tags = [w.tag for w in weak]
    recommendations = [
        Recommendation(
            **_problem_out(p, p.get("solvedCount")),
            matched_tags=[tag for tag in real_tags(p) if tag in weak_tags],
        )
        for p in analysis.recommend(problems, set(solved), weak_tags, lo, hi, limit=RECOMMEND_LIMIT)
    ]

    return Report(
        handle=user.handle,
        last_synced_at=user.last_synced_at,
        overview=overview,
        rating_trend=rating_section,
        difficulty=difficulty,
        topics=topics,
        weak_topics=weak_out,
        habits=habits,
        upsolve=upsolve_section,
        recommendations=recommendations,
    )
