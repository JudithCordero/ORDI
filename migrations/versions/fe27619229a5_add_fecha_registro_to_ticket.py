"""Add fecha_registro to Ticket

Revision ID: fe27619229a5
Revises: 1c6c6611b7c6
Create Date: 2024-07-17 20:49:38.453199

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'fe27619229a5'
down_revision = '1c6c6611b7c6'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('ticket', schema=None) as batch_op:
        batch_op.add_column(sa.Column('fecha_registro', sa.DateTime, nullable=False, server_default=sa.func.now()))

def downgrade():
    with op.batch_alter_table('ticket', schema=None) as batch_op:
        batch_op.drop_column('fecha_registro')
