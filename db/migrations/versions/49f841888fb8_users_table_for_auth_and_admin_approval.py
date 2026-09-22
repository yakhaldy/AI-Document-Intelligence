"""users table for auth and admin approval

Revision ID: 49f841888fb8
Revises: 762bde9e7953
Create Date: 2026-09-22 22:42:48.816324

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '49f841888fb8'
down_revision: Union[str, Sequence[str], None] = '762bde9e7953'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('username', sa.Text(), nullable=False),
        sa.Column('password_hash', sa.Text(), nullable=False),
        sa.Column('role', sa.Text(), server_default='user', nullable=False),
        sa.Column('status', sa.Text(), server_default='pending', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('username', name='uq_users_username'),
        sa.CheckConstraint("role IN ('admin','user')", name='ck_users_role'),
        sa.CheckConstraint("status IN ('pending','approved','rejected')", name='ck_users_status'),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('users')
