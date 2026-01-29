"""Create orders and payments tables

Revision ID: 002_orders_payments
Create Date: 2024-01-28 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '002_orders_payments'
down_revision = '001_initial'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create carts table
    op.create_table(
        'carts',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('items', postgresql.JSONB(), nullable=False, server_default='[]'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', name='uq_carts_user_id'),
    )
    op.create_index('ix_carts_user_id', 'carts', ['user_id'])

    # Create orders table
    op.create_table(
        'orders',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('status', sa.String(20), nullable=False, server_default='pending'),
        sa.Column('total_amount', sa.Float(), nullable=False),
        sa.Column('discount_amount', sa.Float(), nullable=False, server_default='0'),
        sa.Column('tax_amount', sa.Float(), nullable=False, server_default='0'),
        sa.Column('final_amount', sa.Float(), nullable=False),
        sa.Column('items', postgresql.JSONB(), nullable=False),
        sa.Column('shipping_address', postgresql.JSONB(), nullable=False),
        sa.Column('delivery_radius_km', sa.Float(), nullable=True),
        sa.Column('is_home_delivery', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_orders_user_id', 'orders', ['user_id'])
    op.create_index('ix_orders_status', 'orders', ['status'])
    op.create_index('ix_orders_created_at', 'orders', ['created_at'])

    # Create payments table
    op.create_table(
        'payments',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('order_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('razorpay_order_id', sa.String(255), nullable=True),
        sa.Column('razorpay_payment_id', sa.String(255), nullable=True),
        sa.Column('razorpay_signature', sa.String(255), nullable=True),
        sa.Column('amount', sa.Float(), nullable=False),
        sa.Column('currency', sa.String(3), nullable=False, server_default='INR'),
        sa.Column('status', sa.String(20), nullable=False, server_default='pending'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['order_id'], ['orders.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('razorpay_payment_id', name='uq_payments_razorpay_payment_id'),
    )
    op.create_index('ix_payments_order_id', 'payments', ['order_id'])
    op.create_index('ix_payments_user_id', 'payments', ['user_id'])
    op.create_index('ix_payments_status', 'payments', ['status'])
    op.create_index('ix_payments_razorpay_order_id', 'payments', ['razorpay_order_id'])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('ix_payments_razorpay_order_id', table_name='payments')
    op.drop_index('ix_payments_status', table_name='payments')
    op.drop_index('ix_payments_user_id', table_name='payments')
    op.drop_index('ix_payments_order_id', table_name='payments')
    op.drop_table('payments')

    op.drop_index('ix_orders_created_at', table_name='orders')
    op.drop_index('ix_orders_status', table_name='orders')
    op.drop_index('ix_orders_user_id', table_name='orders')
    op.drop_table('orders')

    op.drop_index('ix_carts_user_id', table_name='carts')
    op.drop_table('carts')
