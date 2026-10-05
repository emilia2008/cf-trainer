from urllib.parse import urlparse

import pytest

from app.resources import (
    GENERAL_RESOURCES,
    RESOURCES,
    VERDICT_ADVICE,
    resources_for,
    verdict_label,
)

REQUIRED_TAGS = [
    "dp", "graphs", "greedy", "math", "number theory", "strings", "trees", "sortings",
    "constructive algorithms", "two pointers", "brute force", "implementation",
    "data structures", "dfs and similar", "shortest paths", "bitmasks", "combinatorics",
    "binary search", "dsu",
]
ALLOWED = {
    "cp-algorithms.com": "/",
    "usaco.guide": "/",
    "cses.fi": "/problemset/",
}


@pytest.mark.parametrize("tag", REQUIRED_TAGS)
def test_required_tags_have_resources(tag):
    assert RESOURCES[tag], tag


def test_links_use_allowed_sites_only():
    links = [link for links in RESOURCES.values() for link in links] + GENERAL_RESOURCES
    for link in links:
        url = urlparse(link["url"])
        assert url.scheme == "https", link
        assert url.netloc in ALLOWED, link
        assert url.path.startswith(ALLOWED[url.netloc]), link
        assert link["title"].strip(), link


def test_unknown_tag_falls_back_to_general_resources():
    assert resources_for("geometry") == GENERAL_RESOURCES
    assert resources_for("dp") == RESOURCES["dp"]


def test_verdict_labels_and_advice():
    assert verdict_label("WRONG_ANSWER") == "Wrong answer"
    assert verdict_label("SOME_NEW_VERDICT") == "Some new verdict"
    for verdict in ("WRONG_ANSWER", "TIME_LIMIT_EXCEEDED", "RUNTIME_ERROR", "MEMORY_LIMIT_EXCEEDED"):
        assert VERDICT_ADVICE[verdict]
