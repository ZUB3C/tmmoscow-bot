from sqlalchemy import ForeignKey, PrimaryKeyConstraint, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, Int64, TimestampMixin


class Files(Base, TimestampMixin):
    __tablename__ = "files"

    id: Mapped[Int64] = mapped_column(primary_key=True, nullable=False)
    title: Mapped[str] = mapped_column(nullable=False)
    server_path: Mapped[str] = mapped_column(Text, nullable=False)
    storage_path: Mapped[str] = mapped_column(Text, nullable=False)
    sha256_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)


class FilesContentLines(Base, TimestampMixin):
    __tablename__ = "files_content_lines"

    file_id: Mapped[Int64] = mapped_column(ForeignKey("files.id"), nullable=False)
    content_line_id: Mapped[Int64] = mapped_column(ForeignKey("content_lines.id"), nullable=False)

    __table_args__ = (
        PrimaryKeyConstraint("file_id", "content_line_id", name="pk_file_content_line"),
    )
