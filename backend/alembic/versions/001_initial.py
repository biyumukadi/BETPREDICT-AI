"""initial schema

Revision ID: 001
Revises:
Create Date: 2026-11-13

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\"")
    # Tables are created via metadata in seed for MVP bootstrap;
    # this revision documents the baseline and creates core enums/tables if missing.
    bind = op.get_bind()
    from app.db.base import Base
    import app.models  # noqa: F401

    Base.metadata.create_all(bind=bind)


def downgrade() -> None:
    bind = op.get_bind()
    from app.db.base import Base
    import app.models  # noqa: F401

    Base.metadata.drop_all(bind=bind)
