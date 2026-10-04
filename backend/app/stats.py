"""Pure functions: no database, no network. Easy to test, and the core logic of the app.

A submission from the Codeforces API looks like (only the fields you need):
    {
        "verdict": "OK",                       # "OK" means accepted
        "creationTimeSeconds": 1727000000,
        "problem": {
            "contestId": 1850, "index": "C",
            "rating": 1200,                    # may be missing for new problems
            "tags": ["greedy", "math"],
        },
    }
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class TagStat:
    tag: str
    solved: int          # distinct accepted problems with this tag
    attempted: int       # distinct problems with this tag tried at least once
    avg_rating: float    # average rating of the solved problems (0.0 if none have a rating)


def problem_key(problem: dict) -> str:
    """Unique id for a problem, e.g. '1850C'. Provided."""
    return f"{problem.get('contestId', '')}{problem.get('index', '')}"


def solved_problems(submissions: list[dict]) -> dict[str, dict]:
    """Return {problem_key: problem} for every problem with at least one 'OK' verdict.

    The same problem may be accepted several times; count it once.
    """
    # TODO
    raise NotImplementedError


def tag_stats(submissions: list[dict]) -> list[TagStat]:
    """One TagStat per tag seen in the submissions, sorted by `solved` descending, then tag name."""
    # TODO
    raise NotImplementedError


def weakest_tags(stats: list[TagStat], k: int = 3, min_attempted: int = 1) -> list[str]:
    """The k tags the user is weakest at.

    Your choice how to define "weak" (write it down in README). Suggested start:
    lowest solved/attempted ratio among tags with attempted >= min_attempted,
    ties broken by fewer solved, then tag name.
    """
    # TODO
    raise NotImplementedError


def recommend(
    all_problems: list[dict],
    solved_keys: set[str],
    weak_tags: list[str],
    user_rating: int | None,
    limit: int = 5,
) -> list[dict]:
    """Suggest up to `limit` unsolved problems that have at least one weak tag,
    with rating in [user_rating - 100, user_rating + 200], easiest first.
    Treat a user with no rating (None) as 800. Skip problems that have no rating.
    """
    # TODO
    raise NotImplementedError
