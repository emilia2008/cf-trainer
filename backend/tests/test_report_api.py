"""API tests through TestClient.

app.dependency_overrides swaps in an in-memory SQLite database and a fake Codeforces client
(see conftest.py), so these tests never call the real API.
"""

from sqlalchemy import func, select

from app.cf_client import CodeforcesError
from app.models import User, UserSnapshot
from app.services import sync as sync_service
from app.services.sync import slim_submission


def count(session, model) -> int:
    return session.scalar(select(func.count()).select_from(model))


# ---- Sync ---------------------------------------------------------------------------

def test_sync_stores_user_and_snapshot(api, session):
    response = api.post("/api/users/alice/sync")

    assert response.status_code == 200
    body = response.json()
    assert body["handle"] == "alice"
    assert body["rating"] == 1350
    assert body["max_rating"] == 1420
    assert body["rank"] == "pupil"
    assert body["submissions"] == 9
    assert body["contests"] == 4
    assert body["last_synced_at"].endswith(("Z", "+00:00"))

    user = session.scalars(select(User)).one()
    assert user.handle == "alice"
    assert len(user.snapshot.submissions) == 9
    assert len(user.snapshot.rating_history) == 4


def test_sync_unknown_handle_returns_404(api, session):
    response = api.post("/api/users/nobody_here/sync")

    assert response.status_code == 404
    assert "nobody_here" in response.json()["detail"]
    assert count(session, User) == 0


def test_sync_twice_replaces_data_instead_of_duplicating(api, session, fake_cf):
    assert api.post("/api/users/alice/sync").status_code == 200

    new_submission = dict(fake_cf.users["alice"]["submissions"][0], id=10, creationTimeSeconds=100)
    fake_cf.users["alice"]["submissions"].insert(0, new_submission)
    fake_cf.users["alice"]["info"]["rating"] = 1400
    response = api.post("/api/users/alice/sync")

    assert response.status_code == 200
    assert response.json()["submissions"] == 10
    session.expire_all()
    assert count(session, User) == 1
    assert count(session, UserSnapshot) == 1
    user = session.scalars(select(User)).one()
    assert user.rating == 1400
    assert len(user.snapshot.submissions) == 10


def test_sync_is_case_insensitive(api, session):
    assert api.post("/api/users/alice/sync").status_code == 200
    response = api.post("/api/users/ALICE/sync")

    assert response.status_code == 200
    assert response.json()["handle"] == "alice"  # Codeforces' own spelling
    assert count(session, User) == 1


def test_sync_rejects_malformed_handle(api, fake_cf):
    response = api.post("/api/users/alice;bob/sync")
    assert response.status_code == 422
    assert fake_cf.calls["user_info"] == 0


def test_sync_codeforces_failure_returns_502_and_keeps_old_data(api, session, fake_cf):
    assert api.post("/api/users/alice/sync").status_code == 200

    fake_cf.fail_with = CodeforcesError("Could not reach Codeforces: timed out")
    response = api.post("/api/users/alice/sync")

    assert response.status_code == 502
    assert "Could not reach Codeforces" in response.json()["detail"]
    session.expire_all()
    assert len(session.scalars(select(UserSnapshot)).one().submissions) == 9


def test_sync_recovers_when_another_request_inserts_the_same_user(api, session, monkeypatch):
    # Simulate the race: a concurrent request created "alice" after our lookup returned nothing.
    session.add(User(handle="alice"))
    session.commit()
    real_find_user = sync_service.find_user
    lookups = []

    def racy_find_user(db, handle):
        lookups.append(handle)
        return None if len(lookups) == 1 else real_find_user(db, handle)

    monkeypatch.setattr(sync_service, "find_user", racy_find_user)
    response = api.post("/api/users/alice/sync")

    assert response.status_code == 200
    assert len(lookups) == 2  # first insert hit the unique constraint, the retry updated the row
    session.expire_all()
    assert count(session, User) == 1
    assert len(session.scalars(select(UserSnapshot)).one().submissions) == 9


def test_slim_submission_keeps_only_used_fields():
    raw = {
        "id": 1, "contestId": 5, "creationTimeSeconds": 10, "relativeTimeSeconds": 60,
        "verdict": "OK", "programmingLanguage": "Python 3", "testset": "TESTS",
        "passedTestCount": 12, "timeConsumedMillis": 30, "memoryConsumedBytes": 1024,
        "author": {"participantType": "CONTESTANT", "members": [{"handle": "alice"}], "ghost": False},
        "problem": {"contestId": 5, "index": "A", "name": "X", "type": "PROGRAMMING",
                    "points": 500.0, "rating": 800, "tags": ["math"]},
    }
    assert slim_submission(raw) == {
        "id": 1, "contestId": 5, "creationTimeSeconds": 10, "relativeTimeSeconds": 60,
        "verdict": "OK", "programmingLanguage": "Python 3",
        "author": {"participantType": "CONTESTANT"},
        "problem": {"contestId": 5, "index": "A", "name": "X", "rating": 800, "tags": ["math"]},
    }


def test_slim_submission_keeps_missing_verdict_missing():
    slim = slim_submission({"id": 1, "problem": {}, "author": {}})
    assert "verdict" not in slim
