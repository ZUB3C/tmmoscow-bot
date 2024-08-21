from datetime import datetime

from sqlalchemy import ForeignKey, PrimaryKeyConstraint
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, Int64, TimestampMixin


class Competitions(Base, TimestampMixin):
    __tablename__ = "competitions"

    id: Mapped[Int64] = mapped_column(primary_key=True, nullable=False)
    title: Mapped[str] = mapped_column(nullable=False)
    event_dates: Mapped[str] = mapped_column(nullable=True)
    location: Mapped[str] = mapped_column(nullable=True)
    views: Mapped[Int64] = mapped_column(nullable=False)
    logo_url: Mapped[str] = mapped_column(nullable=True)
    author: Mapped[str] = mapped_column(nullable=False)
    event_begins_at: Mapped[datetime] = mapped_column(nullable=True)
    event_ends_at: Mapped[datetime] = mapped_column(nullable=True)
    competition_created_at: Mapped[datetime] = mapped_column(nullable=False)
    competition_updated_at: Mapped[datetime] = mapped_column(nullable=False)


class CompetitionVersions(Base, TimestampMixin):
    __tablename__ = "competition_versions"

    competition_id: Mapped[Int64] = mapped_column(ForeignKey("competitions.id"), nullable=False)
    version: Mapped[Int64] = mapped_column()

    __table_args__ = (
        PrimaryKeyConstraint("competition_id", "version", name="pk_competition_version"),
    )
