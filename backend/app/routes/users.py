"""HTTP endpoints. Each one returns 501 until you implement it."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_session

router = APIRouter(tags=["users"])


def _todo() -> HTTPException:
    return HTTPException(status_code=501, detail="Not implemented yet")


@router.post("/users/{handle}")
def register_user(handle: str, session: Session = Depends(get_session)):
    """Add a Codeforces handle and sync its data.

    TODO: check the handle exists (CodeforcesClient.user_info), create or update the User row,
    fetch submissions, store solved problems, set last_synced_at. Return the user.
    Return 404 if Codeforces does not know the handle.
    """
    raise _todo()


@router.get("/users/{handle}/stats")
def get_stats(handle: str, session: Session = Depends(get_session)):
    """TODO: return the user's rating and stats.tag_stats(...) as JSON. 404 if not registered."""
    raise _todo()


@router.get("/users/{handle}/recommendations")
def get_recommendations(handle: str, limit: int = 5, session: Session = Depends(get_session)):
    """TODO: weakest tags + stats.recommend(...). Cache the full problem list:
    it is large and changes rarely (refresh at most once a day)."""
    raise _todo()


@router.get("/leaderboard")
def get_leaderboard(session: Session = Depends(get_session)):
    """TODO: all registered users sorted by problems solved in the last 7 days, then rating."""
    raise _todo()
