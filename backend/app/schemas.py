"""JSON shapes returned by the API (Pydantic models, also used for the /docs page)."""

from datetime import UTC, datetime
from typing import Annotated

from pydantic import AfterValidator, BaseModel


def _as_utc(value: datetime) -> datetime:
    # SQLite drops the timezone; every timestamp this app stores is UTC.
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value


UTCDateTime = Annotated[datetime, AfterValidator(_as_utc)]


class Resource(BaseModel):
    title: str
    url: str


class SyncResult(BaseModel):
    handle: str
    rating: int | None
    max_rating: int | None
    rank: str | None
    last_synced_at: UTCDateTime
    submissions: int
    contests: int


# ---- Report ---------------------------------------------------------------------

class Overview(BaseModel):
    handle: str
    rank: str
    rating: int | None
    max_rating: int | None
    max_rank: str
    next_rank: str | None
    next_threshold: int | None
    points_to_next: int | None
    solved_count: int
    contests: int


class RatingPoint(BaseModel):
    contest_id: int
    contest_name: str
    rank: int
    old_rating: int
    new_rating: int
    delta: int
    time: int  # unix seconds


class RatingTrendSection(BaseModel):
    contests: int
    current: int | None
    max_rating: int | None
    recent_window: int     # number of contests recent_change covers
    recent_change: int
    best_gain: int | None
    worst_drop: int | None
    history: list[RatingPoint]


class Bucket(BaseModel):
    rating: int
    solved: int
    attempted: int


class TargetRange(BaseModel):
    lo: int
    hi: int


class DifficultySection(BaseModel):
    buckets: list[Bucket]
    comfort_rating: int | None
    comfort_min_solved: int  # solves needed at a rating for it to count as comfortable
    target_range: TargetRange
    problems_in_range: int  # problems on Codeforces rated inside the target range


class TopicStat(BaseModel):
    tag: str
    solved: int
    attempted: int
    first_try_rate: float
    max_solved_rating: int | None


class WeakTopicOut(BaseModel):
    tag: str
    importance: float
    solved_in_range: int
    score: float
    reason: str
    resources: list[Resource]


class VerdictShare(BaseModel):
    verdict: str
    label: str
    count: int
    share: float          # share of all non-accepted submissions
    advice: str | None    # set when share > ADVICE_MIN_SHARE and advice exists


class ContestLetter(BaseModel):
    letter: str
    rate: float           # share of live contests where a problem with this letter was solved


class HabitsSection(BaseModel):
    total_submissions: int
    accepted: int
    failed: int
    first_try_rate: float
    verdicts: list[VerdictShare]
    live_contests: int
    contest_level: list[ContestLetter]
    usually_solves_up_to: str | None  # furthest letter solved in at least half the live contests


class ProblemOut(BaseModel):
    contest_id: int | None
    index: str
    name: str | None
    rating: int | None
    tags: list[str]
    solved_count: int | None
    url: str


class Recommendation(ProblemOut):
    matched_tags: list[str]


class UpsolveSection(BaseModel):
    total: int
    problems: list[ProblemOut]


class Report(BaseModel):
    handle: str
    last_synced_at: UTCDateTime | None
    overview: Overview
    rating_trend: RatingTrendSection
    difficulty: DifficultySection
    topics: list[TopicStat]
    weak_topics: list[WeakTopicOut]
    habits: HabitsSection
    upsolve: UpsolveSection
    recommendations: list[Recommendation]
