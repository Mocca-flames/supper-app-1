"""add_on_update_cascade_to_user_fks

Revision ID: 118228e84f11
Revises: cb3177d0e158
Create Date: 2025-11-15 12:30:39.863114

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '118228e84f11'
down_revision: Union[str, None] = 'cb3177d0e158'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Drop existing foreign key constraints
    op.drop_constraint('clients_client_id_fkey', 'clients', type_='foreignkey')
    op.drop_constraint('drivers_driver_id_fkey', 'drivers', type_='foreignkey')
    op.drop_constraint('orders_client_id_fkey', 'orders', type_='foreignkey')
    op.drop_constraint('payments_client_id_fkey', 'payments', type_='foreignkey')
    op.drop_constraint('driver_payouts_driver_id_fkey', 'driver_payouts', type_='foreignkey')

    # Recreate foreign key constraints with ON UPDATE CASCADE
    op.create_foreign_key('clients_client_id_fkey', 'clients', 'users', ['client_id'], ['id'], onupdate='CASCADE')
    op.create_foreign_key('drivers_driver_id_fkey', 'drivers', 'users', ['driver_id'], ['id'], onupdate='CASCADE')
    op.create_foreign_key('orders_client_id_fkey', 'orders', 'users', ['client_id'], ['id'], onupdate='CASCADE')
    op.create_foreign_key('payments_client_id_fkey', 'payments', 'users', ['client_id'], ['id'], onupdate='CASCADE')
    op.create_foreign_key('driver_payouts_driver_id_fkey', 'driver_payouts', 'users', ['driver_id'], ['id'], onupdate='CASCADE')


def downgrade() -> None:
    """Downgrade schema."""
    # Drop foreign key constraints with CASCADE
    op.drop_constraint('clients_client_id_fkey', 'clients', type_='foreignkey')
    op.drop_constraint('drivers_driver_id_fkey', 'drivers', type_='foreignkey')
    op.drop_constraint('orders_client_id_fkey', 'orders', type_='foreignkey')
    op.drop_constraint('payments_client_id_fkey', 'payments', type_='foreignkey')
    op.drop_constraint('driver_payouts_driver_id_fkey', 'driver_payouts', type_='foreignkey')

    # Recreate foreign key constraints without CASCADE (original state)
    op.create_foreign_key('clients_client_id_fkey', 'clients', 'users', ['client_id'], ['id'])
    op.create_foreign_key('drivers_driver_id_fkey', 'drivers', 'users', ['driver_id'], ['id'])
    op.create_foreign_key('orders_client_id_fkey', 'orders', 'users', ['client_id'], ['id'])
    op.create_foreign_key('payments_client_id_fkey', 'payments', 'users', ['client_id'], ['id'])
    op.create_foreign_key('driver_payouts_driver_id_fkey', 'driver_payouts', 'users', ['driver_id'], ['id'])
