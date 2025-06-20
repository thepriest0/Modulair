"""Add CourseGeneration model

Revision ID: 7add239581f6
Revises: 707d5ab958d8
Create Date: 2025-06-17 16:14:48.593496

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '7add239581f6'
down_revision = '707d5ab958d8'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('assignment', schema=None) as batch_op:
        batch_op.alter_column('id',
               existing_type=sa.BIGINT(),
               type_=sa.Integer(),
               existing_nullable=False,
               autoincrement=True,
               existing_server_default=sa.text('unique_rowid()'))
        batch_op.alter_column('course_id',
               existing_type=sa.BIGINT(),
               type_=sa.Integer(),
               existing_nullable=False)
        batch_op.alter_column('lesson_id',
               existing_type=sa.BIGINT(),
               type_=sa.Integer(),
               existing_nullable=True)
        batch_op.alter_column('estimated_hours',
               existing_type=sa.BIGINT(),
               type_=sa.Integer(),
               existing_nullable=True)

    with op.batch_alter_table('assignment_submission', schema=None) as batch_op:
        batch_op.alter_column('id',
               existing_type=sa.BIGINT(),
               type_=sa.Integer(),
               existing_nullable=False,
               autoincrement=True,
               existing_server_default=sa.text('unique_rowid()'))
        batch_op.alter_column('assignment_id',
               existing_type=sa.BIGINT(),
               type_=sa.Integer(),
               existing_nullable=False)
        batch_op.alter_column('user_id',
               existing_type=sa.BIGINT(),
               type_=sa.Integer(),
               existing_nullable=False)
        batch_op.alter_column('score',
               existing_type=sa.BIGINT(),
               type_=sa.Integer(),
               existing_nullable=True)

    with op.batch_alter_table('course', schema=None) as batch_op:
        batch_op.alter_column('id',
               existing_type=sa.BIGINT(),
               type_=sa.Integer(),
               existing_nullable=False,
               autoincrement=True,
               existing_server_default=sa.text('unique_rowid()'))
        batch_op.alter_column('user_id',
               existing_type=sa.BIGINT(),
               type_=sa.Integer(),
               existing_nullable=False)

    with op.batch_alter_table('course_generation', schema=None) as batch_op:
        batch_op.add_column(sa.Column('result', sa.JSON(), nullable=True))
        batch_op.alter_column('id',
               existing_type=sa.VARCHAR(length=36),
               type_=sa.String(length=50),
               existing_nullable=False)
        batch_op.alter_column('progress',
               existing_type=sa.BIGINT(),
               type_=sa.Integer(),
               existing_nullable=False)
        batch_op.alter_column('message',
               existing_type=sa.VARCHAR(length=200),
               type_=sa.String(length=500),
               existing_nullable=True)
        batch_op.alter_column('created_at',
               existing_type=postgresql.TIMESTAMP(),
               nullable=False)
        batch_op.alter_column('updated_at',
               existing_type=postgresql.TIMESTAMP(),
               nullable=False)
        batch_op.alter_column('user_id',
               existing_type=sa.BIGINT(),
               type_=sa.Integer(),
               existing_nullable=False)
        batch_op.drop_column('proficiency')
        batch_op.drop_column('topic')
        batch_op.drop_column('result_file')
        batch_op.drop_column('learning_style')

    with op.batch_alter_table('lesson', schema=None) as batch_op:
        batch_op.alter_column('id',
               existing_type=sa.BIGINT(),
               type_=sa.Integer(),
               existing_nullable=False,
               autoincrement=True,
               existing_server_default=sa.text('unique_rowid()'))
        batch_op.alter_column('course_id',
               existing_type=sa.BIGINT(),
               type_=sa.Integer(),
               existing_nullable=False)
        batch_op.alter_column('order_index',
               existing_type=sa.BIGINT(),
               type_=sa.Integer(),
               existing_nullable=False)

    with op.batch_alter_table('progress', schema=None) as batch_op:
        batch_op.alter_column('id',
               existing_type=sa.BIGINT(),
               type_=sa.Integer(),
               existing_nullable=False,
               autoincrement=True,
               existing_server_default=sa.text('unique_rowid()'))
        batch_op.alter_column('user_id',
               existing_type=sa.BIGINT(),
               type_=sa.Integer(),
               existing_nullable=False)
        batch_op.alter_column('course_id',
               existing_type=sa.BIGINT(),
               type_=sa.Integer(),
               existing_nullable=False)
        batch_op.alter_column('current_lesson',
               existing_type=sa.BIGINT(),
               type_=sa.Integer(),
               existing_nullable=True)
        batch_op.alter_column('completion_percentage',
               existing_type=sa.BIGINT(),
               type_=sa.Integer(),
               existing_nullable=True)
        batch_op.alter_column('final_exam_score',
               existing_type=sa.BIGINT(),
               type_=sa.Integer(),
               existing_nullable=True)

    with op.batch_alter_table('quiz', schema=None) as batch_op:
        batch_op.alter_column('id',
               existing_type=sa.BIGINT(),
               type_=sa.Integer(),
               existing_nullable=False,
               autoincrement=True,
               existing_server_default=sa.text('unique_rowid()'))
        batch_op.alter_column('course_id',
               existing_type=sa.BIGINT(),
               type_=sa.Integer(),
               existing_nullable=False)
        batch_op.alter_column('lesson_id',
               existing_type=sa.BIGINT(),
               type_=sa.Integer(),
               existing_nullable=True)
        batch_op.alter_column('lesson_dependency',
               existing_type=sa.BIGINT(),
               type_=sa.Integer(),
               existing_nullable=True)

    with op.batch_alter_table('quiz_attempt', schema=None) as batch_op:
        batch_op.alter_column('id',
               existing_type=sa.BIGINT(),
               type_=sa.Integer(),
               existing_nullable=False,
               autoincrement=True,
               existing_server_default=sa.text('unique_rowid()'))
        batch_op.alter_column('quiz_id',
               existing_type=sa.BIGINT(),
               type_=sa.Integer(),
               existing_nullable=False)
        batch_op.alter_column('user_id',
               existing_type=sa.BIGINT(),
               type_=sa.Integer(),
               existing_nullable=False)
        batch_op.alter_column('score',
               existing_type=sa.BIGINT(),
               type_=sa.Integer(),
               existing_nullable=False)
        batch_op.alter_column('total_questions',
               existing_type=sa.BIGINT(),
               type_=sa.Integer(),
               existing_nullable=False)
        batch_op.alter_column('attempt_number',
               existing_type=sa.BIGINT(),
               type_=sa.Integer(),
               existing_nullable=True)

    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.alter_column('id',
               existing_type=sa.BIGINT(),
               type_=sa.Integer(),
               existing_nullable=False,
               autoincrement=True,
               existing_server_default=sa.text('unique_rowid()'))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.alter_column('id',
               existing_type=sa.Integer(),
               type_=sa.BIGINT(),
               existing_nullable=False,
               autoincrement=True,
               existing_server_default=sa.text('unique_rowid()'))

    with op.batch_alter_table('quiz_attempt', schema=None) as batch_op:
        batch_op.alter_column('attempt_number',
               existing_type=sa.Integer(),
               type_=sa.BIGINT(),
               existing_nullable=True)
        batch_op.alter_column('total_questions',
               existing_type=sa.Integer(),
               type_=sa.BIGINT(),
               existing_nullable=False)
        batch_op.alter_column('score',
               existing_type=sa.Integer(),
               type_=sa.BIGINT(),
               existing_nullable=False)
        batch_op.alter_column('user_id',
               existing_type=sa.Integer(),
               type_=sa.BIGINT(),
               existing_nullable=False)
        batch_op.alter_column('quiz_id',
               existing_type=sa.Integer(),
               type_=sa.BIGINT(),
               existing_nullable=False)
        batch_op.alter_column('id',
               existing_type=sa.Integer(),
               type_=sa.BIGINT(),
               existing_nullable=False,
               autoincrement=True,
               existing_server_default=sa.text('unique_rowid()'))

    with op.batch_alter_table('quiz', schema=None) as batch_op:
        batch_op.alter_column('lesson_dependency',
               existing_type=sa.Integer(),
               type_=sa.BIGINT(),
               existing_nullable=True)
        batch_op.alter_column('lesson_id',
               existing_type=sa.Integer(),
               type_=sa.BIGINT(),
               existing_nullable=True)
        batch_op.alter_column('course_id',
               existing_type=sa.Integer(),
               type_=sa.BIGINT(),
               existing_nullable=False)
        batch_op.alter_column('id',
               existing_type=sa.Integer(),
               type_=sa.BIGINT(),
               existing_nullable=False,
               autoincrement=True,
               existing_server_default=sa.text('unique_rowid()'))

    with op.batch_alter_table('progress', schema=None) as batch_op:
        batch_op.alter_column('final_exam_score',
               existing_type=sa.Integer(),
               type_=sa.BIGINT(),
               existing_nullable=True)
        batch_op.alter_column('completion_percentage',
               existing_type=sa.Integer(),
               type_=sa.BIGINT(),
               existing_nullable=True)
        batch_op.alter_column('current_lesson',
               existing_type=sa.Integer(),
               type_=sa.BIGINT(),
               existing_nullable=True)
        batch_op.alter_column('course_id',
               existing_type=sa.Integer(),
               type_=sa.BIGINT(),
               existing_nullable=False)
        batch_op.alter_column('user_id',
               existing_type=sa.Integer(),
               type_=sa.BIGINT(),
               existing_nullable=False)
        batch_op.alter_column('id',
               existing_type=sa.Integer(),
               type_=sa.BIGINT(),
               existing_nullable=False,
               autoincrement=True,
               existing_server_default=sa.text('unique_rowid()'))

    with op.batch_alter_table('lesson', schema=None) as batch_op:
        batch_op.alter_column('order_index',
               existing_type=sa.Integer(),
               type_=sa.BIGINT(),
               existing_nullable=False)
        batch_op.alter_column('course_id',
               existing_type=sa.Integer(),
               type_=sa.BIGINT(),
               existing_nullable=False)
        batch_op.alter_column('id',
               existing_type=sa.Integer(),
               type_=sa.BIGINT(),
               existing_nullable=False,
               autoincrement=True,
               existing_server_default=sa.text('unique_rowid()'))

    with op.batch_alter_table('course_generation', schema=None) as batch_op:
        batch_op.add_column(sa.Column('learning_style', sa.VARCHAR(length=50), autoincrement=False, nullable=False))
        batch_op.add_column(sa.Column('result_file', sa.VARCHAR(length=200), autoincrement=False, nullable=True))
        batch_op.add_column(sa.Column('topic', sa.VARCHAR(length=100), autoincrement=False, nullable=False))
        batch_op.add_column(sa.Column('proficiency', sa.VARCHAR(length=50), autoincrement=False, nullable=False))
        batch_op.alter_column('user_id',
               existing_type=sa.Integer(),
               type_=sa.BIGINT(),
               existing_nullable=False)
        batch_op.alter_column('updated_at',
               existing_type=postgresql.TIMESTAMP(),
               nullable=True)
        batch_op.alter_column('created_at',
               existing_type=postgresql.TIMESTAMP(),
               nullable=True)
        batch_op.alter_column('message',
               existing_type=sa.String(length=500),
               type_=sa.VARCHAR(length=200),
               existing_nullable=True)
        batch_op.alter_column('progress',
               existing_type=sa.Integer(),
               type_=sa.BIGINT(),
               existing_nullable=False)
        batch_op.alter_column('id',
               existing_type=sa.String(length=50),
               type_=sa.VARCHAR(length=36),
               existing_nullable=False)
        batch_op.drop_column('result')

    with op.batch_alter_table('course', schema=None) as batch_op:
        batch_op.alter_column('user_id',
               existing_type=sa.Integer(),
               type_=sa.BIGINT(),
               existing_nullable=False)
        batch_op.alter_column('id',
               existing_type=sa.Integer(),
               type_=sa.BIGINT(),
               existing_nullable=False,
               autoincrement=True,
               existing_server_default=sa.text('unique_rowid()'))

    with op.batch_alter_table('assignment_submission', schema=None) as batch_op:
        batch_op.alter_column('score',
               existing_type=sa.Integer(),
               type_=sa.BIGINT(),
               existing_nullable=True)
        batch_op.alter_column('user_id',
               existing_type=sa.Integer(),
               type_=sa.BIGINT(),
               existing_nullable=False)
        batch_op.alter_column('assignment_id',
               existing_type=sa.Integer(),
               type_=sa.BIGINT(),
               existing_nullable=False)
        batch_op.alter_column('id',
               existing_type=sa.Integer(),
               type_=sa.BIGINT(),
               existing_nullable=False,
               autoincrement=True,
               existing_server_default=sa.text('unique_rowid()'))

    with op.batch_alter_table('assignment', schema=None) as batch_op:
        batch_op.alter_column('estimated_hours',
               existing_type=sa.Integer(),
               type_=sa.BIGINT(),
               existing_nullable=True)
        batch_op.alter_column('lesson_id',
               existing_type=sa.Integer(),
               type_=sa.BIGINT(),
               existing_nullable=True)
        batch_op.alter_column('course_id',
               existing_type=sa.Integer(),
               type_=sa.BIGINT(),
               existing_nullable=False)
        batch_op.alter_column('id',
               existing_type=sa.Integer(),
               type_=sa.BIGINT(),
               existing_nullable=False,
               autoincrement=True,
               existing_server_default=sa.text('unique_rowid()'))

    # ### end Alembic commands ###
