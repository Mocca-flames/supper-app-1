"""Add payment and refund tables

Revision ID: 7b8ae818df84
Revises: 2af61ddd0063
Create Date: 2025-08-13 04:16:43.743814

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '7b8ae818df84'
down_revision: Union[str, None] = '2af61ddd0063'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    """Upgrade schema."""
    # Create payments table
    op.create_table(
        'payments',
        sa.Column('id', sa.String(), primary_key=True, nullable=False),
        sa.Column('order_id', sa.String(), sa.ForeignKey('orders.id'), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('payment_type', sa.Enum('client_payment', 'driver_payment', name='paymenttype'), nullable=False),
        sa.Column('amount', sa.Numeric(10, 2), nullable=False),
        sa.Column('currency', sa.String(), server_default='ZAR', nullable=True),
        sa.Column('payment_method', sa.Enum('credit_card', 'mobile_money', 'cash', 'other', name='paymentmethod'), nullable=False),
        sa.Column('status', sa.Enum('pending', 'completed', 'failed', 'refunded', 'partial', name='paymentstatus'), server_default='pending', nullable=True),
        sa.Column('transaction_id', sa.String(), nullable=True),
        sa.Column('transaction_details', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=True)
    )

    # Create refunds table
    op.create_table(
        'refunds',
        sa.Column('id', sa.String(), primary_key=True, nullable=False),
        sa.Column('payment_id', sa.String(), sa.ForeignKey('payments.id'), nullable=False),
        sa.Column('order_id', sa.String(), sa.ForeignKey('orders.id'), nullable=False),
        sa.Column('amount', sa.Numeric(10, 2), nullable=False),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('status', sa.Enum('pending', 'completed', 'failed', 'refunded', 'partial', name='paymentstatus'), server_default='pending', nullable=True),
        sa.Column('processed_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=True)
    )

def downgrade() -> None:
    """Downgrade schema."""
    # Drop refunds table first due to foreign key dependency
    op.drop_table('refunds')

    # Drop payments table
    op.drop_table('payments')

    # Drop enums
    op.execute('DROP TYPE IF EXISTS paymenttype')
    op.execute('DROP TYPE IF EXISTS paymentmethod')
    op.execute('DROP TYPE IF EXISTS paymentstatus')
