"""CodeforcesClient tests. httpx.MockTransport answers every request, so nothing hits the network."""

import threading
import time

import httpx
import pytest

from app.cf_client import CodeforcesClient, CodeforcesError, HandleNotFound, RateLimiter


def make_client(handler, **kwargs) -> CodeforcesClient:
    return CodeforcesClient(
        "https://cf.test/api",
        transport=httpx.MockTransport(handler),
        limiter=RateLimiter(0),
        **kwargs,
    )


def ok(result) -> httpx.Response:
    return httpx.Response(200, json={"status": "OK", "result": result})


def failed(comment: str, status_code: int = 400) -> httpx.Response:
    return httpx.Response(status_code, json={"status": "FAILED", "comment": comment})


# ---- _get -----------------------------------------------------------------------

def test_ok_returns_result_and_sends_params():
    seen = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return ok([{"oldRating": 0, "newRating": 400}])

    assert make_client(handler).user_rating("alice") == [{"oldRating": 0, "newRating": 400}]
    assert seen[0].url.path == "/api/user.rating"
    assert seen[0].url.params["handle"] == "alice"


def test_failed_status_raises_codeforces_error():
    client = make_client(lambda request: failed("contestId: Contest with id 1 not started"))
    with pytest.raises(CodeforcesError) as info:
        client.user_rating("alice")
    assert not isinstance(info.value, HandleNotFound)
    assert "not started" in str(info.value)


@pytest.mark.parametrize(
    "comment",
    [
        "handles: User with handle nobody_xyz not found",
        "handle: User with handle nobody_xyz not found",
        "handle: Field should contain between 3 and 24 characters, inclusive",
    ],
)
def test_unknown_handle_raises_handle_not_found(comment):
    client = make_client(lambda request: failed(comment))
    with pytest.raises(HandleNotFound):
        client.user_info("nobody_xyz")


def test_http_500_raises_codeforces_error():
    client = make_client(lambda request: httpx.Response(500, text="<html>Internal error</html>"))
    with pytest.raises(CodeforcesError, match="HTTP 500"):
        client.user_submissions("alice")


def test_network_error_raises_codeforces_error():
    def handler(request):
        raise httpx.ConnectError("connection refused", request=request)

    with pytest.raises(CodeforcesError, match="Could not reach Codeforces"):
        make_client(handler).user_submissions("alice")


def test_call_limit_is_retried():
    responses = iter([failed("Call limit exceeded"), ok([])])
    calls = []

    def handler(request):
        calls.append(request)
        return next(responses)

    assert make_client(handler).user_submissions("alice") == []
    assert len(calls) == 2


def test_call_limit_gives_up_after_max_retries():
    calls = []

    def handler(request):
        calls.append(request)
        return failed("Call limit exceeded")

    with pytest.raises(CodeforcesError, match="Call limit exceeded"):
        make_client(handler, max_retries=2).user_submissions("alice")
    assert len(calls) == 3


# ---- Endpoints --------------------------------------------------------------------

def test_user_info_returns_first_user():
    def handler(request):
        assert request.url.params["handles"] == "alice"
        return ok([{"handle": "alice", "rating": 1500, "rank": "specialist"}])

    assert make_client(handler).user_info("alice")["rating"] == 1500


def test_user_info_empty_result_is_handle_not_found():
    with pytest.raises(HandleNotFound):
        make_client(lambda request: ok([])).user_info("alice")


def test_problemset_merges_solved_count():
    result = {
        "problems": [
            {"contestId": 1, "index": "A", "rating": 800, "tags": ["math"]},
            {"contestId": 1, "index": "B", "tags": []},
            {"contestId": 2, "index": "A", "rating": 1200, "tags": ["dp"]},
        ],
        "problemStatistics": [
            {"contestId": 2, "index": "A", "solvedCount": 42},
            {"contestId": 1, "index": "A", "solvedCount": 9000},
        ],
    }
    problems = make_client(lambda request: ok(result)).problemset()
    by_key = {f"{p['contestId']}{p['index']}": p for p in problems}
    assert by_key["1A"]["solvedCount"] == 9000
    assert by_key["2A"]["solvedCount"] == 42
    assert "solvedCount" not in by_key["1B"]
    assert by_key["1A"]["tags"] == ["math"]


# ---- Rate limiting ------------------------------------------------------------------

class FakeClock:
    def __init__(self) -> None:
        self.now = 0.0
        self.sleeps: list[float] = []

    def __call__(self) -> float:
        return self.now

    def sleep(self, seconds: float) -> None:
        self.sleeps.append(seconds)
        self.now += seconds


def test_rate_limiter_spaces_calls():
    clock = FakeClock()
    limiter = RateLimiter(2.0, clock=clock, sleep=clock.sleep)

    assert limiter.wait() == 0.0       # first call goes straight through
    clock.now = 0.5
    assert limiter.wait() == 2.0       # waits 1.5 s
    assert limiter.wait() == 4.0       # back-to-back: waits the full 2 s
    clock.now = 10.0
    assert limiter.wait() == 10.0      # long gap: no wait
    assert clock.sleeps == [1.5, 2.0]


def test_rate_limiter_is_thread_safe():
    interval = 0.05
    limiter = RateLimiter(interval)
    starts: list[float] = []
    lock = threading.Lock()

    def worker():
        start = limiter.wait()
        with lock:
            starts.append(start)

    threads = [threading.Thread(target=worker) for _ in range(5)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    starts.sort()
    gaps = [b - a for a, b in zip(starts, starts[1:])]
    assert len(starts) == 5
    assert all(gap >= interval - 1e-3 for gap in gaps), gaps


def test_client_waits_for_limiter_before_every_request():
    clock = FakeClock()
    client = CodeforcesClient(
        "https://cf.test/api",
        transport=httpx.MockTransport(lambda request: ok([])),
        limiter=RateLimiter(2.0, clock=clock, sleep=clock.sleep),
    )
    client.user_rating("alice")
    client.user_submissions("alice")
    client.user_rating("bob")
    assert clock.sleeps == [2.0, 2.0]


def test_rate_limiter_real_clock_smoke():
    interval = 0.05
    limiter = RateLimiter(interval)
    began = time.perf_counter()
    for _ in range(3):
        limiter.wait()
    elapsed = time.perf_counter() - began
    # time.monotonic only ticks every ~16 ms on Windows, so the limiter may start the
    # schedule up to one tick early (it does not accumulate across calls).
    tick = time.get_clock_info("monotonic").resolution
    assert elapsed >= 2 * interval - tick - 1e-3
