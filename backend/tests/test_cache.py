"""ProblemCache tests. The clock is injected, so "24 hours later" takes no real time."""

import threading
import time

import pytest

from app.cf_client import CodeforcesError
from app.services.report import ProblemCache

DAY = 24 * 60 * 60


class Clock:
    def __init__(self) -> None:
        self.now = 1000.0

    def __call__(self) -> float:
        return self.now


class Fetcher:
    def __init__(self) -> None:
        self.calls = 0
        self.error: Exception | None = None

    def __call__(self) -> list[dict]:
        self.calls += 1
        if self.error is not None:
            raise self.error
        return [{"contestId": 1, "index": "A", "version": self.calls}]


def test_second_call_within_ttl_uses_cache():
    clock, fetch = Clock(), Fetcher()
    cache = ProblemCache(clock=clock)

    first = cache.get(fetch)
    clock.now += DAY - 1
    second = cache.get(fetch)

    assert fetch.calls == 1
    assert second is first


def test_refetches_after_24_hours():
    clock, fetch = Clock(), Fetcher()
    cache = ProblemCache(clock=clock)

    cache.get(fetch)
    clock.now += DAY
    problems = cache.get(fetch)

    assert fetch.calls == 2
    assert problems[0]["version"] == 2


def test_default_ttl_is_24_hours():
    assert ProblemCache().ttl_seconds == DAY


def test_error_on_cold_cache_propagates():
    fetch = Fetcher()
    fetch.error = CodeforcesError("down")
    with pytest.raises(CodeforcesError):
        ProblemCache(clock=Clock()).get(fetch)


def test_failed_refresh_serves_stale_copy_then_retries_later():
    clock, fetch = Clock(), Fetcher()
    cache = ProblemCache(clock=clock, retry_seconds=300)
    cache.get(fetch)

    clock.now += DAY
    fetch.error = CodeforcesError("down")
    assert cache.get(fetch)[0]["version"] == 1      # stale copy instead of an error
    assert fetch.calls == 2

    clock.now += 299
    cache.get(fetch)
    assert fetch.calls == 2                          # no retry storm while Codeforces is down

    clock.now += 1
    fetch.error = None
    assert cache.get(fetch)[0]["version"] == 3      # retried and refreshed
    clock.now += DAY - 1
    cache.get(fetch)
    assert fetch.calls == 3                          # fresh copy gets the full TTL again


def test_clear_forces_refetch():
    clock, fetch = Clock(), Fetcher()
    cache = ProblemCache(clock=clock)
    cache.get(fetch)
    cache.clear()
    cache.get(fetch)
    assert fetch.calls == 2


def test_concurrent_cold_requests_fetch_once():
    calls = []

    def slow_fetch():
        calls.append(1)
        time.sleep(0.05)
        return [{"contestId": 1, "index": "A"}]

    cache = ProblemCache()
    results = []
    threads = [threading.Thread(target=lambda: results.append(cache.get(slow_fetch))) for _ in range(5)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert len(calls) == 1
    assert len(results) == 5
    assert all(result is results[0] for result in results)
