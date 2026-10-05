import copy
import os
from collections import Counter

# Tests must never touch the development database. Set before any app module is imported.
os.environ["DATABASE_URL"] = "sqlite://"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy.orm import Session, sessionmaker  # noqa: E402

from app import models  # noqa: E402,F401  (registers tables with Base)
from app.cf_client import CodeforcesError, HandleNotFound, get_cf_client  # noqa: E402
from app.db import Base, get_session, make_engine  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture
def engine():
    """In-memory SQLite (make_engine uses StaticPool, so every session sees the same database).

    Set TEST_DATABASE_URL to run the same tests against PostgreSQL (CI does).
    """
    url = os.environ.get("TEST_DATABASE_URL")
    engine = make_engine(url or "sqlite://")
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture
def session(engine):
    with Session(engine, expire_on_commit=False) as session:
        yield session


# ---- Fake Codeforces --------------------------------------------------------------

def make_submission(sub_id, contest, index, verdict, tags, rating=None, t=0, live=False):
    problem = {"contestId": contest, "index": index, "name": f"Problem {contest}{index}", "tags": tags}
    if rating is not None:
        problem["rating"] = rating
    return {
        "id": sub_id,
        "contestId": contest,
        "creationTimeSeconds": t,
        "relativeTimeSeconds": 600,
        "problem": problem,
        "author": {
            "contestId": contest,
            "members": [{"handle": "alice"}],
            "participantType": "CONTESTANT" if live else "PRACTICE",
            "ghost": False,
        },
        "programmingLanguage": "C++20 (GCC 13-64)",
        "verdict": verdict,
        "testset": "TESTS",
        "passedTestCount": 3,
        "timeConsumedMillis": 46,
        "memoryConsumedBytes": 0,
    }


# Newest first, like the real API. Same scenario as tests/test_analysis.py.
ALICE_SUBMISSIONS = [
    make_submission(9, 5, "E", "OK", ["math", "greedy"], t=90),
    make_submission(8, 4, "D", "TIME_LIMIT_EXCEEDED", ["dp"], 1500, t=80, live=True),
    make_submission(7, 3, "C", "WRONG_ANSWER", ["graphs", "dp"], 1600, t=70, live=True),
    make_submission(6, 2, "B", "OK", ["graphs"], 1400, t=60, live=True),
    make_submission(5, 2, "B", "WRONG_ANSWER", ["graphs"], 1400, t=50, live=True),
    make_submission(4, 1, "A", "OK", ["math"], 800, t=40),
    make_submission(3, 1, "A", "OK", ["math"], 800, t=30, live=True),
    make_submission(2, 6, "A", "OK", ["implementation", "*special"], 800, t=20, live=True),
    make_submission(1, 6, "B", "COMPILATION_ERROR", ["greedy"], 1000, t=10, live=True),
]

ALICE_RATING = [
    {"contestId": 1, "contestName": "Round 1", "handle": "alice", "rank": 3000,
     "ratingUpdateTimeSeconds": 1000, "oldRating": 0, "newRating": 400},
    {"contestId": 2, "contestName": "Round 2", "handle": "alice", "rank": 2000,
     "ratingUpdateTimeSeconds": 2000, "oldRating": 400, "newRating": 900},
    {"contestId": 3, "contestName": "Round 3", "handle": "alice", "rank": 900,
     "ratingUpdateTimeSeconds": 3000, "oldRating": 900, "newRating": 1420},
    {"contestId": 4, "contestName": "Round 4", "handle": "alice", "rank": 1500,
     "ratingUpdateTimeSeconds": 4000, "oldRating": 1420, "newRating": 1350},
]

PROBLEMSET = [
    {"contestId": 10, "index": "A", "name": "Ten A", "rating": 1400, "tags": ["dp", "math"], "solvedCount": 500},
    {"contestId": 10, "index": "B", "name": "Ten B", "rating": 1500, "tags": ["dp"], "solvedCount": 900},
    {"contestId": 10, "index": "C", "name": "Ten C", "rating": 1500, "tags": ["graphs", "dp"], "solvedCount": 100},
    {"contestId": 2, "index": "B", "name": "Problem 2B", "rating": 1400, "tags": ["graphs"], "solvedCount": 8000},
    {"contestId": 10, "index": "D", "name": "Ten D", "rating": 2000, "tags": ["dp"], "solvedCount": 50},
    {"contestId": 10, "index": "E", "name": "Ten E", "tags": ["dp"]},
    {"contestId": 10, "index": "F", "name": "Ten F", "rating": 1450, "tags": ["*special", "dp"], "solvedCount": 1},
]


class FakeCodeforces:
    """Stands in for CodeforcesClient. Data is copied so tests can mutate it freely."""

    def __init__(self) -> None:
        self.users = {
            "alice": {
                "info": {"handle": "alice", "rating": 1350, "maxRating": 1420, "rank": "pupil"},
                "rating": copy.deepcopy(ALICE_RATING),
                "submissions": copy.deepcopy(ALICE_SUBMISSIONS),
            }
        }
        self.problems = copy.deepcopy(PROBLEMSET)
        self.calls: Counter[str] = Counter()
        self.fail_with: CodeforcesError | None = None

    def _user(self, handle: str) -> dict:
        if self.fail_with is not None:
            raise self.fail_with
        try:
            return self.users[handle.lower()]
        except KeyError:
            raise HandleNotFound(f"handles: User with handle {handle} not found") from None

    def user_info(self, handle: str) -> dict:
        self.calls["user_info"] += 1
        return copy.deepcopy(self._user(handle)["info"])

    def user_rating(self, handle: str) -> list[dict]:
        self.calls["user_rating"] += 1
        return copy.deepcopy(self._user(handle)["rating"])

    def user_submissions(self, handle: str) -> list[dict]:
        self.calls["user_submissions"] += 1
        return copy.deepcopy(self._user(handle)["submissions"])

    def problemset(self) -> list[dict]:
        self.calls["problemset"] += 1
        if self.fail_with is not None:
            raise self.fail_with
        return copy.deepcopy(self.problems)


@pytest.fixture
def fake_cf() -> FakeCodeforces:
    return FakeCodeforces()


@pytest.fixture
def api(engine, fake_cf):
    """TestClient wired to the test database and the fake Codeforces client."""
    TestSession = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

    def override_session():
        with TestSession() as session:
            yield session

    app.dependency_overrides[get_session] = override_session
    app.dependency_overrides[get_cf_client] = lambda: fake_cf
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()
