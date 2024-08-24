import enum

from sqlalchemy import Enum, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, Int64, TimestampMixin


class ContentBlocks(Base, TimestampMixin):
    __tablename__ = "content_blocks"

    id: Mapped[Int64] = mapped_column(primary_key=True, nullable=False)
    competition_id: Mapped[Int64] = mapped_column(
        ForeignKey("competitions.id"), unique=True, nullable=False
    )
    competition_version_id: Mapped[Int64] = mapped_column(nullable=False)
    position: Mapped[Int64] = mapped_column(nullable=False)
    title: Mapped[str] = mapped_column(nullable=False)

    __table_args__ = (
        UniqueConstraint(
            "competition_version_id", "position", name="uq_competition_version_position"
        ),
    )


class ContentLineTypes(enum.Enum):
    CONTENT_LINE = "ContentLine"
    CONTENT_SUBTITLE = "ContentSubtitle"


class ContentLines(Base, TimestampMixin):
    __tablename__ = "content_lines"

    id: Mapped[Int64] = mapped_column(primary_key=True, nullable=False)
    content_block_id: Mapped[Int64] = mapped_column(
        ForeignKey("content_blocks.id"), unique=True, nullable=False
    )
    position: Mapped[Int64] = mapped_column(nullable=False)
    html: Mapped[str] = mapped_column(nullable=False)
    comment: Mapped[str] = mapped_column(nullable=True)
    line_type: Mapped[ContentLineTypes] = mapped_column(Enum(ContentLineTypes), nullable=False)

    __table_args__ = (
        UniqueConstraint("content_block_id", "position", name="uq_content_block_position"),
    )
