"""add_unique_constraint_on_transaction_id

Revision ID: 5274b142cf82
Revises: 264b0a12b3fd
Create Date: 2025-10-19 08:13:56.438670

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5274b142cf82'
down_revision: Union[str, None] = '264b0a12b3fd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add unique constraint on transaction_id for non-null values to prevent duplicate payments
    # This uses a partial index that only includes non-null transaction_id values
    op.create_index(
        'ix_payments_transaction_id_unique',
        'payments',
        ['transaction_id'],
        unique=True,
        postgresql_where=sa.text('transaction_id IS NOT NULL')
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Drop the unique index
    op.drop_index('ix_payments_transaction_id_unique', table_name='payments')
