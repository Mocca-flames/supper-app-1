"""Update OrderType RIDE enum value from ride to ride_hailing

Revision ID: c038d2821cd1
Revises: 5e7c65591110
Create Date: 2025-10-07 16:29:37.230864

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c038d2821cd1'
down_revision: Union[str, None] = '5e7c65591110'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Update existing data to match new enum values
    op.execute("UPDATE orders SET order_type = 'ride_hailing' WHERE order_type = 'RIDE'")

    # Create a new enum type with the updated values
    op.execute("CREATE TYPE ordertype_new AS ENUM('ride_hailing', 'food_delivery', 'parcel_delivery', 'medical_product', 'patient_transport')")

    # Update the column to use the new enum type
    op.execute("ALTER TABLE orders ALTER COLUMN order_type TYPE ordertype_new USING order_type::text::ordertype_new")

    # Drop the old enum type
    op.execute("DROP TYPE ordertype")

    # Rename the new enum type to the original name
    op.execute("ALTER TYPE ordertype_new RENAME TO ordertype")


def downgrade() -> None:
    """Downgrade schema."""
    # Create the old enum type
    op.execute("CREATE TYPE ordertype_old AS ENUM('RIDE', 'food_delivery', 'parcel_delivery', 'medical_product', 'patient_transport')")

    # Update the column to use the old enum type
    op.execute("ALTER TABLE orders ALTER COLUMN order_type TYPE ordertype_old USING order_type::text::ordertype_old")

    # Drop the new enum type
    op.execute("DROP TYPE ordertype")

    # Rename the old enum type to the original name
    op.execute("ALTER TYPE ordertype_old RENAME TO ordertype")
