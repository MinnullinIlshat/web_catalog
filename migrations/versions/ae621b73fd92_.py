"""empty message

Revision ID: ae621b73fd92
Revises: 
Create Date: 2023-07-01 07:24:10.033467

"""
from alembic import op
import sqlalchemy as sa
import sqlalchemy_utils


# revision identifiers, used by Alembic.
revision = 'ae621b73fd92'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('link',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('uuid', sqlalchemy_utils.types.uuid.UUIDType(binary=False), nullable=True),
    sa.Column('url', sa.String(), nullable=True),
    sa.Column('protocol', sa.String(), nullable=True),
    sa.Column('domain', sa.String(), nullable=True),
    sa.Column('domain_zone', sa.String(), nullable=True),
    sa.Column('path', sa.String(), nullable=True),
    sa.Column('params', sa.PickleType(), nullable=True),
    sa.Column('status_code', sa.Integer(), nullable=True),
    sa.Column('status', sa.String(), nullable=True),
    sa.Column('cover_image', sa.String(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('link', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_link_uuid'), ['uuid'], unique=False)

    op.create_table('user',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('username', sa.String(length=80), nullable=False),
    sa.Column('email', sa.String(length=200), nullable=False),
    sa.Column('password', sa.String(length=200), nullable=True),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('email'),
    sa.UniqueConstraint('username')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('user')
    with op.batch_alter_table('link', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_link_uuid'))

    op.drop_table('link')
    # ### end Alembic commands ###
