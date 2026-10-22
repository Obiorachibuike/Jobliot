"""initial schema (created from SQLAlchemy metadata)"""
revision="0001"; down_revision=None
from alembic import op
from app.db import Base
from app import models  # noqa
def upgrade(): Base.metadata.create_all(op.get_bind())
def downgrade(): Base.metadata.drop_all(op.get_bind())
