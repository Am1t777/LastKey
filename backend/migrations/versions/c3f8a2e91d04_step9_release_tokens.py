"""step9_release_tokens

Revision ID: c3f8a2e91d04
Revises: a856dbc85653
Create Date: 2026-03-25 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c3f8a2e91d04'
down_revision: Union[str, None] = 'a856dbc85653'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add release token columns to beneficiaries
    op.add_column('beneficiaries', sa.Column('release_token', sa.String(), nullable=True))
    op.add_column('beneficiaries', sa.Column('release_token_expires_at', sa.DateTime(), nullable=True))
    # Add released_at column to users
    op.add_column('users', sa.Column('released_at', sa.DateTime(), nullable=True))
    # SQLite does not support ALTER TABLE for unique constraints — uniqueness of
    # release_token is enforced at the application layer via cryptographically random token generation.


def downgrade() -> None:
    op.drop_column('users', 'released_at')
    op.drop_column('beneficiaries', 'release_token_expires_at')
    op.drop_column('beneficiaries', 'release_token')
