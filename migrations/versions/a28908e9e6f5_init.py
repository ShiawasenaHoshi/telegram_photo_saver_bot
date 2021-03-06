"""init

Revision ID: a28908e9e6f5
Revises: 
Create Date: 2019-11-09 15:13:57.704425

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a28908e9e6f5'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('chat',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=240), nullable=False),
    sa.Column('local_folder', sa.String(length=240), nullable=False),
    sa.Column('yd_folder', sa.String(length=240), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('photo',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('file_hash', sa.String(length=240), nullable=False),
    sa.Column('chat_id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('msg_date', sa.DateTime(), nullable=False),
    sa.Column('msg_id', sa.Integer(), nullable=False),
    sa.Column('yd_path', sa.String(length=240), nullable=False),
    sa.ForeignKeyConstraint(['chat_id'], ['chat.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_chat_hash', 'photo', ['chat_id', 'file_hash'], unique=False)
    op.create_index('ix_user_hash_date', 'photo', ['user_id', 'file_hash', 'msg_date'], unique=False)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index('ix_user_hash_date', table_name='photo')
    op.drop_index('ix_chat_hash', table_name='photo')
    op.drop_table('photo')
    op.drop_table('chat')
    # ### end Alembic commands ###
