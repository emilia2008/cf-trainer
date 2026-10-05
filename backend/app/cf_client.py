"""Client for the public Codeforces API (https://codeforces.com/apiHelp).

Endpoints used:
  GET /user.info?handles=<handle>     -> rating, maxRating, rank
  GET /user.rating?handle=<handle>    -> rating change after every rated contest (oldest first)
  GET /user.status?handle=<handle>    -> all submissions, newest first
  GET /problemset.problems            -> {"problems": [...], "problemStatistics": [...]}

Every response looks like {"status": "OK", "result": ...} or {"status": "FAILED", "comment": "..."}.
Codeforces allows about one call every two seconds, so all calls go through a shared RateLimiter.
"""

import threading
import time
from collections.abc import Callable
from functools import lru_cache

import httpx

from app.config import settings


class CodeforcesError(Exception):
    """Raised when Codeforces returns status FAILED or the request fails."""


class HandleNotFound(CodeforcesError):
    """Raised when Codeforces does not know the handle."""


class RateLimiter:
    """Spaces calls at least `min_interval` seconds apart, across all threads.

    The lock is held while sleeping, so concurrent callers queue up and go one at a time.
    `clock` and `sleep` are injectable so tests do not have to wait for real.
    """

    def __init__(
        self,
        min_interval: float,
        clock: Callable[[], float] = time.monotonic,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self.min_interval = min_interval
        self._clock = clock
        self._sleep = sleep
        self._lock = threading.Lock()
        self._next_allowed: float | None = None

    def wait(self) -> float:
        """Block until a call is allowed. Returns the time the call was allowed to start."""
        with self._lock:
            now = self._clock()
            if self._next_allowed is not None and now < self._next_allowed:
                self._sleep(self._next_allowed - now)
                now = max(self._clock(), self._next_allowed)
            self._next_allowed = now + self.min_interval
            return now


# One limiter per process: every client instance shares the same budget.
_shared_limiter = RateLimiter(settings.codeforces_min_interval_seconds)


def _is_handle_error(comment: str) -> bool:
    # e.g. "handles: User with handle xyz not found" (user.info)
    #      "handle: User with handle xyz not found" (user.rating, user.status)
    #      "handle: Field should contain between 3 and 24 characters, inclusive"
    lowered = comment.lower()
    return lowered.startswith(("handle:", "handles:")) or (
        "handle" in lowered and "not found" in lowered
    )


def _is_call_limit(comment: str) -> bool:
    return "call limit exceeded" in comment.lower()


class CodeforcesClient:
    def __init__(
        self,
        base_url: str = settings.codeforces_api_base,
        *,
        limiter: RateLimiter | None = None,
        transport: httpx.BaseTransport | None = None,
        timeout: float = 30.0,
        max_retries: int = 2,
    ) -> None:
        self._http = httpx.Client(
            base_url=base_url,
            timeout=timeout,
            transport=transport,
            headers={"User-Agent": "cf-trainer/1.0"},
        )
        self._limiter = limiter or _shared_limiter
        self._max_retries = max_retries

    def close(self) -> None:
        self._http.close()

    def _fetch(self, method: str, params: dict[str, str]) -> dict:
        """One HTTP call. Returns the JSON body; raises CodeforcesError if there is none."""
        try:
            response = self._http.get(f"/{method}", params=params)
        except httpx.HTTPError as exc:
            raise CodeforcesError(f"Could not reach Codeforces: {exc}") from exc
        try:
            body = response.json()
        except ValueError:
            body = None
        # Codeforces answers FAILED calls with HTTP 400 plus a JSON body, so read the body first
        # and only fall back to the status code when there is no usable body (e.g. a 502 page).
        if not isinstance(body, dict) or "status" not in body:
            raise CodeforcesError(f"Unexpected response from Codeforces (HTTP {response.status_code})")
        return body

    def _get(self, method: str, **params: str) -> object:
        retries = 0
        while True:
            self._limiter.wait()
            body = self._fetch(method, params)
            if body["status"] == "OK":
                return body.get("result")
            comment = str(body.get("comment") or "unknown error")
            if _is_call_limit(comment) and retries < self._max_retries:
                retries += 1  # the limiter spaces out the retry
                continue
            if _is_handle_error(comment):
                raise HandleNotFound(comment)
            raise CodeforcesError(f"Codeforces API error: {comment}")

    def user_info(self, handle: str) -> dict:
        users = self._get("user.info", handles=handle)
        if not users:
            raise HandleNotFound(f"User with handle {handle} not found")
        return users[0]

    def user_rating(self, handle: str) -> list[dict]:
        return self._get("user.rating", handle=handle)

    def user_submissions(self, handle: str) -> list[dict]:
        return self._get("user.status", handle=handle)

    def problemset(self) -> list[dict]:
        """All problems, each with "solvedCount" merged in from problemStatistics."""
        result = self._get("problemset.problems")
        solved_count = {
            (s.get("contestId"), s.get("index")): s["solvedCount"]
            for s in result.get("problemStatistics", [])
            if "solvedCount" in s
        }
        problems = []
        for problem in result.get("problems", []):
            merged = dict(problem)
            count = solved_count.get((problem.get("contestId"), problem.get("index")))
            if count is not None:
                merged["solvedCount"] = count
            problems.append(merged)
        return problems


@lru_cache(maxsize=1)
def get_cf_client() -> CodeforcesClient:
    """FastAPI dependency: one client per process, so connections and the rate limit are shared.

    Tests replace it through app.dependency_overrides.
    """
    return CodeforcesClient()
