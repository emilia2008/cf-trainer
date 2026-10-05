"""HTTP endpoints. Logic lives in app/services; routes only translate errors to status codes."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy.orm import Session

from app.cf_client import CodeforcesClient, CodeforcesError, HandleNotFound, get_cf_client
from app.db import get_session
from app.schemas import SyncResult
from app.services import sync as sync_service

router = APIRouter(tags=["report"])

# Codeforces handles use Latin letters, digits, '_', '-' and '.'. Rejecting anything else
# also stops "a;b" from turning into a multi-user user.info call.
Handle = Annotated[
    str,
    Path(pattern=r"^[A-Za-z0-9_.\-]{1,64}$", description="Codeforces handle, e.g. tourist"),
]


def _todo() -> HTTPException:
    return HTTPException(status_code=501, detail="Not implemented yet")


@router.post(
    "/users/{handle}/sync",
    response_model=SyncResult,
    responses={404: {"description": "Unknown handle"}, 502: {"description": "Codeforces error"}},
)
def sync_user(
    handle: Handle,
    session: Session = Depends(get_session),
    client: CodeforcesClient = Depends(get_cf_client),
) -> SyncResult:
    """Fetch the user's info, rating history and submissions from Codeforces and store them."""
    try:
        user = sync_service.sync_user(session, client, handle)
    except HandleNotFound:
        raise HTTPException(status_code=404, detail=f"Codeforces handle '{handle}' not found")
    except CodeforcesError as exc:
        raise HTTPException(status_code=502, detail=str(exc))
    return SyncResult(
        handle=user.handle,
        rating=user.rating,
        max_rating=user.max_rating,
        rank=user.rank,
        last_synced_at=user.last_synced_at,
        submissions=len(user.snapshot.submissions),
        contests=len(user.snapshot.rating_history),
    )


@router.get("/users/{handle}/report")
def get_report(handle: Handle, session: Session = Depends(get_session)):
    """The full analysis for one user, built from stored data. 404 if never synced."""
    raise _todo()
