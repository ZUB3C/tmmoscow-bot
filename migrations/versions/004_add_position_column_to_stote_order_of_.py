"""Add position column to store order of content

Revision ID: 004
Revises: 003
Create Date: 2024-08-24 13:50:52.758911

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "004"
down_revision: str | None = "003"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column("content_blocks", sa.Column("position", sa.BigInteger(), nullable=False))
    op.create_unique_constraint(
        "uq_competition_version_position", "content_blocks", ["competition_version_id", "position"]
    )
    op.add_column("content_lines", sa.Column("position", sa.BigInteger(), nullable=False))
    op.create_unique_constraint(
        "uq_content_block_position", "content_lines", ["content_block_id", "position"]
    )
    op.drop_column("content_lines", "file_ids")
    op.add_column("files_content_lines", sa.Column("position", sa.BigInteger(), nullable=False))
    op.create_unique_constraint(
        "uq_content_line_position", "files_content_lines", ["content_line_id", "position"]
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint("uq_content_line_position", "files_content_lines", type_="unique")
    op.drop_column("files_content_lines", "position")
    op.add_column(
        "content_lines",
        sa.Column("file_ids", postgresql.ARRAY(sa.BIGINT()), autoincrement=False, nullable=True),
    )
    op.drop_constraint("uq_content_block_position", "content_lines", type_="unique")
    op.drop_column("content_lines", "position")
    op.drop_constraint("uq_competition_version_position", "content_blocks", type_="unique")
    op.drop_column("content_blocks", "position")
    # ### end Alembic commands ###
