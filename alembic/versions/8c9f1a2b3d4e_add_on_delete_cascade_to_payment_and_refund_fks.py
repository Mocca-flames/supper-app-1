"""Add ON DELETE CASCADE to foreign key constraints on payments and refunds

Revision ID: 8c9f1a2b3d4e
Revises: 7b8ae818df84
Create Date: 2025-09-19 23:43:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '8c9f1a2b3d4e'
down_revision = '7b8ae818df84'
branch_labels = None
depends_on = None

def upgrade():
    # Drop existing foreign key constraints
    op.drop_constraint('payments_order_id_fkey', 'payments', type_='foreignkey')
    op.drop_constraint('refunds_payment_id_fkey', 'refunds', type_='foreignkey')
    op.drop_constraint('refunds_order_id_fkey', 'refunds', type_='foreignkey')

    # Recreate foreign key constraints with ON DELETE CASCADE
    op.create_foreign_key(
        'payments_order_id_fkey',
        'payments', 'orders',
        ['order_id'], ['id'],
        ondelete='CASCADE'
    )
    op.create_foreign_key(
        'refunds_payment_id_fkey',
        'refunds', 'payments',
        ['payment_id'], ['id'],
        ondelete='CASCADE'
    )
    op.create_foreign_key(
        'refunds_order_id_fkey',
        'refunds', 'orders',
        ['order_id'], ['id'],
        ondelete='CASCADE'
    )

def downgrade():
    # Drop foreign key constraints with ON DELETE CASCADE
    op.drop_constraint('payments_order_id_fkey', 'payments', type_='foreignkey')
    op.drop_constraint('refunds_payment_id_fkey', 'refunds', type_='foreignkey')
    op.drop_constraint('refunds_order_id_fkey', 'refunds', type_='foreignkey')

    # Recreate original foreign key constraints without ON DELETE CASCADE
    op.create_foreign_key(
        'payments_order_id_fkey',
        'payments', 'orders',
        ['order_id'], ['id']
    )
    op.create_foreign_key(
        'refunds_payment_id_fkey',
        'refunds', 'payments',
        ['payment_id'], ['id']
    )
    op.create_foreign_key(
        'refunds_order_id_fkey',
        'refunds', 'orders',
        ['order_id'], ['id']
    )