"""add_cascade_to_payment_fks

Revision ID: eaa3dbbb02df
Revises: 118228e84f11
Create Date: 2025-11-15 12:35:15.622770

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'eaa3dbbb02df'
down_revision: Union[str, None] = '118228e84f11'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Drop existing foreign key constraints
    op.drop_constraint('payments_client_id_fkey', 'payments', type_='foreignkey')
    op.drop_constraint('driver_payouts_driver_id_fkey', 'driver_payouts', type_='foreignkey')

    # Recreate foreign key constraints with ON UPDATE CASCADE
    op.create_foreign_key('payments_client_id_fkey', 'payments', 'users', ['client_id'], ['id'], onupdate='CASCADE')
    op.create_foreign_key('driver_payouts_driver_id_fkey', 'driver_payouts', 'users', ['driver_id'], ['id'], onupdate='CASCADE')


def downgrade() -> None:
    """Downgrade schema."""
    # Drop foreign key constraints with CASCADE
    op.drop_constraint('payments_client_id_fkey', 'payments', type_='foreignkey')
    op.drop_constraint('driver_payouts_driver_id_fkey', 'driver_payouts', type_='foreignkey')

    # Recreate foreign key constraints without CASCADE (original state)
    op.create_foreign_key('payments_client_id_fkey', 'payments', 'users', ['client_id'], ['id'])
    op.create_foreign_key('driver_payouts_driver_id_fkey', 'driver_payouts', 'users', ['driver_id'], ['id'])
