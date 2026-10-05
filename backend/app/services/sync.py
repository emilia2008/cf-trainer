"""Fetch a user's data from Codeforces and store it."""

from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.cf_client import CodeforcesClient
from app.models import User, UserSnapshot

# Submission fields the analysis uses, plus two kept for planned features (solve speed in
# contests, language stats). Dropping the rest (judge stats, team members, ...) shrinks the
# stored JSON to roughly a third.
SUBMISSION_FIELDS = (
    "id", "contestId", "creationTimeSeconds", "relativeTimeSeconds", "verdict", "programmingLanguage",
)
PROBLEM_FIELDS = ("contestId", "index", "name", "rating", "tags")


def slim_submission(submission: dict) -> dict:
    slim = {field: submission[field] for field in SUBMISSION_FIELDS if field in submission}
    problem = submission.get("problem", {})
    slim["problem"] = {field: problem[field] for field in PROBLEM_FIELDS if field in problem}
    slim["author"] = {"participantType": submission.get("author", {}).get("participantType")}
    return slim


def find_user(session: Session, handle: str) -> User | None:
    """Codeforces handles are case-insensitive: 'Tourist' and 'tourist' are the same user."""
    return session.scalars(select(User).where(func.lower(User.handle) == handle.lower())).first()


def sync_user(session: Session, client: CodeforcesClient, handle: str) -> User:
    """Fetch info, rating history and submissions, then create or replace the stored copy.

    All API calls happen before any database write, so a failed sync leaves the old data intact.
    Raises HandleNotFound / CodeforcesError from the client.
    """
    info = client.user_info(handle)
    canonical = info["handle"]  # Codeforces' own spelling (and the new name after a rename)
    history = client.user_rating(canonical)
    submissions = [slim_submission(s) for s in client.user_submissions(canonical)]
    now = datetime.now(UTC)

    try:
        user = _store(session, info, history, submissions, now)
        session.commit()
    except IntegrityError:
        # Another request inserted the same user between our lookup and our insert. Its row
        # now exists, so the second attempt updates it instead.
        session.rollback()
        user = _store(session, info, history, submissions, now)
        session.commit()
    return user


def _store(
    session: Session, info: dict, history: list[dict], submissions: list[dict], now: datetime
) -> User:
    user = find_user(session, info["handle"])
    if user is None:
        user = User(handle=info["handle"])
        session.add(user)
    user.handle = info["handle"]
    user.rating = info.get("rating")
    user.max_rating = info.get("maxRating")
    user.rank = info.get("rank")
    user.last_synced_at = now

    if user.snapshot is None:
        user.snapshot = UserSnapshot(submissions=submissions, rating_history=history, fetched_at=now)
    else:
        user.snapshot.submissions = submissions
        user.snapshot.rating_history = history
        user.snapshot.fetched_at = now
    session.flush()
    return user
