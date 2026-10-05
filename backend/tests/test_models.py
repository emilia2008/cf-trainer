from datetime import UTC, datetime

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.models import User, UserSnapshot

SUBMISSIONS = [
    {"id": 2, "verdict": "OK", "problem": {"contestId": 1, "index": "A", "tags": ["math", "dp"]}},
    {"id": 1, "verdict": "WRONG_ANSWER", "problem": {"contestId": 1, "index": "A", "tags": []}},
]


def test_snapshot_round_trips_json(session):
    user = User(handle="alice", rating=1500)
    user.snapshot = UserSnapshot(
        submissions=SUBMISSIONS,
        rating_history=[{"oldRating": 0, "newRating": 400}],
        fetched_at=datetime.now(UTC),
    )
    session.add(user)
    session.commit()
    session.expunge_all()

    stored = session.scalars(select(UserSnapshot)).one()
    assert stored.submissions == SUBMISSIONS
    assert stored.rating_history == [{"oldRating": 0, "newRating": 400}]
    assert stored.user.handle == "alice"


def test_one_snapshot_per_user(session):
    user = User(handle="bob")
    session.add(user)
    session.flush()
    now = datetime.now(UTC)
    session.add(UserSnapshot(user_id=user.id, submissions=[], rating_history=[], fetched_at=now))
    session.add(UserSnapshot(user_id=user.id, submissions=[], rating_history=[], fetched_at=now))
    with pytest.raises(IntegrityError):
        session.flush()


def test_deleting_user_deletes_snapshot(session):
    user = User(handle="carol")
    user.snapshot = UserSnapshot(submissions=[], rating_history=[], fetched_at=datetime.now(UTC))
    session.add(user)
    session.commit()

    session.delete(user)
    session.commit()
    assert session.scalars(select(UserSnapshot)).all() == []
