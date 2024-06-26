from datetime import UTC, datetime
from typing import Annotated, TypeAlias

from sqlalchemy import BigInteger, DateTime, Integer, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, registry

Int16: TypeAlias = Annotated[int, 16]
Int64: TypeAlias = Annotated[int, 64]


class Base(DeclarativeBase):
    registry = registry(
        type_annotation_map={Int16: Integer, Int64: BigInteger, datetime: DateTime(timezone=True)}
    )


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(UTC),
        onupdate=func.now(),
        server_default=func.now(),
    )
