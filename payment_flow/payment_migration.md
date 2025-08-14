# Database Migration for Payment Tables

## Alembic Migration Script

```python
"""create payment tables

Revision ID: abc123def456
Revises: 4ab1f928c359
Create Date: 2025-08-13 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'abc123def456'
down_revision = '4ab1f928c359'
branch_labels = None
depends_on = None

def upgrade():
    # Create payment_status enum
    payment_status_enum = sa.Enum(
        'pending', 'completed', 'failed', 'refunded', 'partial',
        name='paymentstatus',
        create_type=False  # Let SQLAlchemy handle the type creation
    )
    payment_status_enum.create(op.get_bind(), checkfirst=False)

    # Create payment_type enum
    payment_type_enum = sa.Enum(
        'client_payment', 'driver_payment',
        name='paymenttype',
        create_type=False
    )
    payment_type_enum.create(op.get_bind(), checkfirst=False)

    # Create payment_method enum
    payment_method_enum = sa.Enum(
        'credit_card', 'mobile_money', 'cash', 'other',
        name='paymentmethod',
        create_type=False
    )
    payment_method_enum.create(op.get_bind(), checkfirst=False)

    # Create payments table
    op.create_table(
        'payments',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('order_id', sa.String(), sa.ForeignKey('orders.id'), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('payment_type', payment_type_enum, nullable=False),
        sa.Column('amount', sa.Numeric(10, 2), nullable=False),
        sa.Column('currency', sa.String(), default='ZAR'),
        sa.Column('payment_method', payment_method_enum, nullable=False),
        sa.Column('status', payment_status_enum, default='pending'),
        sa.Column('transaction_id', sa.String(), nullable=True),
        sa.Column('transaction_details', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), default=sa.func.now(), onupdate=sa.func.now())
    )

    # Create refunds table
    op.create_table(
        'refunds',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('payment_id', sa.String(), sa.ForeignKey('payments.id'), nullable=False),
        sa.Column('order_id', sa.String(), sa.ForeignKey('orders.id'), nullable=False),
        sa.Column('amount', sa.Numeric(10, 2), nullable=False),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('status', payment_status_enum, default='pending'),
        sa.Column('processed_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), default=sa.func.now(), onupdate=sa.func.now())
    )

    # Add payment fields to orders table
    op.add_column('orders', sa.Column('payment_status', payment_status_enum, default='pending'))
    op.add_column('orders', sa.Column('total_paid', sa.Numeric(10, 2), default=0.00))
    op.add_column('orders', sa.Column('total_refunded', sa.Numeric(10, 2), default=0.00))

def downgrade():
    # Remove payment fields from orders table
    op.drop_column('orders', 'total_refunded')
    op.drop_column('orders', 'total_paid')
    op.drop_column('orders', 'payment_status')

    # Drop refunds table
    op.drop_table('refunds')

    # Drop payments table
    op.drop_table('payments')

    # Drop enums
    sa.Enum(name='paymentmethod').drop(op.get_bind(), checkfirst=False)
    sa.Enum(name='paymenttype').drop(op.get_bind(), checkfirst=False)
    sa.Enum(name='paymentstatus').drop(op.get_bind(), checkfirst=False)
```

## Key Features

1. **Enum Types**: Creates proper enum types for payment status, types, and methods
2. **Payments Table**: Complete payment tracking with all required fields
3. **Refunds Table**: Full refund lifecycle support
4. **Order Integration**: Adds payment fields to existing orders table
5. **Rollback Support**: Full downgrade capability to remove all changes
6. **Foreign Keys**: Proper relationships between tables