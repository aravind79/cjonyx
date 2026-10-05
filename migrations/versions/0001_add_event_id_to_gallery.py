"""
Add event_id column to gallery

Revision ID: 0001_add_event_id_to_gallery
Revises: 
Create Date: 2025-11-25 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0001_add_event_id_to_gallery'
# This migration should follow the revision that created the `gallery` table
down_revision = 'd4f1eda20e05'
branch_labels = None
depends_on = None


def upgrade():
    # Note: SQLite supports ADD COLUMN without full table rewrite. This will add a nullable integer column.
    op.add_column('gallery', sa.Column('event_id', sa.Integer(), nullable=True))


def downgrade():
    # Dropping columns in SQLite is non-trivial; leaving downgrade as a no-op.
    # A proper downgrade would need to recreate the table without the column.
    pass
