"""Create model_predictions table

Revision ID: 0002_model_predictions
Revises: 0001_media_records
Create Date: 2026-09-25 21:15:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '0002_model_predictions'
down_revision: Union[str, None] = '0001_media_records'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'model_predictions',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('media_id', sa.Uuid(), nullable=False),
        sa.Column('model_id', sa.String(length=64), nullable=False),
        sa.Column('model_version', sa.String(length=32), nullable=False),
        sa.Column('prediction', sa.String(length=16), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=False),
        sa.Column('preprocessing_version', sa.String(length=32), nullable=False),
        sa.Column('model_artifact_sha256', sa.String(length=64), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['media_id'], ['media_records.id'], name='fk_model_predictions_media_id', ondelete='CASCADE'),
        sa.CheckConstraint("prediction IN ('REAL', 'DEEPFAKE')", name='ck_model_predictions_prediction'),
        sa.CheckConstraint('confidence >= 0.0 AND confidence <= 1.0', name='ck_model_predictions_confidence_range'),
    )
    op.create_index('ix_model_predictions_media_id', 'model_predictions', ['media_id'])


def downgrade() -> None:
    op.drop_index('ix_model_predictions_media_id', table_name='model_predictions')
    op.drop_table('model_predictions')
