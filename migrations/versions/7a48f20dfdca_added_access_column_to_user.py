"""added access column to User

Revision ID: 7a48f20dfdca
Revises: 84f79f7d5819
Create Date: 2020-04-27 21:58:14.319218

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7a48f20dfdca'
down_revision = '84f79f7d5819'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('user', sa.Column('access', sa.Integer(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('user', 'access')
    # ### end Alembic commands ###
