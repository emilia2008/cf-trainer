"""Database tables.

The app fetches a user's data from Codeforces once, stores it, and builds the report
from the stored copy. That keeps reports fast and avoids hitting the API rate limit.

`User` is complete as an example. Design the rest yourself (LEARNING.md, section 2).
"""

from datetime import datetime

from sqlalchemy import DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    handle: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    rating: Mapped[int | None] = mapped_column(Integer)
    max_rating: Mapped[int | None] = mapped_column(Integer)
    rank: Mapped[str | None] = mapped_column(String(64))
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


# TODO: store each user's submissions and rating history.
#
# Two common designs. Pick one and be ready to defend it in an interview:
#   A) Normalised tables: submissions (one row per submission) and rating_changes
#      (one row per contest), each with a foreign key to users.
#      + can query with SQL (e.g. "solves per month")   - more code to write and keep in sync
#   B) One snapshot table: user_id + JSON columns (submissions, rating_history) + fetched_at.
#      + simple, the analysis functions take the API data as is   - cannot query inside easily
#
# Either way, re-syncing a user must replace their old data, not duplicate it.
