"""Added new fields to Ticket model

Revision ID: cace51531a0f
Revises: e71708cbcd2c
Create Date: 2024-07-18 02:01:57.574023

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'cace51531a0f'
down_revision = 'e71708cbcd2c'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('ticket', schema=None) as batch_op:
        
        
        batch_op.add_column(sa.Column('correo', sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column('nivel', sa.Enum('primaria', 'secundaria', 'preparatoria', 'universidad', name='nivel_enum'), nullable=False, server_default='primaria'))
        batch_op.add_column(sa.Column('municipio', sa.Enum('saltillo', 'arteaga', 'ramos arizpe', name='municipio_enum'), nullable=False, server_default='saltillo'))
        batch_op.add_column(sa.Column('asunto', sa.Enum('inscripcion', 'informacion', 'otros', name='asunto_enum'), nullable=False, server_default='inscripcion'))

def downgrade():
    with op.batch_alter_table('ticket', schema=None) as batch_op:
        batch_op.drop_column('telefono')
        batch_op.drop_column('celular')
        batch_op.drop_column('correo')
        batch_op.drop_column('nivel')
        batch_op.drop_column('municipio')
        batch_op.drop_column('asunto')
