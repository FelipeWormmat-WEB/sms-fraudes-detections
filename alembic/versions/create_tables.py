from alembic import op
import sqlalchemy as sa
def upgrade():
    op.create_table(
        "sms_logs",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("message", sa.String, nullable=False),
        sa.Column("prediction", sa.String, nullable=False),
        sa.Column("confidence", sa.Float),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )
    op.create_table(
        "model_metrics",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("accuracy", sa.Float),
        sa.Column("precision", sa.Float),
        sa.Column("recall", sa.Float),
        sa.Column("recorded_at", sa.DateTime, server_default=sa.func.now()),
    )