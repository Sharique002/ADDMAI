"""Create media_records table

Revision ID: 0001_media_records
Revises: None
Create Date: 2026-09-25 18:35:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '0001_media_records'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'media_records',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('sha256_digest', sa.String(length=64), nullable=False),
        sa.Column('media_category', sa.String(length=16), nullable=False),
        sa.Column('mime_type', sa.String(length=64), nullable=False),
        sa.Column('original_filename', sa.String(length=255), nullable=False),
        sa.Column('size_bytes', sa.BigInteger(), nullable=False),
        sa.Column('storage_key', sa.String(length=255), nullable=False),
        sa.Column('validation_status', sa.String(length=32), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('sha256_digest', name='uq_media_records_sha256'),
        sa.CheckConstraint('size_bytes >= 0', name='ck_media_records_size_bytes_non_negative'),
        sa.CheckConstraint("media_category IN ('image', 'video')", name='ck_media_records_media_category'),
    )
    op.create_index('ix_media_records_sha256', 'media_records', ['sha256_digest'], unique=True)



def downgrade() -> None:
    op.drop_index('ix_media_records_sha256', table_name='media_records')
    op.drop_table('media_records')
