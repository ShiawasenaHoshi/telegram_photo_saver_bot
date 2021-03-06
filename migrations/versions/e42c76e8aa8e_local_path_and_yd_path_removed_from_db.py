"""local_path and yd_path removed from db

Revision ID: e42c76e8aa8e
Revises: a336639792e2
Create Date: 2019-11-15 18:27:45.236183

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e42c76e8aa8e'
down_revision = 'a336639792e2'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    # op.drop_column('chat', 'local_folder')
    with op.batch_alter_table("chat") as batch_op:
        batch_op.drop_column('local_folder')
    # op.add_column('chat', sa.Column('local_folder', sa.Boolean(), default=1))
    # op.drop_column('chat', 'yd_folder')
    with op.batch_alter_table("chat") as batch_op:
        batch_op.drop_column('yd_folder')
    # op.add_column('chat', sa.Column('yd_folder', sa.Boolean(), default=1))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('chat', sa.Column('yd_folder', sa.VARCHAR(length=240), nullable=False))
    op.add_column('chat', sa.Column('local_folder', sa.VARCHAR(length=240), nullable=False))
    # ### end Alembic commands ###
