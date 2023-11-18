"""init

Revision ID: 53c6cdb8fe74
Revises: 
Create Date: 2020-04-15 23:20:42.718401

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '53c6cdb8fe74'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('changelog',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('action', sa.String(length=140), nullable=True),
    sa.Column('author', sa.String(length=140), nullable=True),
    sa.Column('employee', sa.String(length=140), nullable=True),
    sa.Column('project', sa.String(length=140), nullable=True),
    sa.Column('month', sa.Integer(), nullable=True),
    sa.Column('year', sa.Integer(), nullable=True),
    sa.Column('dedication_old', sa.Float(), nullable=True),
    sa.Column('dedication_new', sa.Float(), nullable=True),
    sa.Column('remarks', sa.String(length=1400), nullable=True),
    sa.Column('timestamp', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_changelog_action'), 'changelog', ['action'], unique=False)
    op.create_index(op.f('ix_changelog_author'), 'changelog', ['author'], unique=False)
    op.create_index(op.f('ix_changelog_project'), 'changelog', ['project'], unique=False)
    op.create_index(op.f('ix_changelog_timestamp'), 'changelog', ['timestamp'], unique=False)
    op.create_index(op.f('ix_changelog_year'), 'changelog', ['year'], unique=False)
    op.create_table('forecast',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('employee', sa.String(length=140), nullable=True),
    sa.Column('project', sa.String(length=140), nullable=True),
    sa.Column('remarks', sa.String(length=1400), nullable=True),
    sa.Column('month', sa.Integer(), nullable=True),
    sa.Column('year', sa.Integer(), nullable=True),
    sa.Column('dedication', sa.Float(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_forecast_employee'), 'forecast', ['employee'], unique=False)
    op.create_index(op.f('ix_forecast_project'), 'forecast', ['project'], unique=False)
    op.create_table('user',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('username', sa.String(length=64), nullable=True),
    sa.Column('password_hash', sa.String(length=128), nullable=True),
    sa.Column('last_seen', sa.DateTime(), nullable=True),
    sa.Column('token', sa.String(length=32), nullable=True),
    sa.Column('token_expiration', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_user_token'), 'user', ['token'], unique=True)
    op.create_index(op.f('ix_user_username'), 'user', ['username'], unique=True)
    op.create_table('followers',
    sa.Column('follower_id', sa.Integer(), nullable=True),
    sa.Column('followed_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['followed_id'], ['user.id'], ),
    sa.ForeignKeyConstraint(['follower_id'], ['user.id'], )
    )
    op.create_table('post',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('body', sa.String(length=140), nullable=True),
    sa.Column('timestamp', sa.DateTime(), nullable=True),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('language', sa.String(length=5), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_post_timestamp'), 'post', ['timestamp'], unique=False)
    op.create_table('task',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('name', sa.String(length=128), nullable=True),
    sa.Column('description', sa.String(length=128), nullable=True),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('complete', sa.Boolean(), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_task_name'), 'task', ['name'], unique=False)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_task_name'), table_name='task')
    op.drop_table('task')
    op.drop_index(op.f('ix_post_timestamp'), table_name='post')
    op.drop_table('post')
    op.drop_table('followers')
    op.drop_index(op.f('ix_user_username'), table_name='user')
    op.drop_index(op.f('ix_user_token'), table_name='user')
    op.drop_table('user')
    op.drop_index(op.f('ix_forecast_project'), table_name='forecast')
    op.drop_index(op.f('ix_forecast_employee'), table_name='forecast')
    op.drop_table('forecast')
    op.drop_index(op.f('ix_changelog_year'), table_name='changelog')
    op.drop_index(op.f('ix_changelog_timestamp'), table_name='changelog')
    op.drop_index(op.f('ix_changelog_project'), table_name='changelog')
    op.drop_index(op.f('ix_changelog_author'), table_name='changelog')
    op.drop_index(op.f('ix_changelog_action'), table_name='changelog')
    op.drop_table('changelog')
    # ### end Alembic commands ###
