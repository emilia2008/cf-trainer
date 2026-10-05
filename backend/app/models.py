"""Database tables.

The app fetches a user's data from Codeforces once, stores it, and builds the report
from the stored copy. That keeps reports fast and avoids hitting the API rate limit.

Design: one `users` row per handle plus one `user_snapshots` row per user holding the raw
submissions and rating history as JSON (JSONB on PostgreSQL). The analysis functions take
the API data as is, so a snapshot is the simplest faithful copy. `user_snapshots.user_id`
is unique, so re-syncing updates the existing snapshot instead of adding a duplicate.
"""

from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base

# Plain JSON on SQLite, binary JSONB on PostgreSQL (smaller, faster to read back).
JSONType = JSON().with_variant(JSONB(), "postgresql")


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    handle: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    rating: Mapped[int | None] = mapped_column(Integer)
    max_rating: Mapped[int | None] = mapped_column(Integer)
    rank: Mapped[str | None] = mapped_column(String(64))
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    snapshot: Mapped["UserSnapshot | None"] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan"
    )


class UserSnapshot(Base):
    """The latest copy of a user's Codeforces data. Exactly one per user."""

    __tablename__ = "user_snapshots"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True, index=True
    )
    submissions: Mapped[list[dict]] = mapped_column(JSONType, default=list)     # newest first
    rating_history: Mapped[list[dict]] = mapped_column(JSONType, default=list)  # oldest first
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    user: Mapped[User] = relationship(back_populates="snapshot")
