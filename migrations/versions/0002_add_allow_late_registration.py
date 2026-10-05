"""
Add allow_late_registration column to event

Revision ID: 0002_add_allow_late_registration
Revises: 0001_add_event_id_to_gallery
Create Date: 2025-11-25 00:30:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0002_add_allow_late_registration'
down_revision = '0001_add_event_id_to_gallery'
branch_labels = None
depends_on = None


def upgrade():
    # Add nullable boolean column with default False
    op.add_column('event', sa.Column('allow_late_registration', sa.Boolean(), nullable=True, server_default=sa.sql.expression.false()))


def downgrade():
    # No-op downgrade for SQLite
    pass
