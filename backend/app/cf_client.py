"""Client for the public Codeforces API (https://codeforces.com/apiHelp).

Endpoints you need:
  GET /user.info?handles=<handle>     -> rating, maxRating, rank
  GET /user.rating?handle=<handle>    -> rating change after every rated contest (oldest first)
  GET /user.status?handle=<handle>    -> all submissions, newest first
  GET /problemset.problems            -> {"problems": [...], "problemStatistics": [...]}

Every response looks like {"status": "OK", "result": ...} or {"status": "FAILED", "comment": "..."}.
"""

import httpx

from app.config import settings


class CodeforcesError(Exception):
    """Raised when Codeforces returns status FAILED or the request fails."""


class HandleNotFound(CodeforcesError):
    """Raised when Codeforces does not know the handle."""


class CodeforcesClient:
    def __init__(self, base_url: str = settings.codeforces_api_base) -> None:
        self._http = httpx.Client(base_url=base_url, timeout=30.0)

    def _get(self, method: str, **params: str) -> object:
        # TODO:
        #   1. Wait so that two calls are at least settings.codeforces_min_interval_seconds apart
        #      (store the time of the last call; use time.monotonic and time.sleep).
        #   2. Send the GET request, raise CodeforcesError on HTTP errors.
        #   3. If body["status"] != "OK": raise HandleNotFound when the comment says the handle
        #      was not found, otherwise CodeforcesError. Return body["result"].
        raise NotImplementedError

    def user_info(self, handle: str) -> dict:
        # TODO: call user.info and return the first (only) user object.
        raise NotImplementedError

    def user_rating(self, handle: str) -> list[dict]:
        # TODO: call user.rating and return the list of rating changes.
        raise NotImplementedError

    def user_submissions(self, handle: str) -> list[dict]:
        # TODO: call user.status and return the list of submissions.
        raise NotImplementedError

    def problemset(self) -> list[dict]:
        # TODO: call problemset.problems. Merge each problem's solvedCount from
        # "problemStatistics" (match on contestId + index) into the problem dict.
        raise NotImplementedError
