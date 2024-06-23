"""empty message

Revision ID: 040c160be611
Revises: 12318bb0cf75
Create Date: 2024-06-20 22:32:49.928379

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '040c160be611'
down_revision = '12318bb0cf75'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('movies', schema=None) as batch_op:
        batch_op.add_column(sa.Column('id', sa.Integer(), nullable=False))
        batch_op.add_column(sa.Column('spoken_languages', sa.String(length=50), nullable=True))
        batch_op.add_column(sa.Column('original_language', sa.String(length=50), nullable=True))
        batch_op.add_column(sa.Column('poster_url', sa.String(length=300), nullable=True))
        batch_op.add_column(sa.Column('youtube_trailers', sa.String(length=1000), nullable=True))
        batch_op.add_column(sa.Column('popularity', sa.Float(), nullable=True))
        batch_op.drop_column('show_id')

    with op.batch_alter_table('series', schema=None) as batch_op:
        batch_op.add_column(sa.Column('id', sa.Integer(), nullable=False))
        batch_op.add_column(sa.Column('spoken_languages', sa.String(length=50), nullable=True))
        batch_op.add_column(sa.Column('original_language', sa.String(length=50), nullable=True))
        batch_op.add_column(sa.Column('seasons', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('poster_url', sa.String(length=300), nullable=True))
        batch_op.add_column(sa.Column('youtube_trailers', sa.String(length=1000), nullable=True))
        batch_op.add_column(sa.Column('popularity', sa.Float(), nullable=True))
        batch_op.drop_column('duration')
        batch_op.drop_column('show_id')

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('series', schema=None) as batch_op:
        batch_op.add_column(sa.Column('show_id', sa.VARCHAR(length=10), autoincrement=False, nullable=False))
        batch_op.add_column(sa.Column('duration', sa.VARCHAR(length=20), autoincrement=False, nullable=True))
        batch_op.drop_column('popularity')
        batch_op.drop_column('youtube_trailers')
        batch_op.drop_column('poster_url')
        batch_op.drop_column('seasons')
        batch_op.drop_column('original_language')
        batch_op.drop_column('spoken_languages')
        batch_op.drop_column('id')

    with op.batch_alter_table('movies', schema=None) as batch_op:
        batch_op.add_column(sa.Column('show_id', sa.VARCHAR(length=10), autoincrement=False, nullable=False))
        batch_op.drop_column('popularity')
        batch_op.drop_column('youtube_trailers')
        batch_op.drop_column('poster_url')
        batch_op.drop_column('original_language')
        batch_op.drop_column('spoken_languages')
        batch_op.drop_column('id')

    # ### end Alembic commands ###
