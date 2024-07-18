"""Add nombre column to Ticket with default value

Revision ID: 30f3d051fb88
Revises: 929b3b0e6516
Create Date: 2024-07-17 20:39:03.942525

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '30f3d051fb88'
down_revision = '929b3b0e6516'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('ticket', schema=None) as batch_op:
        batch_op.add_column(sa.Column('nombre', sa.String(length=50), nullable=True, server_default='default_value'))

def downgrade():
    with op.batch_alter_table('ticket', schema=None) as batch_op:
        batch_op.drop_column('nombre')
