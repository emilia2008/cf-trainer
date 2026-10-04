"""Database tables.

`User` is complete as an example. Design the rest yourself (LEARNING.md, section 2):
think about which columns you need, the primary key, and which columns need an index.
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
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


# TODO: a table for problems (contest_id + index identify a problem; it has a rating and tags).
#       Hint: tags are a list. Store them in a separate table, or as a comma-separated string
#       to start with. Be ready to explain the trade-off in an interview.

# TODO: a table for each user's solved problems (which user, which problem, when solved).
#       Make sure the same problem cannot be stored twice for one user.
