from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, Int64, TimestampMixin


class Subscriptions(Base, TimestampMixin):
    __tablename__ = "subscriptions"

    id: Mapped[Int64] = mapped_column(primary_key=True, nullable=False)
    user_id: Mapped[Int64] = mapped_column(ForeignKey("users.id"), nullable=False)
    competition_id: Mapped[Int64] = mapped_column(ForeignKey("competitions.id"), nullable=False)
