"""Add gateway field to payments

Revision ID: add_gateway_field_to_payments
Revises: 8c9f1a2b3d4e
Create Date: 2025-10-07 18:06:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'add_gateway_field_to_payments'
down_revision: Union[str, None] = '8c9f1a2b3d4e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    """Upgrade schema."""
    # Create enum type first
    paymentgateway_enum = sa.Enum('PAYFAST', 'PAYSTACK', name='paymentgateway')
    paymentgateway_enum.create(op.get_bind(), checkfirst=True)

    # Add gateway column to payments table
    op.add_column('payments', sa.Column('gateway', paymentgateway_enum, server_default='PAYFAST', nullable=False))

def downgrade() -> None:
    """Downgrade schema."""
    # Drop gateway column from payments table
    op.drop_column('payments', 'gateway')

    # Drop enum type
    paymentgateway_enum = sa.Enum('PAYFAST', 'PAYSTACK', name='paymentgateway')
    paymentgateway_enum.drop(op.get_bind(), checkfirst=True)