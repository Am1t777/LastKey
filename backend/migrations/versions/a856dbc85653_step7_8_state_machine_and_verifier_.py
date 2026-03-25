"""step7_8_state_machine_and_verifier_fields

Revision ID: a856dbc85653
Revises: 860c7c51edc7
Create Date: 2026-03-25 09:32:50.294580

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a856dbc85653'
down_revision: Union[str, None] = '860c7c51edc7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # trusted_verifiers columns were partially applied in a prior run — skip them.
    # op.add_column('trusted_verifiers', ...) already present in DB.
    op.add_column('users', sa.Column('switch_status', sa.String(), nullable=False, server_default='active'))
    op.add_column('users', sa.Column('reminder_sent_at', sa.DateTime(), nullable=True))
    op.add_column('users', sa.Column('verifier_contacted_at', sa.DateTime(), nullable=True))
    op.add_column('users', sa.Column('checkin_token', sa.String(), nullable=True))
    op.add_column('users', sa.Column('checkin_token_expires_at', sa.DateTime(), nullable=True))
    # SQLite does not support ALTER TABLE for unique constraints — uniqueness is
    # enforced at the application layer via cryptographically random token generation.


def downgrade() -> None:
    op.drop_column('users', 'checkin_token_expires_at')
    op.drop_column('users', 'checkin_token')
    op.drop_column('users', 'verifier_contacted_at')
    op.drop_column('users', 'reminder_sent_at')
    op.drop_column('users', 'switch_status')
    op.drop_column('trusted_verifiers', 'contacted_at')
    op.drop_column('trusted_verifiers', 'has_denied')
    op.drop_column('trusted_verifiers', 'denial_token')
