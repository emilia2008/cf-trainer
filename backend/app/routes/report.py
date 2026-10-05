"""HTTP endpoints. Each one returns 501 until you implement it."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_session

router = APIRouter(tags=["report"])


def _todo() -> HTTPException:
    return HTTPException(status_code=501, detail="Not implemented yet")


@router.post("/users/{handle}/sync")
def sync_user(handle: str, session: Session = Depends(get_session)):
    """Fetch the user's info, rating history and submissions from Codeforces and store them.

    TODO: put the logic in app/services/sync.py and call it from here.
    404 if the handle does not exist. Return the user's handle, rating and last_synced_at.
    """
    raise _todo()


@router.get("/users/{handle}/report")
def get_report(handle: str, session: Session = Depends(get_session)):
    """The full analysis for one user, built from stored data. 404 if never synced.

    TODO: put the logic in app/services/report.py. Suggested JSON sections:
      overview         rank_info, rating, max rating, problems solved
      rating_trend     rating_trend(...) plus the raw history for a chart
      difficulty       difficulty_profile(...), comfort_rating(...), target_range(...)
      topics           tag_stats(...)
      weak_topics      weak_topics(...) with RESOURCES for each tag
      habits           verdict_breakdown(...) with VERDICT_ADVICE, contest_level(...)
      upsolve          upsolve_list(...) (first 10)
      recommendations  recommend(...)
    The full problem list is large and changes rarely: cache it (refresh at most once a day).
    """
    raise _todo()
