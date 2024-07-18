"""Set nombre column to NOT NULL

Revision ID: 1c6c6611b7c6
Revises: 30f3d051fb88
Create Date: 2024-07-17 20:48:25.747007

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1c6c6611b7c6'
down_revision = '30f3d051fb88'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('ticket', schema=None) as batch_op:
        batch_op.alter_column('nombre',
               existing_type=sa.String(length=50),
               nullable=False,
               server_default=None)

def downgrade():
    with op.batch_alter_table('ticket', schema=None) as batch_op:
        batch_op.alter_column('nombre',
               existing_type=sa.String(length=50),
               nullable=True,
               server_default='default_value')
