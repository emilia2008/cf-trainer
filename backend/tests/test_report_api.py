"""API tests through TestClient.

app.dependency_overrides swaps in an in-memory SQLite database and a fake Codeforces client
(see conftest.py), so these tests never call the real API.
"""

import pytest
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


# ---- Report -------------------------------------------------------------------------

REPORT_SECTIONS = {
    "handle", "last_synced_at", "overview", "rating_trend", "difficulty", "topics",
    "weak_topics", "habits", "upsolve", "recommendations",
}


def test_report_after_sync_has_every_section(api):
    assert api.post("/api/users/alice/sync").status_code == 200
    response = api.get("/api/users/alice/report")

    assert response.status_code == 200
    assert set(response.json()) == REPORT_SECTIONS


def test_report_before_sync_returns_404(api, fake_cf):
    response = api.get("/api/users/alice/report")

    assert response.status_code == 404
    assert "Sync it first" in response.json()["detail"]
    assert fake_cf.calls["problemset"] == 0  # no Codeforces call for an unknown user


def test_report_numbers_are_correct(api):
    api.post("/api/users/alice/sync")
    report = api.get("/api/users/ALICE/report").json()  # lookup is case-insensitive

    assert report["handle"] == "alice"
    assert report["overview"] == {
        "handle": "alice", "rank": "Pupil", "rating": 1350, "max_rating": 1420,
        "max_rank": "Specialist", "next_rank": "Specialist", "next_threshold": 1400,
        "points_to_next": 50, "solved_count": 4, "contests": 4,
    }

    trend = report["rating_trend"]
    assert (trend["contests"], trend["current"], trend["max_rating"]) == (4, 1350, 1420)
    assert (trend["recent_window"], trend["recent_change"]) == (4, 1350)
    assert (trend["best_gain"], trend["worst_drop"]) == (520, -70)
    assert [p["delta"] for p in trend["history"]] == [400, 500, 520, -70]
    assert trend["history"][2]["contest_name"] == "Round 3"

    difficulty = report["difficulty"]
    assert difficulty["buckets"] == [
        {"rating": 800, "solved": 2, "attempted": 2},
        {"rating": 1000, "solved": 0, "attempted": 1},
        {"rating": 1400, "solved": 1, "attempted": 1},
        {"rating": 1500, "solved": 0, "attempted": 1},
        {"rating": 1600, "solved": 0, "attempted": 1},
    ]
    assert difficulty["comfort_rating"] is None
    assert difficulty["comfort_min_solved"] == 21
    assert difficulty["target_range"] == {"lo": 1400, "hi": 1600}
    assert difficulty["problems_in_range"] == 5

    topics = {t["tag"]: t for t in report["topics"]}
    assert [t["tag"] for t in report["topics"]] == ["math", "graphs", "greedy", "implementation", "dp"]
    assert topics["graphs"] == {"tag": "graphs", "solved": 1, "attempted": 2,
                                "first_try_rate": 0.0, "max_solved_rating": 1400}

    weak = report["weak_topics"]
    assert [w["tag"] for w in weak] == ["dp", "graphs", "math"]
    assert weak[0]["score"] == pytest.approx(0.8)
    assert weak[0]["reason"] == (
        "Appears in 80% of problems rated 1400–1600, and you have not solved any of them yet."
    )
    assert "solved only 1 problem" in weak[1]["reason"]
    assert all(w["resources"] and w["resources"][0]["url"].startswith("https://") for w in weak)

    habits = report["habits"]
    assert (habits["total_submissions"], habits["accepted"], habits["failed"]) == (9, 5, 4)
    assert habits["first_try_rate"] == pytest.approx(0.75)
    assert [(v["verdict"], v["count"]) for v in habits["verdicts"]] == [
        ("WRONG_ANSWER", 2), ("COMPILATION_ERROR", 1), ("TIME_LIMIT_EXCEEDED", 1),
    ]
    assert habits["verdicts"][0]["label"] == "Wrong answer"
    assert habits["verdicts"][0]["share"] == pytest.approx(0.5)
    assert all(v["advice"] for v in habits["verdicts"])  # each is above 15% of failures
    assert habits["live_contests"] == 5
    assert habits["contest_level"] == [{"letter": "A", "rate": 0.4}, {"letter": "B", "rate": 0.2}]
    assert habits["usually_solves_up_to"] is None

    upsolve = report["upsolve"]
    assert upsolve["total"] == 3
    assert [f"{p['contest_id']}{p['index']}" for p in upsolve["problems"]] == ["6B", "4D", "3C"]
    assert upsolve["problems"][0]["url"] == "https://codeforces.com/problemset/problem/6/B"

    recs = report["recommendations"]
    assert [f"{p['contest_id']}{p['index']}" for p in recs] == ["10A", "10C", "10F", "10B"]
    assert recs[0]["url"] == "https://codeforces.com/problemset/problem/10/A"
    assert recs[0]["matched_tags"] == ["dp", "math"]
    assert recs[0]["solved_count"] == 500
    assert "*special" not in recs[2]["tags"]


def test_verdict_advice_only_above_15_percent(api, fake_cf):
    subs = fake_cf.users["alice"]["submissions"]
    wrong_answer = next(s for s in subs if s["verdict"] == "WRONG_ANSWER")
    # Seven more wrong answers: WA 9, TLE 1, CE 1 -> TLE and CE drop to 1/11 (about 9%).
    for i in range(7):
        subs.insert(0, dict(wrong_answer, id=100 + i, creationTimeSeconds=200 + i))
    api.post("/api/users/alice/sync")
    verdicts = {v["verdict"]: v for v in api.get("/api/users/alice/report").json()["habits"]["verdicts"]}

    assert verdicts["WRONG_ANSWER"]["advice"]
    assert verdicts["TIME_LIMIT_EXCEEDED"]["advice"] is None
    assert verdicts["COMPILATION_ERROR"]["advice"] is None


def test_problem_list_is_fetched_once_across_reports(api, fake_cf):
    api.post("/api/users/alice/sync")
    for _ in range(3):
        assert api.get("/api/users/alice/report").status_code == 200
    assert fake_cf.calls["problemset"] == 1


def test_report_problemset_failure_returns_502(api, fake_cf):
    api.post("/api/users/alice/sync")
    fake_cf.fail_with = CodeforcesError("Codeforces API error: down for maintenance")

    response = api.get("/api/users/alice/report")

    assert response.status_code == 502
    assert "problem list" in response.json()["detail"]


def test_report_for_user_without_activity(api, fake_cf):
    fake_cf.users["newbie"] = {"info": {"handle": "newbie"}, "rating": [], "submissions": []}
    assert api.post("/api/users/newbie/sync").status_code == 200

    report = api.get("/api/users/newbie/report").json()

    assert report["overview"]["rank"] == "Newbie"
    assert report["overview"]["points_to_next"] == 1200
    assert report["rating_trend"]["contests"] == 0
    assert report["rating_trend"]["history"] == []
    assert report["difficulty"]["target_range"] == {"lo": 900, "hi": 1100}
    assert report["topics"] == []
    assert report["habits"]["contest_level"] == []
    assert report["upsolve"] == {"total": 0, "problems": []}
    assert report["weak_topics"] == []  # the fake problem set has nothing rated 900-1100
    assert report["recommendations"] == []


def test_gym_problems_link_to_gym():
    from app.services.report import problem_url

    assert problem_url(1850, "C") == "https://codeforces.com/problemset/problem/1850/C"
    assert problem_url(102035, "A") == "https://codeforces.com/gym/102035/problem/A"


def test_openapi_documents_both_endpoints(api):
    paths = api.get("/openapi.json").json()["paths"]
    assert "post" in paths["/api/users/{handle}/sync"]
    assert "get" in paths["/api/users/{handle}/report"]


@pytest.mark.parametrize("solves_at_1500, expected_range", [
    (20, {"lo": 1400, "hi": 1600}),  # not comfortable yet: the target follows the rating (1350)
    (21, {"lo": 1600, "hi": 1800}),  # more than 20 solves at 1500: the target moves up
])
def test_target_moves_up_only_after_more_than_20_solves(api, fake_cf, solves_at_1500, expected_range):
    from conftest import make_submission

    subs = [make_submission(i, 100 + i, "A", "OK", ["dp"], 1500, t=i) for i in range(solves_at_1500)]
    fake_cf.users["grinder"] = {
        "info": {"handle": "grinder", "rating": 1350, "maxRating": 1350, "rank": "pupil"},
        "rating": [],
        "submissions": subs[::-1],
    }
    api.post("/api/users/grinder/sync")
    difficulty = api.get("/api/users/grinder/report").json()["difficulty"]

    assert difficulty["target_range"] == expected_range
    assert difficulty["comfort_rating"] == (1500 if solves_at_1500 > 20 else None)
